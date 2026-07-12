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

    def build_script_adapters(self) -> list[ScriptAdapterDefinition]:
        return [
            ScriptAdapterDefinition(
                type_key="MaaEnd",
                display_name="MaaEnd脚本",
                script_model=MaaEndConfig,
                user_model=MaaEndUserConfig,
                hooks_factory=MaaEndAdapterHooks,
                supported_modes=("AutoProxy", "ScriptConfig"),
                icon="MaaEnd",
                editor_kind="plugin:maaend_adapter",
                metadata={
                    "framework": "maafw",
                    "source": "maaend_adapter",
                    "breaking": True,
                },
            )
        ]
