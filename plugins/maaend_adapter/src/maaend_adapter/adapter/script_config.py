from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

from app.core import Config
from app.models.task import ScriptItem, TaskExecuteBase
from app.services import System
from app.utils import ProcessManager, get_logger


logger = get_logger("MaaEnd 脚本设置")


def normalize_maaend_config(
    maaend_set: dict[str, Any],
    controller_type: str,
    template_set: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """将 MaaEnd 配置收束为 AUTO-MAS 单实例配置。"""

    def select_instance(source_set: dict[str, Any]) -> dict[str, Any] | None:
        instances = source_set.get("instances")
        if not isinstance(instances, list) or not instances:
            return None

        last_active_instance_id = source_set.get("lastActiveInstanceId")
        for instance in instances:
            if not isinstance(instance, dict):
                continue
            if instance.get("id") == "automas" or instance.get("name") == "AUTO-MAS":
                return instance
            if instance.get("id") == last_active_instance_id:
                return instance
        return next((item for item in instances if isinstance(item, dict)), None)

    selected_instance = select_instance(maaend_set)
    if selected_instance is None and template_set is not None:
        selected_instance = select_instance(template_set)
    if selected_instance is None:
        raise ValueError("MaaEnd 配置文件中未找到可用实例")

    selected_instance["id"] = "automas"
    selected_instance["name"] = "AUTO-MAS"
    selected_instance.pop("customName", None)
    selected_instance["controllerName"] = controller_type
    selected_instance.setdefault("tasks", [])
    maaend_set["instances"] = [selected_instance]
    maaend_set["lastActiveInstanceId"] = "automas"
    return maaend_set


class MaaEndScriptConfigTask(TaskExecuteBase):
    """通过 MaaEnd/MXU 图形界面编辑单个用户配置。"""

    def __init__(self, script_info: ScriptItem, script_config: Any) -> None:
        super().__init__()
        if script_info.task_info is None:
            raise RuntimeError("ScriptItem 未绑定到 TaskItem")

        self.task_info = script_info.task_info
        self.script_info = script_info
        self.script_config = script_config
        self.cur_user_item = self.script_info.user_list[self.script_info.current_index]
        self.process_manager = ProcessManager()
        self.wait_event = asyncio.Event()
        self.maaend_root_path = Path(self.script_config.get("Info", "Path"))
        self.maaend_config_path = self.maaend_root_path / "config"
        self.maaend_exe_path = self.maaend_root_path / "MaaEnd.exe"
        self.config_file_path = (
            Path.cwd()
            / "data"
            / self.script_info.script_id
            / self.cur_user_item.user_id
            / "ConfigFile"
        )

    async def main_task(self) -> None:
        await self._prepare_maaend_config()
        logger.info(f"启动 MaaEnd 进程: {self.maaend_exe_path}")
        self.wait_event.clear()
        await self.process_manager.open_process(self.maaend_exe_path)
        await self.wait_event.wait()

    async def _prepare_maaend_config(self) -> None:
        await self._stop_maaend()

        source = self.config_file_path
        if not (source / "mxu-MaaEnd.json").is_file():
            source = Path.cwd() / "res" / "templates" / "MaaEnd" / "config"
        if not (source / "mxu-MaaEnd.json").is_file():
            raise FileNotFoundError(
                "未找到 MaaEnd 配置文件，请先启动 MaaEnd 完成初始配置"
            )

        self._replace_directory(source, self.maaend_config_path)
        config_path = self.maaend_config_path / "mxu-MaaEnd.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        template_path = (
            Path.cwd() / "res" / "templates" / "MaaEnd" / "config" / "mxu-MaaEnd.json"
        )
        template_data = (
            json.loads(template_path.read_text(encoding="utf-8"))
            if template_path.is_file()
            else None
        )
        normalized = normalize_maaend_config(
            config_data,
            self.script_config.get("Game", "ControllerType"),
            template_data,
        )
        config_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    async def final_task(self) -> None:
        await self._stop_maaend()
        self._replace_directory(self.maaend_config_path, self.config_file_path)
        config_path = self.config_file_path / "mxu-MaaEnd.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        normalized = normalize_maaend_config(
            config_data,
            self.script_config.get("Game", "ControllerType"),
        )
        config_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    async def on_crash(self, error: Exception) -> None:
        self.cur_user_item.status = "异常"
        logger.exception(f"MaaEnd 脚本设置任务出现异常: {error}")
        try:
            await self._stop_maaend()
        except Exception as cleanup_error:
            logger.exception(f"MaaEnd 配置进程清理失败: {cleanup_error}")
        try:
            await Config.send_websocket_message(
                id=self.task_info.task_id,
                type="Info",
                data={"Error": f"MaaEnd 脚本设置任务出现异常: {error}"},
            )
        except Exception as notify_error:
            logger.exception(f"MaaEnd 配置异常通知发送失败: {notify_error}")

    async def _stop_maaend(self) -> None:
        try:
            await self.process_manager.kill()
        except Exception as error:
            logger.exception(f"MaaEnd 配置进程管理器清理失败: {error}")
        try:
            await System.kill_process(self.maaend_exe_path)
        except Exception as error:
            logger.exception(f"MaaEnd 配置主进程清理失败: {error}")

    @staticmethod
    def _replace_directory(source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f"{target.name}.automas-copy.tmp")
        shutil.rmtree(temporary, ignore_errors=True)
        shutil.copytree(source, temporary)
        shutil.rmtree(target, ignore_errors=True)
        temporary.rename(target)
