"""Knowledge base endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import PaginationParams, get_current_active_user
from nagiflow.core.database import get_session
from nagiflow.core.workspace import workspace
from nagiflow.models.user import User
from nagiflow.schemas.common import MessageResponse
from nagiflow.schemas.knowledge import (
    KnowledgeDocCreate,
    KnowledgeDocResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)
from nagiflow.services.knowledge import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("", response_model=KnowledgeDocResponse, status_code=201)
async def create_document(
    data: KnowledgeDocCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> KnowledgeDocResponse:
    """
    Create a knowledge document from inline text.

    The text is split into chunks and embedded automatically.
    To upload a file instead, use ``POST /knowledge/upload``.
    """
    svc = KnowledgeService(db)
    doc = await svc.create(current_user.id, data)
    result = KnowledgeDocResponse.model_validate(doc)
    result.chunk_count = len(doc.chunks)
    return result


@router.post("/upload", response_model=KnowledgeDocResponse, status_code=201)
async def upload_document(
    title: str = Query(..., min_length=1, max_length=512),
    character_id: UUID | None = Query(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> KnowledgeDocResponse:
    """
    Upload a plain-text or markdown file as a knowledge document.

    The file is saved to the workspace and its content is chunked and embedded.
    """
    raw = await file.read()

    # Attempt UTF-8 decode; reject binary files
    try:
        text_content = raw.decode("utf-8")
    except UnicodeDecodeError:
        from nagiflow.core.exceptions import UnsupportedFileTypeError
        raise UnsupportedFileTypeError("Only UTF-8 text files are supported for knowledge upload.")

    # Save raw file to workspace
    dest = workspace.knowledge_dir() / str(current_user.id) / (file.filename or "upload.txt")
    await workspace.save_file(dest, raw)
    rel_path = workspace.relative_to_workspace(dest)

    data = KnowledgeDocCreate(
        title=title,
        content=text_content,
        source=file.filename,
        character_id=character_id,
    )
    svc = KnowledgeService(db)
    doc = await svc.create(current_user.id, data, file_path=rel_path)
    result = KnowledgeDocResponse.model_validate(doc)
    result.chunk_count = len(doc.chunks)
    return result


@router.get("", response_model=list[KnowledgeDocResponse])
async def list_documents(
    character_id: UUID | None = Query(default=None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[KnowledgeDocResponse]:
    """List knowledge documents for the current user."""
    svc = KnowledgeService(db)
    docs = await svc.list_for_user(
        current_user.id,
        character_id=character_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    results = []
    for doc in docs:
        r = KnowledgeDocResponse.model_validate(doc)
        r.chunk_count = len(doc.chunks) if doc.chunks else 0
        results.append(r)
    return results


@router.get("/{doc_id}", response_model=KnowledgeDocResponse)
async def get_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> KnowledgeDocResponse:
    """Get a knowledge document by ID."""
    svc = KnowledgeService(db)
    doc = await svc.get(doc_id, current_user.id)
    result = KnowledgeDocResponse.model_validate(doc)
    result.chunk_count = len(doc.chunks)
    return result


@router.delete("/{doc_id}", response_model=MessageResponse)
async def delete_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a knowledge document and all its chunks."""
    svc = KnowledgeService(db)
    await svc.delete(doc_id, current_user.id)
    return MessageResponse(message="Document deleted.")


@router.post("/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge(
    req: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[KnowledgeSearchResult]:
    """
    Semantic search over the knowledge base.

    Optionally scoped to a specific character's knowledge documents.
    """
    svc = KnowledgeService(db)
    return await svc.search(
        current_user.id, req.query,
        top_k=req.top_k,
        character_id=req.character_id,
    )
