# MaaEnd Adapter

AUTO-MAS pluginized MaaEnd script adapter.

## Scope

- Registers the `MaaEnd` script type from a plugin instead of the host builtin registry.
- Requires the split MaaFW plugin stack and runs MaaEnd through its interface,
  runner, project-update, agent-env, controller, and emulator services.
- Supports both automatic proxy and the MaaEnd/MXU `ScriptConfig` session.
- Stores new records through `PluginScriptConfig`.

## Compatibility Notes

This adapter is intentionally breaking. Existing builtin `MaaEndConfig` records are
not migrated automatically; recreate MaaEnd scripts after enabling this plugin.
