"""
Central provider and skill registry.

All plugins register their providers and skills here.
Services obtain provider instances through this registry instead of
importing provider classes directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from nagiflow.plugin.base import (
    BaseAvatarProvider,
    BaseEmbeddingProvider,
    BaseLLMProvider,
    BaseSkill,
    BaseTTSProvider,
    SkillMeta,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ProviderRegistry:
    """Singleton registry for all provider types and skills."""

    def __init__(self) -> None:
        self._llm: dict[str, type[BaseLLMProvider]] = {}
        self._tts: dict[str, type[BaseTTSProvider]] = {}
        self._avatar: dict[str, type[BaseAvatarProvider]] = {}
        self._embedding: dict[str, type[BaseEmbeddingProvider]] = {}
        self._skills: dict[str, type[BaseSkill]] = {}

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    def register_llm(self, name: str, cls: type[BaseLLMProvider]) -> None:
        self._llm[name] = cls
        logger.info(f"Registered LLM provider: '{name}'")

    def get_llm(self, name: str | None = None) -> BaseLLMProvider:
        from nagiflow.config import settings
        n = name or settings.DEFAULT_LLM_PROVIDER
        cls = self._llm.get(n)
        if cls is None:
            raise ValueError(
                f"LLM provider '{n}' not registered. Available: {list(self._llm)}"
            )
        return cls()

    def list_llm(self) -> list[str]:
        return list(self._llm)

    # ------------------------------------------------------------------
    # TTS
    # ------------------------------------------------------------------

    def register_tts(self, name: str, cls: type[BaseTTSProvider]) -> None:
        self._tts[name] = cls
        logger.info(f"Registered TTS provider: '{name}'")

    def get_tts(self, name: str | None = None) -> BaseTTSProvider:
        from nagiflow.config import settings
        n = name or settings.DEFAULT_TTS_PROVIDER
        cls = self._tts.get(n)
        if cls is None:
            raise ValueError(
                f"TTS provider '{n}' not registered. Available: {list(self._tts)}"
            )
        return cls()

    def list_tts(self) -> list[str]:
        return list(self._tts)

    # ------------------------------------------------------------------
    # Avatar
    # ------------------------------------------------------------------

    def register_avatar(self, name: str, cls: type[BaseAvatarProvider]) -> None:
        self._avatar[name] = cls
        logger.info(f"Registered Avatar provider: '{name}'")

    def get_avatar(self, name: str | None = None) -> BaseAvatarProvider:
        from nagiflow.config import settings
        n = name or settings.DEFAULT_AVATAR_PROVIDER
        cls = self._avatar.get(n)
        if cls is None:
            raise ValueError(
                f"Avatar provider '{n}' not registered. Available: {list(self._avatar)}"
            )
        return cls()

    def list_avatar(self) -> list[str]:
        return list(self._avatar)

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def register_embedding(self, name: str, cls: type[BaseEmbeddingProvider]) -> None:
        self._embedding[name] = cls
        logger.info(f"Registered Embedding provider: '{name}'")

    def get_embedding(self, name: str | None = None) -> BaseEmbeddingProvider:
        from nagiflow.config import settings
        n = name or settings.EMBEDDING_PROVIDER
        cls = self._embedding.get(n)
        if cls is None:
            # Fallback to "simple" if registered
            if "simple" in self._embedding:
                logger.warning(f"Embedding provider '{n}' not found, falling back to 'simple'.")
                return self._embedding["simple"]()
            raise ValueError(
                f"Embedding provider '{n}' not registered. Available: {list(self._embedding)}"
            )
        return cls()

    def list_embedding(self) -> list[str]:
        return list(self._embedding)

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    def register_skill(self, cls: type[BaseSkill]) -> type[BaseSkill]:
        """Register a skill class. Can be used as a decorator."""
        name = cls.meta.name
        if name in self._skills:
            logger.warning(f"Skill '{name}' is being overwritten.")
        self._skills[name] = cls
        logger.debug(f"Registered skill: '{name}'")
        return cls

    def get_skill(self, name: str) -> type[BaseSkill] | None:
        return self._skills.get(name)

    def get_skill_or_raise(self, name: str) -> type[BaseSkill]:
        cls = self.get_skill(name)
        if cls is None:
            raise KeyError(f"Skill '{name}' is not registered.")
        return cls

    def list_skills(self) -> list[type[BaseSkill]]:
        return list(self._skills.values())

    def instantiate_skill(self, name: str, config: dict[str, Any] | None = None) -> BaseSkill:
        cls = self.get_skill_or_raise(name)
        return cls(config=config)

    def instantiate_skills_for_character(
        self,
        skill_names: list[str],
        configs: dict[str, dict[str, Any]] | None = None,
    ) -> list[BaseSkill]:
        configs = configs or {}
        result: list[BaseSkill] = []
        for name in skill_names:
            cls = self.get_skill(name)
            if cls is None:
                logger.warning(f"Skill '{name}' not found; skipping.")
                continue
            result.append(cls(config=configs.get(name)))
        return result

    async def sync_skills_to_db(self, db: "AsyncSession") -> None:
        """Upsert all registered skills into the database on startup."""
        from sqlalchemy import select

        from nagiflow.models.skill import Skill

        for skill_cls in self._skills.values():
            meta: SkillMeta = skill_cls.meta
            stmt = select(Skill).where(Skill.name == meta.name)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Skill(**meta.to_db_dict()))
                logger.info(f"Inserted skill '{meta.name}' into database.")
            else:
                for k, v in meta.to_db_dict().items():
                    setattr(existing, k, v)
        await db.commit()
        logger.info(f"Synced {len(self._skills)} skills to database.")

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def summary(self) -> dict[str, list[str]]:
        return {
            "llm": self.list_llm(),
            "tts": self.list_tts(),
            "avatar": self.list_avatar(),
            "embedding": self.list_embedding(),
            "skills": [cls.meta.name for cls in self.list_skills()],
        }


# Global singleton
registry = ProviderRegistry()
