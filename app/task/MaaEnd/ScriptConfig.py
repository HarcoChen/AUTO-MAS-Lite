#   AUTO-MAS: A Multi-Script, Multi-Config Management and Automation Software
#   Copyright © 2025-2026 AUTO-MAS Team

#   This file is part of AUTO-MAS.

#   AUTO-MAS is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.

#   AUTO-MAS is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with AUTO-MAS. If not, see <https://www.gnu.org/licenses/>.

#   Contact: DLmaster_361@163.com


import shutil
import asyncio
from pathlib import Path
from typing import Any

from app.models.task import ScriptItem
from app.models.ConfigBase import MultipleConfig
from app.models.config import MaaEndConfig, MaaEndUserConfig
from app.models.emulator import DeviceBase
from app.utils import get_logger
from app.utils.io import read_file, write_file
from .base import MaaEndTaskBase

logger = get_logger("MaaEnd 脚本设置")

_MAAEND_LOCAL_FIELDS = ("version", "interfaceTaskSnapshot")


def restore_maaend_local_fields(
    maaend_set: dict[str, Any],
    local_config: dict[str, Any] | None,
) -> dict[str, Any]:
    """从 MaaEnd 本地配置恢复版本快照等字段，避免被用户配置覆盖"""

    for field in _MAAEND_LOCAL_FIELDS:
        maaend_set.pop(field, None)
        if local_config is not None and field in local_config:
            maaend_set[field] = local_config[field]

    settings = maaend_set.get("settings")
    if isinstance(settings, dict):
        settings.pop("welcomeShownHash", None)

    if local_config is not None:
        local_settings = local_config.get("settings")
        if (
            isinstance(local_settings, dict)
            and "welcomeShownHash" in local_settings
        ):
            maaend_set.setdefault("settings", {})["welcomeShownHash"] = (
                local_settings["welcomeShownHash"]
            )

    return maaend_set


def select_maaend_instance(source_set: dict[str, Any]) -> dict[str, Any] | None:
    """按 AUTO-MAS 实例 > 最近活动实例 > 首个实例的顺序选择 MaaEnd 实例"""

    instances = source_set.get("instances")
    if not isinstance(instances, list) or len(instances) == 0:
        return None

    last_active_instance_id = source_set.get("lastActiveInstanceId")
    for instance in instances:
        if instance.get("id") == "automas" or instance.get("name") == "AUTO-MAS":
            return instance
        if isinstance(instance, dict) and instance.get("id") == last_active_instance_id:
            return instance

    for instance in instances:
        if isinstance(instance, dict):
            return instance
    return None


def normalize_maaend_config(
    maaend_set: dict[str, Any],
    controller_type: str,
    fallback_set: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """将 MaaEnd 配置收束为 AUTO-MAS 单实例配置"""

    selected_instance = select_maaend_instance(maaend_set)
    if selected_instance is None and fallback_set is not None:
        selected_instance = select_maaend_instance(fallback_set)
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


class ScriptConfigTask(MaaEndTaskBase):
    """MaaEnd 脚本设置模式"""

    mode_name = "MaaEnd 脚本设置"

    def __init__(
        self,
        script_info: ScriptItem,
        script_config: MaaEndConfig,
        user_config: MultipleConfig[MaaEndUserConfig],
        emulator_manager: DeviceBase | None,
    ):
        super().__init__(script_info, script_config, user_config, emulator_manager)

        # 脚本设置模式直接按用户目录读写，不参与简洁模式共用
        self.config_file_path = (
            Path.cwd()
            / f"data/{self.script_info.script_id}/{self.cur_user_item.user_id}/ConfigFile"
        )

    async def prepare(self):

        self.wait_event = asyncio.Event()

    async def main_task(self):

        await self.prepare()

        await self.set_maaend()
        logger.info(f"启动 MaaEnd 进程: {self.maaend_exe_path}")
        self.wait_event.clear()
        await self.maaend_process_manager.open_process(self.maaend_exe_path)
        await self.wait_event.wait()

    async def set_maaend(self):
        """配置 MaaEnd 运行参数"""

        logger.info(f"开始配置 MaaEnd 运行参数: 设置脚本 {self.cur_user_item.user_id}")

        await self.kill_maaend()

        if (self.config_file_path / "mxu-MaaEnd.json").exists():
            shutil.rmtree(self.maaend_set_path, ignore_errors=True)
            shutil.copytree(self.config_file_path, self.maaend_set_path)
        elif self.maaend_set_path.exists():
            shutil.copytree(
                self.maaend_set_path,
                self.config_file_path,
                dirs_exist_ok=True,
            )

        maaend_set_path = self.maaend_set_path / "mxu-MaaEnd.json"
        if not maaend_set_path.exists():
            raise FileNotFoundError(
                "未找到 MaaEnd 配置文件, 请检查 MaaEnd 路径设置或先启动 MaaEnd 完成配置文件生成"
            )

        maaend_set = read_file(maaend_set_path)
        maaend_set = normalize_maaend_config(
            maaend_set,
            self.script_config.get("Game", "ControllerType"),
        )

        write_file(maaend_set_path, maaend_set)
        logger.success(
            f"MaaEnd 运行参数配置完成: 设置脚本 {self.cur_user_item.user_id}"
        )

    async def final_task(self):

        await self.kill_maaend()

        shutil.rmtree(self.config_file_path, ignore_errors=True)
        self.config_file_path.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.maaend_set_path, self.config_file_path, dirs_exist_ok=True)
        config_path = self.config_file_path / "mxu-MaaEnd.json"
        maaend_set = read_file(config_path)
        maaend_set = normalize_maaend_config(
            maaend_set, self.script_config.get("Game", "ControllerType")
        )
        write_file(config_path, maaend_set)
