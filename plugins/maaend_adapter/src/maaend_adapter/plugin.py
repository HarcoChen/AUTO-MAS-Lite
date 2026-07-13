from __future__ import annotations

from app.plugins import ScriptAdapterDefinition, ScriptAdapterPlugin

from .adapter import MaaEndAdapterHooks
from .schema import MaaEndConfig, MaaEndUserConfig


DEFAULT_INSTANCE = {
    "name": "MaaEnd 专项适配",
    "enabled": True,
    "config": {},
}


class Plugin(ScriptAdapterPlugin):
    """MaaEnd script adapter plugin."""

    needs = [
        "emulator",
        "maafw.interface.v1",
        "maafw.runner.v1",
        "maafw.project_update.v1",
        "maafw.agent_env.v1",
    ]
    wants = ["mxu.import.v1"]
    pages = [
        {
            "id": "maaend-adapter-task-editor",
            "path": "/plugins/maaend-adapter/task-editor",
            "title": "MaaEnd 任务编辑器",
            "menu_label": "MaaEnd 任务编辑器",
            "icon": "app",
            "component": "PluginPage",
            "renderer": "custom-element",
            "element_tag": "maaend-task-editor",
            "section": "main",
            "order": 1000,
            "visible": False,
        }
    ]

    def build_script_adapters(self) -> list[ScriptAdapterDefinition]:
        return [
            ScriptAdapterDefinition(
                type_key="MaaEnd",
                display_name="MaaEnd脚本",
                script_model=MaaEndConfig,
                user_model=MaaEndUserConfig,
                script_class_name="MaaEndPluginConfig",
                user_class_name="MaaEndPluginUserConfig",
                hooks_factory=MaaEndAdapterHooks,
                supported_modes=("AutoProxy",),
                icon="MaaEnd",
                editor_kind="plugin:maaend_adapter",
                legacy_config_class_name="MaaEndConfig",
                legacy_user_config_class_name="MaaEndUserConfig",
                metadata={
                    "framework": "maafw",
                    "source": "maaend_adapter",
                    "breaking": True,
                },
            )
        ]
