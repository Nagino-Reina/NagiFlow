"""
ORM models package.

All model classes must be imported here so that SQLAlchemy's metadata is
populated before Alembic or ``create_all_tables()`` is called.
"""

from nagiflow.models.base import Base, TimestampMixin, new_uuid
from nagiflow.models.character import Character
from nagiflow.models.conversation import Conversation, Message
from nagiflow.models.knowledge import KnowledgeChunk, KnowledgeDocument
from nagiflow.models.memory import LongTermMemory
from nagiflow.models.skill import CharacterSkill, Skill
from nagiflow.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "new_uuid",
    "User",
    "Character",
    "Conversation",
    "Message",
    "LongTermMemory",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "Skill",
    "CharacterSkill",
]
