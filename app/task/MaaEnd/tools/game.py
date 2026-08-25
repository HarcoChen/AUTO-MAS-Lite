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


import asyncio

from app.models.config import MaaEndConfig
from app.models.emulator import DeviceBase, DeviceInfo
from app.models.task import ScriptItem
from app.utils import ProcessManager, get_logger, is_process_running

logger = get_logger("终末地启动")

ENDFIELD_PACKAGE = "com.hypergryph.endfield"


async def launch_endfield(
    script_info: ScriptItem,
    script_config: MaaEndConfig,
    emulator_manager: DeviceBase | None,
    game_process_manager: ProcessManager,
) -> DeviceInfo | None:
    """启动终末地客户端或模拟器，返回模拟器设备信息，直连时为 None。"""

    if emulator_manager is None:
        if is_process_running("Endfield.exe"):
            logger.info("检测到终末地客户端进程已在运行，跳过由 MAS 重复启动游戏")
            script_info.log = "检测到游戏已在运行，跳过启动游戏"
            return None
        logger.info(
            f"启动终末地: {script_config.get('Game', 'Path')} - "
            f"{script_config.get('Game', 'Arguments')}"
        )
        await game_process_manager.open_process(
            script_config.get("Game", "Path"),
            *str(script_config.get("Game", "Arguments")).split(" "),
        )
        await asyncio.sleep(script_config.get("Game", "WaitTime"))
        return None

    logger.info(f"启动模拟器: {script_config.get('Game', 'EmulatorIndex')}")
    return await emulator_manager.open(
        script_config.get("Game", "EmulatorIndex"),
        ENDFIELD_PACKAGE,
    )
