"""Character ORM model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from nagiflow.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from nagiflow.models.conversation import Conversation
    from nagiflow.models.knowledge import KnowledgeDocument
    from nagiflow.models.memory import LongTermMemory
    from nagiflow.models.skill import CharacterSkill
    from nagiflow.models.user import User


class Character(Base, TimestampMixin):
    """
    An AI Vtuber character profile.

    The ``personality`` JSON column stores the Big Five scores plus any
    custom free-form configuration supplied by the user.

    Example personality payload::

        {
            "big_five": {
                "openness": 75,
                "conscientiousness": 60,
                "extraversion": 80,
                "agreeableness": 70,
                "neuroticism": 40
            },
            "custom": {
                "catchphrase": "Let's go!",
                "speech_style": "casual",
                "interests": ["gaming", "anime"]
            }
        }
    """

    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Identity ---
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Personality ---
    personality: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # --- LLM / TTS / Avatar overrides (if null, global defaults are used) ---
    llm_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tts_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tts_speaker_id: Mapped[int | None] = mapped_column(nullable=True)
    avatar_provider: Mapped[str] = mapped_column(String(64), nullable=False, default="pngtuber")

    # --- Asset paths (workspace-relative) ---
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_sample_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_type: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )  # "live2d" | "3d"

    # --- Visibility ---
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)

    # --- Relationships ---
    owner: Mapped["User"] = relationship("User", back_populates="characters")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="character", cascade="all, delete-orphan"
    )
    memories: Mapped[list["LongTermMemory"]] = relationship(
        "LongTermMemory", back_populates="character", cascade="all, delete-orphan"
    )
    knowledge_docs: Mapped[list["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="character"
    )
    character_skills: Mapped[list["CharacterSkill"]] = relationship(
        "CharacterSkill", back_populates="character", cascade="all, delete-orphan"
    )
