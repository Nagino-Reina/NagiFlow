"""
Skills package.

Importing this package automatically registers all built-in skills via the
side-effects of the imports below.
"""

from nagiflow.skills.base import BaseSkill, SkillMeta, SkillParameter
from nagiflow.skills.registry import SkillRegistry, skill_registry

# Register built-ins by importing them (they self-register via @skill_registry.register)
from nagiflow.skills.builtin import calculator, web_search  # noqa: F401

__all__ = [
    "BaseSkill",
    "SkillMeta",
    "SkillParameter",
    "SkillRegistry",
    "skill_registry",
]
