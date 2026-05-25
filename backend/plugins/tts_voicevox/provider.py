"""VOICEVOX TTS provider implementation."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import TTSProviderError
from nagiflow.plugin.base import BaseTTSProvider, TTSConfig, TTSResult


class VoicevoxProvider(BaseTTSProvider):
    """TTS provider using the VOICEVOX HTTP API (two-step: audio_query → synthesis)."""

    provider_name = "voicevox"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.VOICEVOX_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0),
        )

    async def _audio_query(self, text: str, speaker_id: int) -> dict:
        try:
            resp = await self._client.post("/audio_query", params={"text": text, "speaker": speaker_id})
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise TTSProviderError(f"VOICEVOX audio_query failed: {exc}") from exc
        return resp.json()

    async def _synthesis(self, query: dict, speaker_id: int) -> bytes:
        try:
            resp = await self._client.post(
                "/synthesis",
                params={"speaker": speaker_id},
                json=query,
                headers={"Content-Type": "application/json", "Accept": "audio/wav"},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise TTSProviderError(f"VOICEVOX synthesis failed: {exc}") from exc
        return resp.content

    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        if not text.strip():
            return TTSResult(audio_bytes=b"", sample_rate=24000)
        speaker = config.speaker_id or settings.DEFAULT_VOICEVOX_SPEAKER
        query = await self._audio_query(text, speaker)
        query["speedScale"] = config.speed
        query["pitchScale"] = config.pitch
        query["volumeScale"] = config.volume
        audio = await self._synthesis(query, speaker)
        return TTSResult(audio_bytes=audio, sample_rate=24000, format="wav")

    async def stream_synthesize(
        self, text: str, config: TTSConfig
    ) -> AsyncGenerator[bytes, None]:
        for sentence in self.split_into_sentences(text) or [text]:
            if sentence.strip():
                result = await self.synthesize(sentence, config)
                if result.audio_bytes:
                    yield result.audio_bytes

    async def list_speakers(self) -> list[dict]:
        try:
            resp = await self._client.get("/speakers")
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning(f"Could not fetch VOICEVOX speakers: {exc}")
            return []

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/version", timeout=3.0)
            return resp.is_success
        except Exception as exc:
            logger.warning(f"VOICEVOX health check failed: {exc}")
            return False
