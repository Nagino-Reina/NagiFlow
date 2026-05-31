"""String enums used across models (kept as plain str constants for SQLite portability)."""

from __future__ import annotations

from enum import StrEnum


class UserKind(StrEnum):
    GUEST = "guest"
    LOCAL = "local"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class SessionKind(StrEnum):
    GUEST = "guest"
    USER = "user"


class CharacterStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class AvatarRenderer(StrEnum):
    PNGTUBER = "pngtuber"
    LIVE2D = "live2d"
    THREE_D = "3d"
    EXTERNAL = "external"


class ConversationMode(StrEnum):
    CHAT = "chat"
    LIVE = "live"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class MessageRole(StrEnum):
    USER = "user"
    CHARACTER = "character"
    SYSTEM = "system"
    TOOL = "tool"


class ParticipantRole(StrEnum):
    PRIMARY = "primary"
    CAST = "cast"
