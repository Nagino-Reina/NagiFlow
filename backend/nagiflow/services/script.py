"""Script / Screenplay service."""

from __future__ import annotations

import io
import uuid
import zipfile
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nagiflow.core.exceptions import NotFoundError, PermissionDeniedError
from nagiflow.core.workspace import workspace
from nagiflow.models.script import Script, ScriptLine, ScriptScene
from nagiflow.schemas.script import (
    ScriptCreate,
    ScriptLineCreate,
    ScriptLineUpdate,
    ScriptSceneCreate,
    ScriptSceneUpdate,
    ScriptUpdate,
)


class ScriptService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Script CRUD
    # ------------------------------------------------------------------

    async def create(self, user_id: UUID, data: ScriptCreate) -> Script:
        script = Script(owner_id=user_id, **data.model_dump())
        self.db.add(script)
        await self.db.flush()
        await self.db.refresh(script)
        return script

    async def get(self, script_id: UUID, user_id: UUID, *, detail: bool = False) -> Script:
        stmt = select(Script).where(Script.id == script_id)
        if detail:
            stmt = stmt.options(
                selectinload(Script.scenes).selectinload(ScriptScene.lines)
            )
        result = await self.db.execute(stmt)
        script = result.scalar_one_or_none()
        if script is None:
            raise NotFoundError(f"Script '{script_id}' not found.")
        if script.owner_id != user_id:
            raise PermissionDeniedError()
        return script

    async def list_for_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Script]:
        result = await self.db.execute(
            select(Script)
            .where(Script.owner_id == user_id)
            .order_by(Script.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, script_id: UUID, user_id: UUID, data: ScriptUpdate) -> Script:
        script = await self.get(script_id, user_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(script, k, v)
        await self.db.flush()
        await self.db.refresh(script)
        return script

    async def delete(self, script_id: UUID, user_id: UUID) -> None:
        script = await self.get(script_id, user_id)
        await self.db.delete(script)

    # ------------------------------------------------------------------
    # Scene CRUD
    # ------------------------------------------------------------------

    async def create_scene(
        self, script_id: UUID, user_id: UUID, data: ScriptSceneCreate
    ) -> ScriptScene:
        await self.get(script_id, user_id)
        scene = ScriptScene(script_id=script_id, **data.model_dump())
        self.db.add(scene)
        await self.db.flush()
        await self.db.refresh(scene)
        return scene

    async def get_scene(
        self, script_id: UUID, scene_id: UUID, user_id: UUID
    ) -> ScriptScene:
        await self.get(script_id, user_id)
        result = await self.db.execute(
            select(ScriptScene).where(
                ScriptScene.id == scene_id, ScriptScene.script_id == script_id
            )
        )
        scene = result.scalar_one_or_none()
        if scene is None:
            raise NotFoundError(f"Scene '{scene_id}' not found.")
        return scene

    async def update_scene(
        self, script_id: UUID, scene_id: UUID, user_id: UUID, data: ScriptSceneUpdate
    ) -> ScriptScene:
        scene = await self.get_scene(script_id, scene_id, user_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(scene, k, v)
        await self.db.flush()
        await self.db.refresh(scene)
        return scene

    async def delete_scene(
        self, script_id: UUID, scene_id: UUID, user_id: UUID
    ) -> None:
        scene = await self.get_scene(script_id, scene_id, user_id)
        await self.db.delete(scene)

    # ------------------------------------------------------------------
    # Line CRUD
    # ------------------------------------------------------------------

    async def create_line(
        self, script_id: UUID, scene_id: UUID, user_id: UUID, data: ScriptLineCreate
    ) -> ScriptLine:
        await self.get_scene(script_id, scene_id, user_id)
        line = ScriptLine(scene_id=scene_id, **data.model_dump())
        self.db.add(line)
        await self.db.flush()
        await self.db.refresh(line)
        return line

    async def get_line(
        self, script_id: UUID, scene_id: UUID, line_id: UUID, user_id: UUID
    ) -> ScriptLine:
        await self.get_scene(script_id, scene_id, user_id)
        result = await self.db.execute(
            select(ScriptLine).where(
                ScriptLine.id == line_id, ScriptLine.scene_id == scene_id
            )
        )
        line = result.scalar_one_or_none()
        if line is None:
            raise NotFoundError(f"Line '{line_id}' not found.")
        return line

    async def update_line(
        self,
        script_id: UUID,
        scene_id: UUID,
        line_id: UUID,
        user_id: UUID,
        data: ScriptLineUpdate,
    ) -> ScriptLine:
        line = await self.get_line(script_id, scene_id, line_id, user_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(line, k, v)
        await self.db.flush()
        await self.db.refresh(line)
        return line

    async def delete_line(
        self, script_id: UUID, scene_id: UUID, line_id: UUID, user_id: UUID
    ) -> None:
        line = await self.get_line(script_id, scene_id, line_id, user_id)
        await self.db.delete(line)

    # ------------------------------------------------------------------
    # TTS Synthesis
    # ------------------------------------------------------------------

    async def synthesize_line(
        self, script_id: UUID, scene_id: UUID, line_id: UUID, user_id: UUID
    ) -> ScriptLine:
        """Synthesise TTS for a single script line."""
        from nagiflow.config import settings
        from nagiflow.plugin.base import TTSConfig
        from nagiflow.plugin.registry import registry

        line = await self.get_line(script_id, scene_id, line_id, user_id)
        if not line.text.strip():
            return line

        tts_provider_name = settings.DEFAULT_TTS_PROVIDER
        speaker_id = settings.DEFAULT_VOICEVOX_SPEAKER

        # If line has a character, use its overrides
        if line.character_id:
            from nagiflow.models.character import Character
            result = await self.db.execute(
                select(Character).where(Character.id == line.character_id)
            )
            char = result.scalar_one_or_none()
            if char:
                tts_provider_name = char.tts_provider or tts_provider_name
                speaker_id = char.tts_speaker_id or speaker_id

        tts = registry.get_tts(tts_provider_name)
        config = TTSConfig(speaker_id=speaker_id)
        tts_result = await tts.synthesize(line.text, config)

        filename = f"{uuid.uuid4()}.wav"
        dest = workspace.audio_cache_dir() / "scripts" / str(line_id) / filename
        await workspace.save_file(dest, tts_result.audio_bytes)

        line.audio_path = str(workspace.relative_to_workspace(dest))
        line.duration_ms = tts_result.duration_ms
        await self.db.flush()
        await self.db.refresh(line)
        return line

    async def synthesize_all(self, script_id: UUID, user_id: UUID) -> int:
        """Synthesise all lines without audio. Returns count of synthesised lines."""
        script = await self.get(script_id, user_id, detail=True)
        count = 0
        for scene in script.scenes:
            for line in scene.lines:
                if line.audio_path is None and line.text.strip():
                    try:
                        await self.synthesize_line(
                            script_id, scene.id, line.id, user_id
                        )
                        count += 1
                    except Exception as exc:
                        logger.warning(f"TTS failed for line {line.id}: {exc}")
        return count

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    async def export_zip(self, script_id: UUID, user_id: UUID) -> bytes:
        """Return a ZIP archive of all WAV files + an SRT subtitle file."""
        script = await self.get(script_id, user_id, detail=True)

        buf = io.BytesIO()
        srt_lines: list[str] = []
        srt_index = 1

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for scene in sorted(script.scenes, key=lambda s: s.order):
                for line in sorted(scene.lines, key=lambda l: l.order):
                    if line.audio_path:
                        abs_path = workspace.abs_path(line.audio_path)
                        if abs_path.exists():
                            arcname = f"{scene.order:03d}/{line.order:04d}_{line.id}.wav"
                            zf.write(abs_path, arcname)

                    if line.text.strip():
                        ms = line.duration_ms or 0
                        start_ms = 0
                        end_ms = max(ms, 1000)
                        srt_lines.append(
                            f"{srt_index}\n"
                            f"{_ms_to_srt(start_ms)} --> {_ms_to_srt(end_ms)}\n"
                            f"{line.text}\n"
                        )
                        srt_index += 1

            if srt_lines:
                zf.writestr("subtitles.srt", "\n".join(srt_lines))

        return buf.getvalue()


def _ms_to_srt(ms: int) -> str:
    h, remainder = divmod(ms, 3_600_000)
    m, remainder = divmod(remainder, 60_000)
    s, millis = divmod(remainder, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"
