from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .client import ApiClient, CliError


@dataclass
class BackendLifecycle:
    client: ApiClient
    startup_timeout: float = 30.0
    probe_interval: float = 0.5
    process: subprocess.Popen[bytes] | None = None
    started_by_cli: bool = False

    def ensure_ready(self) -> None:
        if self._is_ready():
            return
        self._start_backend()
        if not self._wait_until_ready():
            raise CliError("后端启动超时，请手动检查后台日志")

    def close_if_started(self) -> None:
        if not self.started_by_cli:
            return
        try:
            self.client.post("/api/core/close")
        except Exception:  # noqa: BLE001
            pass

        if self.process is not None and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:  # noqa: BLE001
                try:
                    self.process.kill()
                except Exception:  # noqa: BLE001
                    pass

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
        project_root = Path(__file__).resolve().parents[2]
        main_file = project_root / "main.py"
        if not main_file.exists():
            raise CliError(f"未找到后端入口: {main_file}")

        self.process = subprocess.Popen(
            [sys.executable, str(main_file)],
            cwd=str(project_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.started_by_cli = True

