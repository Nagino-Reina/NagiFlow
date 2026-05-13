"""Skill and CharacterSkill ORM models."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from nagiflow.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from nagiflow.models.character import Character


class Skill(Base, TimestampMixin):
    """
    A registered agent skill (tool) that can be assigned to characters.

    Built-in skills are created at startup; user-defined skills can be
    registered by admin users or loaded from plugins.

    The ``config_schema`` column stores a JSON Schema describing the shape of
    ``config``, allowing the frontend to render a dynamic form.
    """

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)

    # Unique machine-readable identifier used as the tool name in the LLM
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # "builtin" | "plugin" | "custom"
    skill_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Python import path for dynamic loading: "nagiflow.skills.builtin.web_search:WebSearchSkill"
    entry_point: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Default configuration for this skill
    default_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # JSON Schema of expected config fields
    config_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    character_skills: Mapped[list["CharacterSkill"]] = relationship(
        "CharacterSkill", back_populates="skill", cascade="all, delete-orphan"
    )


class CharacterSkill(Base, TimestampMixin):
    """Association between a Character and a Skill with per-character config."""

    __tablename__ = "character_skills"
    __table_args__ = (UniqueConstraint("character_id", "skill_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Per-character skill configuration (overrides Skill.default_config)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    character: Mapped["Character"] = relationship("Character", back_populates="character_skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="character_skills")
