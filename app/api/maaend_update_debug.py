#   AUTO-MAS: A Multi-Script, Multi-Config Management and Automation Software
#   Copyright © 2026 AUTO-MAS Team

#   This file is part of AUTO-MAS.

#   AUTO-MAS is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.

#   AUTO-MAS is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with AUTO-MAS. If not, see <https://www.gnu.org/licenses/>.


"""开发环境 MaaEnd 外部更新器调试接口。"""

from fastapi import APIRouter, Body

from app.core import Config
from app.models.schema import MaaEndUpdaterDebugIn, MaaEndUpdaterDebugOut
from app.services import run_maaend_update


router = APIRouter(prefix="/api/debug/maaend-update", tags=["开发调试"])


@router.post(
    "",
    summary="调试：使用 MAAFW-Updater 更新 MaaEnd",
    response_model=MaaEndUpdaterDebugOut,
    status_code=200,
)
async def update_maaend_debug(
    request: MaaEndUpdaterDebugIn = Body(...),
) -> MaaEndUpdaterDebugOut:
    """从已配置的 MaaEnd 脚本读取 spec，并执行外部 updater。"""

    try:
        root_path, spec = await Config.get_maaend_update_target(request.scriptId)
        result = await run_maaend_update(
            updater_path=request.updaterPath,
            root_path=root_path,
            spec=spec,
            current_version=request.currentVersion,
            platform=request.platform,
            source=request.source,
            wait_pid=request.waitPid,
            relaunch=request.relaunch,
            timeout_seconds=request.timeoutSeconds,
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        return MaaEndUpdaterDebugOut(
            code=400,
            status="error",
            message=f"MaaEnd 更新参数无效: {type(error).__name__}: {error}",
        )
    except Exception as error:
        return MaaEndUpdaterDebugOut(
            code=500,
            status="error",
            message=f"MaaEnd 更新器执行失败: {type(error).__name__}: {error}",
        )

    data = {
        "root": str(root_path),
        "spec": spec,
        "returncode": result.returncode,
        "events": list(result.events),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "resource_reloaded": False,
    }
    if not result.success:
        return MaaEndUpdaterDebugOut(
            code=500,
            status="error",
            message=f"MaaEnd 更新器返回失败（退出码 {result.returncode}）",
            data=data,
        )

    try:
        await Config.reload_maaend_resource(request.scriptId)
        data["resource_reloaded"] = True
    except Exception as error:
        return MaaEndUpdaterDebugOut(
            code=500,
            status="error",
            message=f"MaaEnd 更新成功，但资源缓存刷新失败: {type(error).__name__}: {error}",
            data=data,
        )

    return MaaEndUpdaterDebugOut(
        message="MaaEnd 更新完成，资源缓存已刷新",
        data=data,
    )
