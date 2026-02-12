#   AUTO-MAS: A Multi-Script, Multi-Config Management and Automation Software
#   Copyright © 2024-2025 DLmaster361
#   Copyright © 2025 MoeSnowyFox
#   Copyright © 2025-2026 AUTO-MAS Team

#   This file is part of AUTO-MAS.

#   AUTO-MAS is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   AUTO-MAS is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with AUTO-MAS. If not, see <https://www.gnu.org/licenses/>.

#   Contact: DLmaster_361@163.com


import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schema import OutBase

router = APIRouter(prefix="/api/path", tags=["路径管理"])


# ===== 常用系统路径 =====
COMMON_PATHS = {
    "win32": [
        {"name": "我的文档", "path": os.path.expandvars("%USERPROFILE%\\Documents")},
        {"name": "下载", "path": os.path.expandvars("%USERPROFILE%\\Downloads")},
        {"name": "桌面", "path": os.path.expandvars("%USERPROFILE%\\Desktop")},
        {"name": "用户目录", "path": os.path.expandvars("%USERPROFILE%")},
        {"name": "MAA 工作目录", "path": "C:\\MAA"},
        {"name": "蓝叠模拟器", "path": "C:\\Program Files\\BlueStacks_nxt"},
        {"name": "夜神模拟器", "path": "C:\\Program Files\\Nox"},
        {"name": "雷电模拟器", "path": "C:\\Program Files\\LDPlayer"},
        {"name": "MuMu 模拟器", "path": "C:\\Program Files\\MuMu\\星云云手机\\VMS"},
        {"name": "逍遥模拟器", "path": "C:\\Program Files\\Microvirt"},
    ],
    "linux": [
        {"name": "主目录", "path": os.path.expanduser("~")},
        {"name": "下载", "path": os.path.expanduser("~/Downloads")},
        {"name": "桌面", "path": os.path.expanduser("~/Desktop")},
    ],
    "darwin": [
        {"name": "主目录", "path": os.path.expanduser("~")},
        {"name": "下载", "path": os.path.expanduser("~/Downloads")},
        {"name": "桌面", "path": os.path.expanduser("~/Desktop")},
        {"name": "文稿", "path": os.path.expanduser("~/Documents")},
    ],
}


class PathValidateIn(BaseModel):
    """路径验证请求"""

    path: str
    check_exists: bool = True
    check_readable: bool = True
    check_dir: bool = False


class PathValidateOut(OutBase):
    """路径验证响应"""

    valid: bool = False
    exists: bool = False
    readable: bool = False
    is_dir: bool = False
    is_file: bool = False
    normalized_path: str = ""
    error: Optional[str] = None


class PathReadIn(BaseModel):
    """路径读取请求"""

    path: str
    encoding: str = "utf-8"


class PathReadOut(OutBase):
    """路径读取响应"""

    exists: bool = False
    is_dir: bool = False
    is_file: bool = False
    content: Optional[str] = None
    files: Optional[list] = None
    error: Optional[str] = None


class SystemPathsOut(OutBase):
    """系统路径列表响应"""

    platform: str = ""
    paths: list = []


@router.get("/system", response_model=SystemPathsOut, summary="获取常用系统路径")
async def get_system_paths() -> SystemPathsOut:
    """获取当前平台的常用系统路径列表"""
    platform = os.name
    paths = COMMON_PATHS.get(platform, COMMON_PATHS.get("win32", []))

    # 检查每个路径是否存在
    valid_paths = []
    for item in paths:
        p = Path(item["path"])
        if p.exists():
            valid_paths.append(item)

    return SystemPathsOut(
        platform=platform,
        paths=valid_paths,
    )


@router.post("/validate", response_model=PathValidateOut, summary="验证路径有效性")
async def validate_path(data: PathValidateIn) -> PathValidateOut:
    """验证指定路径的有效性（是否存在、是否可读、是否目录等）"""
    try:
        p = Path(data.path)
        exists = p.exists()
        normalized = str(p.resolve())

        readable = False
        if exists:
            try:
                readable = os.access(data.path, os.R_OK)
            except Exception:
                readable = False

        is_dir = p.is_dir() if exists else False
        is_file = p.is_file() if exists else False

        valid = True
        error = None

        if data.check_exists and not exists:
            valid = False
            error = "路径不存在"

        if data.check_readable and exists and not readable:
            valid = False
            error = "路径无读取权限"

        if data.check_dir and exists and not is_dir:
            valid = False
            error = "期望是目录，但路径是文件"

        return PathValidateOut(
            valid=valid,
            exists=exists,
            readable=readable,
            is_dir=is_dir,
            is_file=is_file,
            normalized_path=normalized,
            error=error,
        )

    except Exception as e:
        return PathValidateOut(
            valid=False,
            exists=False,
            readable=False,
            is_dir=False,
            is_file=False,
            normalized_path="",
            error=str(e),
        )


@router.post("/read", response_model=PathReadOut, summary="读取路径内容")
async def read_path(data: PathReadIn) -> PathReadOut:
    """读取指定路径的内容（如果是文件则返回内容，如果是目录则返回文件列表）"""
    try:
        p = Path(data.path)

        if not p.exists():
            return PathReadOut(exists=False, error="路径不存在")

        if p.is_file():
            try:
                content = p.read_text(encoding=data.encoding)
                return PathReadOut(
                    exists=True,
                    is_dir=False,
                    is_file=True,
                    content=content,
                )
            except UnicodeDecodeError:
                return PathReadOut(
                    exists=True,
                    is_dir=False,
                    is_file=True,
                    content=None,
                    error="文件编码不支持，无法读取文本内容",
                )
            except PermissionError:
                return PathReadOut(
                    exists=True,
                    is_dir=False,
                    is_file=True,
                    content=None,
                    error="无读取权限",
                )

        elif p.is_dir():
            try:
                items = []
                for item in sorted(p.iterdir()):
                    items.append(
                        {
                            "name": item.name,
                            "path": str(item),
                            "is_dir": item.is_dir(),
                            "is_file": item.is_file(),
                        }
                    )
                return PathReadOut(exists=True, is_dir=True, is_file=False, files=items)
            except PermissionError:
                return PathReadOut(
                    exists=True,
                    is_dir=True,
                    is_file=False,
                    files=[],
                    error="无读取目录内容的权限",
                )

        else:
            return PathReadOut(exists=True, error="未知路径类型")

    except Exception as e:
        return PathReadOut(exists=False, error=str(e))


@router.get("/resolve/{path:path}", summary="解析相对路径")
async def resolve_path(path: str) -> dict:
    """将相对路径解析为绝对路径"""
    try:
        p = Path(path)
        if not p.is_absolute():
            # 相对于当前工作目录
            p = Path.cwd() / p
        return {"resolved": str(p.resolve()), "exists": p.exists()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
