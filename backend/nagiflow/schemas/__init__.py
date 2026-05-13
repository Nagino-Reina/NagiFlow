"""NagiFlow Pydantic schemas."""

from nagiflow.schemas.character import (
    BigFivePersonality,
    CharacterBrief,
    CharacterCreate,
    CharacterResponse,
    CharacterUpdate,
    PersonalityConfig,
)
from nagiflow.schemas.common import MessageResponse, OrmBase, PaginatedResponse, TimestampSchema
from nagiflow.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationResponse,
    MessageResponse as ConvMessageResponse,
)
from nagiflow.schemas.knowledge import (
    KnowledgeDocCreate,
    KnowledgeDocResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)
from nagiflow.schemas.memory import MemoryCreate, MemoryResponse, MemorySearchRequest, MemoryUpdate
from nagiflow.schemas.skill import AssignSkillRequest, CharacterSkillResponse, SkillResponse
from nagiflow.schemas.user import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserPasswordChange,
    UserResponse,
    UserUpdate,
)

__all__ = [
    "OrmBase",
    "TimestampSchema",
    "PaginatedResponse",
    "MessageResponse",
    "UserCreate",
    "UserUpdate",
    "UserPasswordChange",
    "UserResponse",
    "TokenResponse",
    "LoginRequest",
    "RefreshRequest",
    "BigFivePersonality",
    "PersonalityConfig",
    "CharacterCreate",
    "CharacterUpdate",
    "CharacterResponse",
    "CharacterBrief",
    "ConversationCreate",
    "ConversationResponse",
    "ConversationDetail",
    "ConvMessageResponse",
    "ChatRequest",
    "ChatResponse",
    "MemoryCreate",
    "MemoryUpdate",
    "MemoryResponse",
    "MemorySearchRequest",
    "KnowledgeDocCreate",
    "KnowledgeDocResponse",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResult",
    "SkillResponse",
    "AssignSkillRequest",
    "CharacterSkillResponse",
]
