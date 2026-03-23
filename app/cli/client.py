from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class CliError(RuntimeError):
    """CLI runtime error."""


@dataclass
class ApiClient:
    base_url: str
    timeout: float = 10.0

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + path
        try:
            response = httpx.post(url, json=payload or {}, timeout=self.timeout)
        except Exception as exc:  # noqa: BLE001
            raise CliError(f"请求失败: {exc}") from exc

        try:
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise CliError(f"接口返回非JSON: {response.text}") from exc

        if response.status_code != 200:
            raise CliError(f"接口HTTP错误({response.status_code}): {data}")
        if isinstance(data, dict) and data.get("code", 200) != 200:
            raise CliError(data.get("message", f"接口业务错误: {data}"))
        if not isinstance(data, dict):
            raise CliError(f"接口返回格式错误: {data}")
        return data

