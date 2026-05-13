"""
Plugin base class.

A NagiFlow plugin is a Python package or module placed in the workspace
``plugins/`` directory.  It must expose a class that inherits ``BasePlugin``
and implement ``setup()``.

Plugin authors can:
  - Register custom LLM providers via ``register_llm_provider``
  - Register custom TTS providers via ``register_tts_provider``
  - Register custom skills via ``skill_registry.register``
  - Add FastAPI routers via the router list provided in ``setup()``

Example plugin structure::

    workspace/
    └── plugins/
        └── my_plugin/
            ├── __init__.py          ← must expose MyPlugin class
            └── my_plugin.py

    # __init__.py
    from nagiflow.plugins.base import BasePlugin, PluginMeta
    from nagiflow.skills.registry import skill_registry
    from .my_skill import MySkill

    class MyPlugin(BasePlugin):
        meta = PluginMeta(name="my_plugin", version="1.0.0", author="You")

        async def setup(self) -> None:
            skill_registry.register(MySkill)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginMeta:
    name: str
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    requires: list[str] = field(default_factory=list)  # required NagiFlow version constraints


class BasePlugin(ABC):
    """Abstract base class for NagiFlow plugins."""

    meta: PluginMeta

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}

    @abstractmethod
    async def setup(self) -> None:
        """
        Called once when the plugin is loaded.

        Register skills, providers, or routers here.
        """

    async def teardown(self) -> None:
        """Called when the application shuts down. Override if needed."""
