"""
Base class for agent skills (LLM tools).

A skill is a callable unit of capability that the LLM agent can invoke
during a conversation.  Skills are registered in the SkillRegistry and
bound as tools to the CharacterAgent at request time.

To create a custom skill::

    from nagiflow.skills.base import BaseSkill, SkillParameter, SkillMeta

    class MySkill(BaseSkill):
        meta = SkillMeta(
            name="my_skill",
            display_name="My Skill",
            description="Does something useful.",
            parameters=[
                SkillParameter(name="query", type="string", description="Input query", required=True),
            ],
        )

        async def execute(self, query: str, **kwargs) -> str:
            return f"Result for: {query}"
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillParameter:
    name: str
    type: str  # "string" | "integer" | "number" | "boolean" | "array" | "object"
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None


@dataclass
class SkillMeta:
    """Static metadata describing a skill."""

    name: str  # Unique machine-readable identifier (used as tool name for LLM)
    display_name: str
    description: str
    parameters: list[SkillParameter] = field(default_factory=list)
    is_builtin: bool = True

    def to_json_schema(self) -> dict:
        """Return a JSON Schema object describing the skill's parameters."""
        properties: dict[str, Any] = {}
        required: list[str] = []
        for p in self.parameters:
            prop: dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def to_db_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "skill_type": "builtin" if self.is_builtin else "plugin",
            "entry_point": None,
            "default_config": {},
            "config_schema": self.to_json_schema(),
            "is_active": True,
            "is_builtin": self.is_builtin,
        }


class BaseSkill(ABC):
    """
    Abstract base for all NagiFlow skills.

    Subclasses must:
      1. Define a class-level ``meta: SkillMeta`` attribute.
      2. Implement ``execute(**kwargs) -> str`` where kwargs match the
         parameters declared in ``meta``.
    """

    meta: SkillMeta

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the skill and return a string result for the LLM."""

    async def __call__(self, **kwargs: Any) -> str:
        return await self.execute(**kwargs)

    def as_tool_definition(self) -> dict[str, Any]:
        """Return an OpenAI-style tool definition dict."""
        return {
            "type": "function",
            "function": {
                "name": self.meta.name,
                "description": self.meta.description,
                "parameters": self.meta.to_json_schema(),
            },
        }
