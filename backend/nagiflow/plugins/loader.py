"""
Plugin loader and registry.

Plugins are discovered from the workspace ``plugins/`` directory.  Each
sub-directory is treated as a Python package and dynamically imported.
The top-level ``__init__.py`` of each plugin must expose exactly one class
that inherits ``BasePlugin``.
"""

import importlib.util
import inspect
import sys
from pathlib import Path

from loguru import logger

from nagiflow.core.exceptions import PluginLoadError
from nagiflow.plugins.base import BasePlugin


class PluginRegistry:
    """Tracks loaded plugin instances."""

    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        self._plugins[plugin.meta.name] = plugin

    def get(self, name: str) -> BasePlugin | None:
        return self._plugins.get(name)

    def all(self) -> list[BasePlugin]:
        return list(self._plugins.values())

    def names(self) -> list[str]:
        return list(self._plugins.keys())


class PluginLoader:
    """Discovers and loads plugins from a directory."""

    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry

    def _find_plugin_class(self, module: object) -> type[BasePlugin] | None:
        """Return the first BasePlugin subclass found in *module*."""
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                return obj
        return None

    def _load_module_from_path(self, package_path: Path) -> object:
        """Dynamically import a plugin package given its directory path."""
        init_file = package_path / "__init__.py"
        if not init_file.exists():
            raise PluginLoadError(
                f"Plugin directory '{package_path}' has no __init__.py file."
            )

        # Add the parent directory to sys.path so the import works correctly
        parent = str(package_path.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)

        module_name = package_path.name
        spec = importlib.util.spec_from_file_location(module_name, init_file)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Could not create module spec for '{package_path}'.")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module

    async def load_from_directory(self, directory: Path) -> list[BasePlugin]:
        """
        Scan *directory* for plugin packages, import them, and call ``setup()``.

        Returns a list of successfully loaded plugin instances.
        """
        if not directory.exists():
            logger.debug(f"Plugin directory '{directory}' does not exist; skipping.")
            return []

        loaded: list[BasePlugin] = []

        for entry in sorted(directory.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_"):
                continue

            logger.info(f"Loading plugin: '{entry.name}'")
            try:
                module = self._load_module_from_path(entry)
                plugin_cls = self._find_plugin_class(module)
                if plugin_cls is None:
                    logger.warning(
                        f"Plugin '{entry.name}' has no BasePlugin subclass; skipping."
                    )
                    continue

                plugin = plugin_cls()
                await plugin.setup()
                self.registry.register(plugin)
                loaded.append(plugin)
                logger.info(
                    f"Plugin '{plugin.meta.name}' v{plugin.meta.version} loaded successfully."
                )
            except PluginLoadError:
                raise
            except Exception as exc:
                logger.error(f"Failed to load plugin '{entry.name}': {exc}", exc_info=True)

        return loaded

    async def unload_all(self) -> None:
        for plugin in self.registry.all():
            try:
                await plugin.teardown()
                logger.info(f"Plugin '{plugin.meta.name}' torn down.")
            except Exception as exc:
                logger.warning(f"Plugin teardown error for '{plugin.meta.name}': {exc}")


# Module-level singletons
plugin_registry = PluginRegistry()
plugin_loader = PluginLoader(plugin_registry)
