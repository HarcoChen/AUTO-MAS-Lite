from __future__ import annotations

import json
from typing import Any


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_kv(title: str, value: str) -> None:
    print(f"{title}: {value}")

