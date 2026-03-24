from __future__ import annotations

import os
import sys
from pathlib import Path

from .client import CliError


def resolve_app_root(explicit_root: str | None = None) -> Path:
    candidates: list[Path] = []

    if explicit_root:
        candidates.append(Path(explicit_root).expanduser().resolve())

    env_root = os.environ.get("AUTO_MAS_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser().resolve())

    candidates.append(Path.cwd().resolve())
    candidates.append(Path(__file__).resolve().parents[2])

    exe_path = Path(sys.executable).resolve()
    candidates.append(exe_path.parent)
    candidates.append(exe_path.parent.parent)

    for candidate in candidates:
        if _looks_like_app_root(candidate):
            return candidate

    raise CliError(
        "未找到 AUTO-MAS 根目录。请通过 --app-root 或 AUTO_MAS_ROOT 显式指定。"
    )


def resolve_python_executable(
    app_root: Path, explicit_python: str | None = None
) -> str:
    candidates: list[Path] = []

    if explicit_python:
        candidates.append(Path(explicit_python).expanduser().resolve())

    env_python = os.environ.get("AUTO_MAS_PYTHON")
    if env_python:
        candidates.append(Path(env_python).expanduser().resolve())

    if sys.platform.startswith("win"):
        candidates.append(app_root / "environment/python/python.exe")
    else:
        candidates.append(app_root / "environment/python/bin/python3")
        candidates.append(app_root / "environment/python/bin/python")

    if not getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve())

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise CliError(
        "未找到可用于启动后端的 Python。请通过 --python-exe 或 AUTO_MAS_PYTHON 显式指定。"
    )


def _looks_like_app_root(path: Path) -> bool:
    return (
        path.exists()
        and (path / "main.py").exists()
        and (path / "app").is_dir()
        and (path / "requirements.txt").exists()
    )

