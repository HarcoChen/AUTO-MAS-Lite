from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from automas_plugin_mxu_import.service import MxuImportService


class InterfaceServiceStub:
    def __init__(self) -> None:
        self.interface = SimpleNamespace(
            task=[SimpleNamespace(name="TaskA"), SimpleNamespace(name="TaskB")],
            controller=[SimpleNamespace(name="Win32")],
            resource=[SimpleNamespace(name="Official", controller=["Win32"])],
        )

    def load(self, path: Path):
        return self.interface

    def normalize_snapshot(self, interface, snapshot):
        checked = {"TaskA": False, "TaskB": False}
        checked.update(
            {key: value for key, value in snapshot["taskChecked"].items() if key in checked}
        )
        return SimpleNamespace(
            model_dump=lambda **kwargs: {
                "taskOrder": [
                    name for name in snapshot["taskOrder"] if name in checked
                ] + [name for name in checked if name not in snapshot["taskOrder"]],
                "taskChecked": checked,
                "taskOptions": {
                    name: value
                    for name, value in snapshot["taskOptions"].items()
                    if name in checked
                },
            }
        )


def test_preview_prefers_automas_and_reports_unknown_tasks(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "mxu-test.json").write_text(
        json.dumps(
            {
                "instances": [
                    {"id": "other", "tasks": []},
                    {
                        "id": "automas",
                        "name": "AUTO-MAS",
                        "controllerName": "Win32",
                        "resourceName": "Official",
                        "tasks": [
                            {
                                "taskName": "TaskA",
                                "enabled": True,
                                "optionValues": {"Mode": "Fast"},
                            },
                            {"taskName": "Unknown", "enabled": True},
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = MxuImportService(InterfaceServiceStub()).preview(tmp_path)

    assert result.selected_instance_id == "automas"
    assert result.snapshot["taskChecked"] == {"TaskA": True, "TaskB": False}
    assert result.snapshot["taskOptions"]["TaskA"] == {"Mode": "Fast"}
    assert result.warnings == ["已忽略 Interface 中不存在的任务: Unknown"]
