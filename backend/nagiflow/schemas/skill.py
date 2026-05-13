"""Skill Pydantic schemas."""

from typing import Any
from uuid import UUID

from nagiflow.schemas.common import OrmBase, TimestampSchema


class SkillResponse(TimestampSchema):
    id: UUID
    name: str
    display_name: str
    description: str
    skill_type: str
    default_config: dict[str, Any] | None
    config_schema: dict[str, Any] | None
    is_active: bool
    is_builtin: bool


class AssignSkillRequest(OrmBase):
    skill_id: UUID
    config: dict[str, Any] | None = None
    is_enabled: bool = True


class CharacterSkillResponse(OrmBase):
    id: UUID
    character_id: UUID
    skill_id: UUID
    skill_name: str
    skill_display_name: str
    config: dict[str, Any] | None
    is_enabled: bool
