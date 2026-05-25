"""NagiFlow plugin system."""

from nagiflow.plugin.base import (
    AvatarState,
    BaseAvatarProvider,
    BaseEmbeddingProvider,
    BaseLLMProvider,
    BasePlugin,
    BaseSkill,
    BaseTTSProvider,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    PluginMeta,
    SkillMeta,
    SkillParameter,
    TTSConfig,
    TTSResult,
)
from nagiflow.plugin.loader import plugin_loader
from nagiflow.plugin.registry import registry

__all__ = [
    # Base classes
    "BasePlugin",
    "PluginMeta",
    "BaseLLMProvider",
    "LLMMessage",
    "LLMConfig",
    "LLMResponse",
    "BaseTTSProvider",
    "TTSConfig",
    "TTSResult",
    "BaseAvatarProvider",
    "AvatarState",
    "BaseEmbeddingProvider",
    "BaseSkill",
    "SkillMeta",
    "SkillParameter",
    # Singletons
    "registry",
    "plugin_loader",
]
