from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .client import ApiClient, CliError
from .runtime import resolve_app_root, resolve_python_executable


@dataclass
class BackendLifecycle:
    client: ApiClient
    app_root: str | None = None
    python_executable: str | None = None
    keep_backend: bool = False
    startup_timeout: float = 30.0
    probe_interval: float = 0.5
    process: subprocess.Popen[bytes] | None = None
    started_by_cli: bool = False
    _resolved_app_root: Path | None = None
    _resolved_python_executable: str | None = None

    def ensure_ready(self) -> None:
        if self._is_ready():
            return
        self.start_backend()
        if not self._wait_until_ready():
            raise CliError("后端启动超时，请手动检查后台日志")

    def close_if_started(self) -> None:
        if not self.started_by_cli or self.keep_backend:
            return
        self.stop_backend()

    def start_backend(self) -> None:
        if self._is_ready():
            return
        self._start_backend()

    def stop_backend(self) -> None:
        if self._is_ready():
            try:
                self.client.post("/api/core/close")
            except Exception:  # noqa: BLE001
                pass

        if self.process is not None and self.process.poll() is None:
            try:
                self.process.wait(timeout=5)
            except Exception:  # noqa: BLE001
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except Exception:  # noqa: BLE001
                    try:
                        self.process.kill()
                    except Exception:  # noqa: BLE001
                        pass

    def status(self) -> dict[str, object]:
        return {
            "ready": self._is_ready(),
            "startedByCli": self.started_by_cli,
            "trackedPid": self.process.pid if self.process is not None else None,
            "appRoot": self._safe_app_root(),
            "pythonExecutable": self._safe_python_executable(),
            "apiUrl": self.client.base_url,
        }

    def _is_ready(self) -> bool:
        try:
            self.client.post("/api/info/version")
            return True
        except Exception:  # noqa: BLE001
            return False

    def _wait_until_ready(self) -> bool:
        deadline = time.time() + self.startup_timeout
        while time.time() < deadline:
            if self._is_ready():
                return True
            time.sleep(self.probe_interval)
        return False

    def _start_backend(self) -> None:
        project_root = self._get_app_root()
        main_file = project_root / "main.py"
        if not main_file.exists():
            raise CliError(f"未找到后端入口: {main_file}")

        self.process = subprocess.Popen(
            [self._get_python_executable(), str(main_file)],
            cwd=str(project_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.started_by_cli = True

    def _get_app_root(self) -> Path:
        if self._resolved_app_root is None:
            self._resolved_app_root = resolve_app_root(self.app_root)
        return self._resolved_app_root

    def _get_python_executable(self) -> str:
        if self._resolved_python_executable is None:
            self._resolved_python_executable = resolve_python_executable(
                self._get_app_root(), self.python_executable
            )
        return self._resolved_python_executable

    def _safe_app_root(self) -> str | None:
        try:
            return str(self._get_app_root())
        except CliError:
            return None

    def _safe_python_executable(self) -> str | None:
        try:
            return self._get_python_executable()
        except CliError:
            return None
