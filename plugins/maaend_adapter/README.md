# MaaEnd Adapter

AUTO-MAS pluginized MaaEnd script adapter.

## Scope

- Registers the `MaaEnd` script type from a plugin instead of the host builtin registry.
- Runs MaaEnd as a MaaFW project through the host MaaFW runtime capabilities.
- Stores new records through `PluginScriptConfig`.

## Compatibility Notes

This adapter is intentionally breaking. Existing builtin `MaaEndConfig` records are
not migrated automatically; recreate MaaEnd scripts after enabling this plugin.
