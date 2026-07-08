"""MaaEnd script adapter plugin."""

from .plugin import Plugin
from .schema import MaaEndConfig, MaaEndUserConfig, PluginConfig

__all__ = ["Plugin", "PluginConfig", "MaaEndConfig", "MaaEndUserConfig"]
