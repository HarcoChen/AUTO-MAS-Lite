from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core import Config, EmulatorManager
from app.models.ConfigBase import ConfigBase, MultipleConfig
from app.models.task import TaskExecuteBase, UserItem
from app.plugins import ScriptAdapterHooks, ScriptAdapterRuntime
from app.services import Notify
from app.task.MaaFW.AutoProxy import AutoProxyTask
from app.task.MaaFW.interface_loader import (
    MaaFWInterfaceLoadError,
    load_interface_model_cached,
)
from app.task.MaaFW.project_updater import update_maafw_project_if_needed
from app.task.MaaFW.runner import prepare_maafw_agent_python_envs
from app.utils import get_logger
from app.utils.constants import TASK_MODE_ZH

logger = get_logger("MaaEnd 插件适配")


def _cfg_get(config: Any, group: str, name: str, default: Any = None) -> Any:
    if config is None:
        return default
    get_value = getattr(config, "get", None)
    if callable(get_value):
        try:
            value = get_value(group, name)
        except Exception:
            return default
        return default if value is None else value
    if isinstance(config, dict):
        group_data = config.get(group)
        if isinstance(group_data, dict):
            return group_data.get(name, default)
    return default


def _user_name(config: ConfigBase, fallback: str) -> str:
    return str(_cfg_get(config, "Info", "Name", fallback) or fallback)


def _user_enabled(config: ConfigBase) -> bool:
    return bool(_cfg_get(config, "Info", "Status", True))


def _user_remaining_days(config: ConfigBase) -> int:
    value = _cfg_get(config, "Info", "RemainedDay", -1)
    return value if isinstance(value, int) else -1


