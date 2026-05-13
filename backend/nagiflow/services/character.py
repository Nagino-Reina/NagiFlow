"""
Character service.

Handles character CRUD, asset management (avatar / voice samples /
Live2D & 3D model files), and skill assignment.
"""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nagiflow.core.exceptions import NotFoundError, PermissionDeniedError
from nagiflow.core.workspace import workspace
from nagiflow.models.character import Character
from nagiflow.models.skill import CharacterSkill, Skill
from nagiflow.schemas.character import CharacterCreate, CharacterUpdate
from nagiflow.schemas.skill import AssignSkillRequest


class CharacterService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(self, user_id: UUID, data: CharacterCreate) -> Character:
        personality_dict = data.personality.model_dump() if data.personality else None
        character = Character(
            user_id=user_id,
            name=data.name,
            description=data.description,
            system_prompt=data.system_prompt,
            personality=personality_dict,
            llm_provider=data.llm_provider,
            llm_model=data.llm_model,
            tts_provider=data.tts_provider,
            tts_speaker_id=data.tts_speaker_id,
            model_type=data.model_type,
            is_public=data.is_public,
        )
        self.db.add(character)
        await self.db.flush()
        await self.db.refresh(character)
        # Provision workspace directories
        await workspace.ensure_dir(workspace.character_dir(character.id))
        await workspace.ensure_dir(workspace.character_models_dir(character.id))
        await workspace.ensure_dir(workspace.character_voice_dir(character.id))
        await workspace.ensure_dir(workspace.character_avatar_dir(character.id))
        logger.info(f"Created character '{character.name}' ({character.id}) for user {user_id}")
        return character

    async def get(self, character_id: UUID, user_id: UUID | None = None) -> Character:
        """
        Fetch a character by ID.

        If *user_id* is provided, raises PermissionDeniedError unless the
        character belongs to that user or is marked public.
        """
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        if character is None:
            raise NotFoundError(f"Character '{character_id}' not found.")
        if user_id is not None:
            if character.user_id != user_id and not character.is_public:
                raise PermissionDeniedError()
        return character

    async def list_for_user(
        self, user_id: UUID, include_public: bool = False, limit: int = 50, offset: int = 0
    ) -> list[Character]:
        stmt = select(Character)
        if include_public:
            from sqlalchemy import or_
            stmt = stmt.where(
                or_(Character.user_id == user_id, Character.is_public.is_(True))
            )
        else:
            stmt = stmt.where(Character.user_id == user_id)
        stmt = stmt.order_by(Character.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, character_id: UUID, user_id: UUID, data: CharacterUpdate) -> Character:
        character = await self.get(character_id, user_id)
        if character.user_id != user_id:
            raise PermissionDeniedError()

        update_data = data.model_dump(exclude_unset=True)
        if "personality" in update_data and update_data["personality"] is not None:
            update_data["personality"] = data.personality.model_dump()  # type: ignore[union-attr]

        for field, value in update_data.items():
            setattr(character, field, value)

        await self.db.flush()
        await self.db.refresh(character)
        return character

    async def delete(self, character_id: UUID, user_id: UUID) -> None:
        character = await self.get(character_id, user_id)
        if character.user_id != user_id:
            raise PermissionDeniedError()
        await self.db.delete(character)
        await workspace.delete_character_workspace(character_id)
        logger.info(f"Deleted character {character_id}")

    # ------------------------------------------------------------------
    # Asset management
    # ------------------------------------------------------------------

    async def save_avatar(self, character_id: UUID, user_id: UUID, data: bytes, filename: str) -> str:
        character = await self.get(character_id, user_id)
        dest = workspace.character_avatar_dir(character_id) / filename
        await workspace.save_file(dest, data, allowed_extensions={".png", ".jpg", ".jpeg", ".webp", ".gif"})
        rel = workspace.relative_to_workspace(dest)
        character.avatar_path = rel
        await self.db.flush()
        return rel

    async def save_voice_sample(self, character_id: UUID, user_id: UUID, data: bytes, filename: str) -> str:
        character = await self.get(character_id, user_id)
        dest = workspace.character_voice_dir(character_id) / filename
        await workspace.save_file(dest, data, allowed_extensions={".wav", ".mp3", ".ogg", ".flac"})
        rel = workspace.relative_to_workspace(dest)
        character.voice_sample_path = rel
        await self.db.flush()
        return rel

    async def save_model_file(self, character_id: UUID, user_id: UUID, data: bytes, filename: str, model_type: str) -> str:
        character = await self.get(character_id, user_id)
        dest = workspace.character_models_dir(character_id) / filename
        await workspace.save_file(dest, data, allowed_extensions={".model3.json", ".moc3", ".zip", ".vrm", ".glb", ".gltf"})
        rel = workspace.relative_to_workspace(dest)
        character.model_path = rel
        character.model_type = model_type
        await self.db.flush()
        return rel

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    async def assign_skill(
        self, character_id: UUID, user_id: UUID, req: AssignSkillRequest
    ) -> CharacterSkill:
        character = await self.get(character_id, user_id)
        if character.user_id != user_id:
            raise PermissionDeniedError()

        # Verify skill exists
        skill_result = await self.db.execute(select(Skill).where(Skill.id == req.skill_id))
        skill = skill_result.scalar_one_or_none()
        if skill is None:
            raise NotFoundError(f"Skill '{req.skill_id}' not found.")

        # Check for existing assignment
        existing_result = await self.db.execute(
            select(CharacterSkill).where(
                CharacterSkill.character_id == character_id,
                CharacterSkill.skill_id == req.skill_id,
            )
        )
        cs = existing_result.scalar_one_or_none()
        if cs:
            cs.config = req.config
            cs.is_enabled = req.is_enabled
        else:
            cs = CharacterSkill(
                character_id=character_id,
                skill_id=req.skill_id,
                config=req.config,
                is_enabled=req.is_enabled,
            )
            self.db.add(cs)

        await self.db.flush()
        await self.db.refresh(cs)
        return cs

    async def remove_skill(self, character_id: UUID, user_id: UUID, skill_id: UUID) -> None:
        character = await self.get(character_id, user_id)
        if character.user_id != user_id:
            raise PermissionDeniedError()
        result = await self.db.execute(
            select(CharacterSkill).where(
                CharacterSkill.character_id == character_id,
                CharacterSkill.skill_id == skill_id,
            )
        )
        cs = result.scalar_one_or_none()
        if cs is None:
            raise NotFoundError("Skill assignment not found.")
        await self.db.delete(cs)

    async def get_skills(
        self, character_id: UUID, user_id: UUID
    ) -> list[CharacterSkill]:
        await self.get(character_id, user_id)  # ownership check
        result = await self.db.execute(
            select(CharacterSkill)
            .options(selectinload(CharacterSkill.skill))
            .where(
                CharacterSkill.character_id == character_id,
                CharacterSkill.is_enabled.is_(True),
            )
        )
        return list(result.scalars().all())
