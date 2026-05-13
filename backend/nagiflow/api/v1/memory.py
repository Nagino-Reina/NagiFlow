"""Long-term memory endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import PaginationParams, get_current_active_user
from nagiflow.core.database import get_session
from nagiflow.models.user import User
from nagiflow.schemas.common import MessageResponse
from nagiflow.schemas.memory import MemoryCreate, MemoryResponse, MemorySearchRequest, MemoryUpdate
from nagiflow.services.memory import MemoryService

router = APIRouter(prefix="/characters/{character_id}/memories", tags=["Memory"])


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(
    character_id: UUID,
    data: MemoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MemoryResponse:
    """Manually add a memory entry for a character."""
    svc = MemoryService(db)
    memory = await svc.create(character_id, current_user.id, data)
    return MemoryResponse.model_validate(memory)


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    character_id: UUID,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[MemoryResponse]:
    """List all memories for a character (owned by the current user)."""
    svc = MemoryService(db)
    memories = await svc.list_for_character(
        character_id, current_user.id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return [MemoryResponse.model_validate(m) for m in memories]


@router.post("/search", response_model=list[MemoryResponse])
async def search_memories(
    character_id: UUID,
    req: MemorySearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[MemoryResponse]:
    """Semantic search over a character's memories."""
    svc = MemoryService(db)
    results = await svc.search(
        character_id, current_user.id, req.query,
        top_k=req.top_k, min_importance=req.min_importance,
    )
    return [MemoryResponse.model_validate(m) for m, _ in results]


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    character_id: UUID,
    memory_id: UUID,
    data: MemoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MemoryResponse:
    """Update a memory entry."""
    svc = MemoryService(db)
    memory = await svc.update(memory_id, current_user.id, data)
    return MemoryResponse.model_validate(memory)


@router.delete("/{memory_id}", response_model=MessageResponse)
async def delete_memory(
    character_id: UUID,
    memory_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a specific memory entry."""
    svc = MemoryService(db)
    await svc.delete(memory_id, current_user.id)
    return MessageResponse(message="Memory deleted.")


@router.delete("", response_model=MessageResponse)
async def clear_memories(
    character_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete all memories for a character (irreversible)."""
    svc = MemoryService(db)
    count = await svc.delete_all_for_character(character_id, current_user.id)
    return MessageResponse(message=f"Deleted {count} memories.")
