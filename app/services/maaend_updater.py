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


"""MaaEnd 外部更新器进程适配。

下载源和安装包获取由 MAAFW-Updater/runtime 决定；本模块只负责规范化
spec、启动 updater，并解析其 stdout 结果。
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils import ProcessRunner, get_logger


logger = get_logger("MaaEnd 外部更新器")

UPDATER_PATH_ENV = "MAAFW_UPDATER_PATH"
DEFAULT_TIMEOUT_SECONDS = 30 * 60
SUPPORTED_SOURCES = frozenset({"auto", "mirrorchyan", "github"})


@dataclass(frozen=True)
class MaaEndUpdateResult:
    """一次 MaaEnd updater 进程执行结果。"""

    success: bool
    returncode: int
    events: tuple[dict[str, Any], ...]
    stdout: str
    stderr: str


def resolve_updater_path(updater_path: str | Path | None = None) -> Path:
    """解析 runtime 提供的 updater 路径。"""

    candidates: list[Path] = []
    if updater_path is not None and str(updater_path).strip():
        candidates.append(Path(updater_path).expanduser())

    env_path = os.getenv(UPDATER_PATH_ENV, "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())

    executable_name = "maafw-updater.exe" if os.name == "nt" else "maafw-updater"
    candidates.append(Path.cwd() / executable_name)

    resolved_candidates = [path.resolve() for path in candidates]
    for path in resolved_candidates:
        if path.is_file() and (os.name == "nt" or os.access(path, os.X_OK)):
            return path

    formatted = ", ".join(str(path) for path in resolved_candidates)
    raise FileNotFoundError(
        f"未找到可执行的 MAAFW-Updater，请由 runtime 提供 {UPDATER_PATH_ENV} "
        f"或放置于: {formatted}"
    )


def _build_update_args(
    *,
    spec_path: Path,
    root_path: Path,
    current_version: str,
    platform: str | None,
    source: str,
    wait_pid: int | None,
    relaunch: str | None,
) -> list[str]:
    """构造 updater CLI 参数。"""

    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"不支持的 MaaEnd 更新源: {source}")

    args = [
        "update",
        "--spec",
        str(spec_path),
        "--root",
        str(root_path),
        "--current-version",
        current_version,
        "--source",
        source,
    ]
    if platform:
        args.extend(("--platform", platform))
    if wait_pid is not None:
        args.extend(("--wait-pid", str(wait_pid)))
    if relaunch:
        args.extend(("--relaunch", relaunch))
    return args


def _parse_update_events(stdout: str) -> tuple[dict[str, Any], ...]:
    """从 updater stdout 中提取 JSON 事件行。"""

    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("event"), str):
            events.append(payload)
    return tuple(events)


async def run_maaend_update(
    *,
    updater_path: str | Path | None,
    root_path: Path,
    spec: dict[str, Any],
    current_version: str,
    platform: str | None = None,
    source: str = "auto",
    wait_pid: int | None = None,
    relaunch: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> MaaEndUpdateResult:
    """使用独立 updater 更新 MaaEnd。"""

    if not current_version.strip():
        raise ValueError("MaaEnd 当前版本不能为空")
    if not root_path.is_dir():
        raise FileNotFoundError(f"MaaEnd 路径不存在: {root_path}")
    if timeout_seconds <= 0:
        raise ValueError("MaaEnd 更新超时时间必须大于 0")

    executable = resolve_updater_path(updater_path)
    temp_root = Path.cwd() / "data"
    temp_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="maaend-update-", dir=temp_root
    ) as directory:
        spec_path = Path(directory) / "ProjectUpdateSpec.json"
        spec_path.write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        args = _build_update_args(
            spec_path=spec_path,
            root_path=root_path,
            current_version=current_version.strip(),
            platform=platform.strip() if platform and platform.strip() else None,
            source=source,
            wait_pid=wait_pid,
            relaunch=relaunch.strip() if relaunch and relaunch.strip() else None,
        )
        logger.info(f"启动 MaaEnd updater: {executable} {' '.join(args)}")
        process_result = await ProcessRunner.run_process(
            executable,
            *args,
            cwd=executable.parent,
            timeout=timeout_seconds,
        )

    events = _parse_update_events(process_result.stdout)
    result_event = next(
        (event for event in reversed(events) if event.get("event") == "result"),
        None,
    )
    success = process_result.returncode == 0
    if result_event is not None and isinstance(result_event.get("success"), bool):
        success = success and result_event["success"]

    return MaaEndUpdateResult(
        success=success,
        returncode=process_result.returncode,
        events=events,
        stdout=process_result.stdout,
        stderr=process_result.stderr,
    )
