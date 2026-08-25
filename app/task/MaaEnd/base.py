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


import uuid
from pathlib import Path

from app.core import Config
from app.models.task import TaskExecuteBase, ScriptItem
from app.models.ConfigBase import MultipleConfig
from app.models.config import MaaEndConfig, MaaEndUserConfig
from app.models.emulator import DeviceBase
from app.services import System
from app.utils import get_logger, ProcessManager


class MaaEndTaskBase(TaskExecuteBase):
    """MaaEnd 任务模式公共基类

    收束三种模式共用的入参、MaaEnd 路径、进程管理器与进程中止逻辑。
    子类用 `mode_name` 指定日志模块名与异常文案前缀。
    """

    mode_name = "MaaEnd 任务"

    def __init__(
        self,
        script_info: ScriptItem,
        script_config: MaaEndConfig,
        user_config: MultipleConfig[MaaEndUserConfig],
        emulator_manager: DeviceBase | None,
    ):
        super().__init__()

        if script_info.task_info is None:
            raise RuntimeError("ScriptItem 未绑定到 TaskItem")

        self.logger = get_logger(self.mode_name)
        self.task_info = script_info.task_info
        self.script_info = script_info
        self.script_config = script_config
        self.user_config = user_config
        self.emulator_manager = emulator_manager
        self.cur_user_item = self.script_info.user_list[self.script_info.current_index]

        self.maaend_root_path = Path(self.script_config.get("Info", "Path"))
        self.maaend_exe_path = self.maaend_root_path / "MaaEnd.exe"
        self.maaend_set_path = self.maaend_root_path / "config"

        # 直连模式下也保留游戏进程管理器，避免调用方按模拟器分支取用时缺字段
        self.maaend_process_manager = ProcessManager()
        self.game_process_manager = ProcessManager()

    async def kill_maaend(self) -> None:
        """中止 MaaEnd 进程本体"""

        await self.maaend_process_manager.kill()
        await System.kill_process(self.maaend_exe_path)

    async def kill_managed_process(self) -> None:
        """中止 MaaEnd 与游戏/模拟器进程"""

        try:
            self.logger.info(f"中止 MaaEnd 进程: {self.maaend_exe_path}")
            await self.kill_maaend()
        except Exception as e:
            self.logger.opt(exception=True).warning(f"中止 MaaEnd 进程失败: {e}")
        try:
            if self.emulator_manager is None:
                self.logger.info("中止终末地进程")
                await self.game_process_manager.kill()
                await System.kill_process(self.script_config.get("Game", "Path"))
            else:
                self.logger.info("中止模拟器进程")
                await self.emulator_manager.close(
                    self.script_config.get("Game", "EmulatorIndex")
                )
        except Exception as e:
            self.logger.opt(exception=True).warning(f"关闭模拟器失败: {e}")

    async def on_crash(self, e: Exception):
        self.cur_user_item.status = "异常"
        self.logger.opt(exception=True).warning(f"{self.mode_name}任务出现异常: {e}")
        await Config.send_websocket_message(
            id=self.task_info.task_id,
            type="Info",
            data={"Error": f"{self.mode_name}任务出现异常: {e}"},
        )


class MaaEndUserTaskBase(MaaEndTaskBase):
    """按用户执行的 MaaEnd 任务基类

    自动代理与人工检查都绑定到具体用户，共用用户配置、账号与配置目录解析。
    脚本设置模式不绑定用户，因此不继承本类。
    """

    def __init__(
        self,
        script_info: ScriptItem,
        script_config: MaaEndConfig,
        user_config: MultipleConfig[MaaEndUserConfig],
        emulator_manager: DeviceBase | None,
    ):
        super().__init__(script_info, script_config, user_config, emulator_manager)

        self.cur_user_uid = uuid.UUID(self.cur_user_item.user_id)
        self.cur_user_config = self.user_config[self.cur_user_uid]
        self.check_result = "-"

    @property
    def account_id(self) -> str:
        """当前用户配置的游戏账号"""

        return str(self.cur_user_config.get("Info", "Id")).strip()

    @property
    def user_config_dir(self) -> Path:
        """用户的 MaaEnd 配置目录，简洁模式下所有用户共用 Default 目录"""

        config_user_id = (
            "Default"
            if self.cur_user_config.get("Info", "Mode") == "简洁"
            else self.cur_user_uid
        )
        return (
            Path.cwd()
            / f"data/{self.script_info.script_id}/{config_user_id}/ConfigFile"
        )
