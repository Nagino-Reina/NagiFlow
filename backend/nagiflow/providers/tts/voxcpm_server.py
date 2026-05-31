"""VoxCPM TTS over a remote server (docs/06 §12, docs/08 §4 — external-service seam).

Optional alternative to the in-process `voxcpm.VoxCPMTTS`: talks to a VoxCPM/OpenAI-compatible
TTS server over `/v1/audio/speech` (docs/03 §8). Useful when the model runs on a separate GPU
box. Select it with `NAGIFLOW_DEFAULT_TTS=voxcpm_server`.
"""

from __future__ import annotations

import httpx

from ..base import ProviderError, TTSCaps, VoiceRef


class VoxCPMServerTTS:
    name = "voxcpm_server"

    def __init__(self, base_url: str, model: str, sample_rate: int = 48000) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.capabilities = TTSCaps(
            streaming=True, voice_clone=True, voice_design=False, fine_tune=False,
            sample_rate=sample_rate,
        )

    async def synthesize(
        self,
        *,
        text: str,
        voice: VoiceRef,
        style: str | None = None,
        speech_rate: float = 1.0,
    ) -> bytes:
        payload: dict = {
            "model": self.model,
            "input": text,
            "voice": voice.params.get("voice", "default"),
            "response_format": "wav",
            "speed": speech_rate,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if voice.kind == "zero_shot" and voice.reference_paths:
                    with open(voice.reference_paths[0], "rb") as ref:
                        files = {"reference": ("reference.wav", ref, "audio/wav")}
                        resp = await client.post(
                            f"{self.base_url}/v1/audio/speech", data=payload, files=files,
                        )
                else:
                    resp = await client.post(f"{self.base_url}/v1/audio/speech", json=payload)
                resp.raise_for_status()
                return resp.content
        except (httpx.HTTPError, OSError) as exc:
            raise ProviderError(f"VoxCPM server request failed: {exc}") from exc

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code < 500
        except (httpx.HTTPError, OSError):
            return False
