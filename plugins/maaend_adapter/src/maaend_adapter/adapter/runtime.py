from __future__ import annotations

from app.models.ConfigBase import ConfigBase
from app.models.task import UserItem
from app.plugins import ScriptAdapterRuntime
from automas_script_maafw.adapter import MaaFWAdapterHooks


def _config_value(config: ConfigBase, group: str, name: str, default=None):
    try:
        value = config.get(group, name)
    except Exception:
        return default
    return default if value is None else value


class MaaEndAdapterHooks(MaaFWAdapterHooks):
    """MaaEnd 配置桥接层，运行生命周期复用通用 MaaFW adapter。"""

    async def prepare(self, runtime: ScriptAdapterRuntime) -> None:
        await runtime.storage.lock()
        runtime.storage_script_config = runtime.get_storage_script_config()
        runtime.script_config = await runtime.build_script_model()
        runtime.user_config = await runtime.storage.load_user_collection()
        runtime.extra["maafw_project_update_logs"] = []

        await self._update_project_before_run(runtime, runtime.script_config)

        emulator_id = _config_value(runtime.script_config, "Emulator", "Id", "-")
        controller_type = _config_value(
            runtime.script_config,
            "Game",
            "ControllerType",
            "Win32",
        )
        if controller_type == "Adb" and emulator_id != "-":
            runtime.emulator_manager = await runtime.initialize_emulator_manager(emulator_id)

        runtime.script_info.user_list = [
            UserItem(
                user_id=str(user_id),
                name=str(_config_value(config, "Info", "Name", user_id)),
                status="等待",
            )
            for user_id, config in runtime.user_config.items()
            if isinstance(config, ConfigBase)
            and bool(_config_value(config, "Info", "Status", True))
            and _config_value(config, "Info", "RemainedDay", -1) != 0
        ]
        self._emit_log(
            runtime,
            f"MaaEnd 插件用户列表加载完成，已筛选用户数: {len(runtime.script_info.user_list)}",
        )