class MaaEndAdapterHooks(ScriptAdapterHooks):
    """MaaEnd 专项适配层，复用 MaaFW 项目运行能力。"""

    async def check(self, runtime: ScriptAdapterRuntime) -> str:
        if runtime.mode != "AutoProxy":
            return "MaaEnd 插件化适配当前仅支持 AutoProxy 模式"

        try:
            script_config = await runtime.build_script_model()
        except Exception as exc:
            return f"无法读取 MaaEnd 插件配置: {exc}"

        raw_project_path = str(_cfg_get(script_config, "Info", "Path", "") or "").strip()
        if not raw_project_path:
            return "请设置 MaaEnd MaaFW 项目目录"
        project_path = Path(raw_project_path)
        if not project_path.exists():
            return "请设置 MaaEnd MaaFW 项目目录"

        try:
            interface = self._load_interface(runtime, project_path)
        except Exception as exc:
            return f"无法读取 MaaEnd MaaFW interface，请检查项目路径: {exc}"

        if not getattr(interface, "controller", None):
            return "MaaEnd MaaFW interface 未声明 controller，请检查项目目录"
        if not getattr(interface, "resource", None):
            return "MaaEnd MaaFW interface 未声明 resource，请检查项目目录"
        if not getattr(interface, "task", None):
            return "MaaEnd MaaFW interface 未声明 task，请检查项目目录"

        emulator_id = _cfg_get(script_config, "Emulator", "Id", "-")
        emulator_index = _cfg_get(script_config, "Emulator", "Index", "-")
        if emulator_id != "-" and emulator_index in ("", "-"):
            return "请在 MaaEnd 插件配置中选择模拟器实例"

        return "Pass"

    async def prepare(self, runtime: ScriptAdapterRuntime) -> None:
        await runtime.storage.lock()
        runtime.storage_script_config = runtime.get_storage_script_config()
        runtime.script_config = await runtime.build_script_model()
        runtime.user_config = await runtime.storage.load_user_collection()

        runtime.extra["project_update_logs"] = []
        await self._update_project_before_run(runtime)

        emulator_id = _cfg_get(runtime.script_config, "Emulator", "Id", "-")
        if emulator_id != "-":
            runtime.emulator_manager = await EmulatorManager.get_emulator_instance(
                emulator_id
            )

        user_config = runtime.user_config
        runtime.script_info.user_list = [
            UserItem(
                user_id=str(user_id),
                name=_user_name(config, str(user_id)),
                status="等待",
            )
            for user_id, config in user_config.items()
            if isinstance(config, ConfigBase)
            and _user_enabled(config)
            and _user_remaining_days(config) != 0
        ]
        logger.info(
            f"MaaEnd 插件用户列表加载完成，已筛选用户数: {len(runtime.script_info.user_list)}"
        )

    def run_auto_proxy(self, runtime: ScriptAdapterRuntime) -> TaskExecuteBase:
        if runtime.script_config is None:
            raise RuntimeError("MaaEnd 插件脚本配置未准备完成")
        if not isinstance(runtime.user_config, MultipleConfig):
            raise RuntimeError("MaaEnd 插件用户配置未准备完成")

        return AutoProxyTask(
            runtime.script_info,
            runtime.script_config,
            runtime.user_config,
            runtime.emulator_manager,
            runtime.extra.get("project_update_logs", []),
        )

    async def finalize(self, runtime: ScriptAdapterRuntime) -> None:
        await self._unlock_and_save_users(runtime)

        if runtime.check_result != "Pass":
            runtime.script_info.status = "异常"
            return

        error_user = [u.name for u in runtime.script_info.user_list if u.status == "异常"]
        over_user = [u.name for u in runtime.script_info.user_list if u.status == "完成"]
        wait_user = [u.name for u in runtime.script_info.user_list if u.status == "等待"]
        skip_user = [u.name for u in runtime.script_info.user_list if u.status == "跳过"]

        if error_user:
            runtime.script_info.status = "异常"
        elif over_user:
            runtime.script_info.status = "完成"
        else:
            runtime.script_info.status = "跳过" if skip_user else "完成"

        title = (
            f"{datetime.now().strftime('%m-%d')} | "
            f"{runtime.script_info.name or '空白'}的{TASK_MODE_ZH[runtime.mode]}任务报告"
        )
        try:
            await Notify.push_plyer(
                title.replace("报告", "已完成！"),
                f"已完成用户数: {len(over_user)}, 未完成用户数: {len(error_user) + len(wait_user)}",
                f"已完成用户数: {len(over_user)}, 未完成用户数: {len(error_user) + len(wait_user)}",
                10,
            )
        except Exception as exc:
            logger.warning(f"MaaEnd 插件桌面通知发送失败: {exc}")

    async def on_crash(self, runtime: ScriptAdapterRuntime, error: Exception) -> None:
        runtime.script_info.status = "异常"
        logger.exception(f"MaaEnd 插件任务出现异常: {error}")
        with suppress(Exception):
            await self._unlock_and_save_users(runtime)
        await Config.send_websocket_message(
            id=runtime.task_info.task_id,
            type="Info",
            data={"Error": f"MaaEnd 插件任务出现异常: {error}"},
        )

    def _load_interface(
        self,
        runtime: ScriptAdapterRuntime,
        project_path: Path,
        *,
        force_reload: bool = False,
    ) -> Any:
        interface_service = runtime.get_service("maafw.interface.v1")
        load = getattr(interface_service, "load", None)
        if callable(load):
            return load(project_path, force_reload=force_reload)
        return load_interface_model_cached(project_path, force_reload=force_reload)

    async def _update_project_before_run(self, runtime: ScriptAdapterRuntime) -> None:
        if not _cfg_get(runtime.script_config, "Update", "IfAutoUpdate", True):
            self._send_update_log(runtime, "MaaEnd MaaFW 项目运行前自动更新已关闭")
            return

        project_path = Path(_cfg_get(runtime.script_config, "Info", "Path", "")).resolve()
        try:
            interface_model = self._load_interface(runtime, project_path)
        except MaaFWInterfaceLoadError as exc:
            self._send_update_log(
                runtime,
                f"MaaEnd MaaFW 项目更新跳过，interface 读取失败: {exc}",
            )
            return

        mirror_cdk = (
            _cfg_get(runtime.script_config, "Update", "MirrorChyanCDK", "")
            or Config.get("Update", "MirrorChyanCDK")
        )
        channel = (
            _cfg_get(runtime.script_config, "Update", "Channel", "")
            or Config.get("Update", "Channel")
        )
        try:
            update_result = await update_maafw_project_if_needed(
                project_path,
                interface_model,
                mirror_cdk=mirror_cdk,
                channel=channel,
                proxy=Config.proxy,
                send_log=lambda message: self._send_update_log(runtime, message),
            )
            if update_result.updated:
                refreshed_interface = self._load_interface(
                    runtime,
                    project_path,
                    force_reload=True,
                )
                self._send_update_log(
                    runtime,
                    "MaaEnd MaaFW project updated, preparing agent Python env",
                )
                agent_prepare_logs: list[str] = []
                try:
                    await asyncio.to_thread(
                        prepare_maafw_agent_python_envs,
                        project_path,
                        refreshed_interface,
                        send_log=agent_prepare_logs.append,
                    )
                finally:
                    for log_line in agent_prepare_logs:
                        self._send_update_log(runtime, log_line)
        except Exception as exc:
            self._send_update_log(
                runtime,
                f"MaaEnd MaaFW 项目更新失败，继续使用当前目录: {exc}",
            )

    def _send_update_log(self, runtime: ScriptAdapterRuntime, message: str) -> None:
        logger.info(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        runtime.extra.setdefault("project_update_logs", []).append(
            f"[{timestamp}] {message}\n"
        )
        runtime.script_info.log = "".join(runtime.extra["project_update_logs"][-80:])

    async def _unlock_and_save_users(self, runtime: ScriptAdapterRuntime) -> None:
        storage_script_config = runtime.get_storage_script_config()
        if getattr(storage_script_config, "is_locked", False):
            await runtime.storage.unlock()

        if isinstance(runtime.user_config, MultipleConfig):
            await runtime.storage.save_user_models(runtime.user_config)
            await Config.ScriptConfig.save()
