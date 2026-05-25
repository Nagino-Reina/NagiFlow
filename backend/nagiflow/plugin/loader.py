"""
Plugin loader.

Scans two directories in order:
  1. backend/plugins/  — built-in plugins shipped with NagiFlow
  2. workspace/plugins/ — user-installed plugins

Each subdirectory must be a Python package (has __init__.py) that exposes
exactly one BasePlugin subclass.  The loader imports the package, finds the
class, instantiates it, and calls setup().
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

from loguru import logger

from nagiflow.core.exceptions import PluginLoadError
from nagiflow.plugin.base import BasePlugin

# backend/plugins/ — same repo, always present
BUILTIN_PLUGINS_DIR: Path = Path(__file__).parents[3] / "plugins"


class _PluginTracker:
    """Tracks loaded plugin instances for teardown."""

    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        self._plugins[plugin.meta.name] = plugin

    def all(self) -> list[BasePlugin]:
        return list(self._plugins.values())

    def names(self) -> list[str]:
        return list(self._plugins.keys())


class PluginLoader:
    def __init__(self) -> None:
        self._tracker = _PluginTracker()

    def _find_plugin_class(self, module: object) -> type[BasePlugin] | None:
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                return obj
        return None

    def _load_module(self, package_path: Path) -> object:
        init_file = package_path / "__init__.py"
        if not init_file.exists():
            raise PluginLoadError(f"Plugin '{package_path}' has no __init__.py.")

        parent = str(package_path.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)

        module_name = package_path.name
        spec = importlib.util.spec_from_file_location(module_name, init_file)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Cannot create module spec for '{package_path}'.")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module

    async def _load_from(self, directory: Path, builtin: bool = False) -> None:
        if not directory.exists():
            if not builtin:
                logger.debug(f"Plugin directory '{directory}' not found; skipping.")
            return

        tag = "built-in" if builtin else "user"
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_"):
                continue
            logger.info(f"Loading {tag} plugin: '{entry.name}'")
            try:
                module = self._load_module(entry)
                cls = self._find_plugin_class(module)
                if cls is None:
                    logger.warning(f"Plugin '{entry.name}' has no BasePlugin subclass; skipping.")
                    continue
                plugin = cls()
                await plugin.setup()
                self._tracker.register(plugin)
                logger.info(f"Plugin '{plugin.meta.name}' v{plugin.meta.version} loaded.")
            except PluginLoadError:
                raise
            except Exception as exc:
                logger.error(f"Failed to load plugin '{entry.name}': {exc}", exc_info=True)

    async def load_all(self, user_plugins_dir: Path) -> None:
        """Load built-in plugins first, then user plugins."""
        await self._load_from(BUILTIN_PLUGINS_DIR, builtin=True)
        await self._load_from(user_plugins_dir, builtin=False)

    async def unload_all(self) -> None:
        for plugin in self._tracker.all():
            try:
                await plugin.teardown()
                logger.info(f"Plugin '{plugin.meta.name}' torn down.")
            except Exception as exc:
                logger.warning(f"Teardown error for '{plugin.meta.name}': {exc}")

    def loaded_names(self) -> list[str]:
        return self._tracker.names()


# Module-level singleton
plugin_loader = PluginLoader()
