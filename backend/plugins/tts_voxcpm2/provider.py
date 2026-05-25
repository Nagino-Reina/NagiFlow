"""
VoxCPM2 TTS provider (local inference).

Install: pip install voxcpm soundfile
Model (~2 GB) downloaded from Hugging Face on first use.

Extra TTSConfig fields (via config.extra):
    cfg_value (float)            – Classifier-free guidance strength (default 2.0)
    inference_timesteps (int)    – Diffusion steps (default 10)
    voice_description (str)      – Voice Design: describe the voice in natural language
    ref_audio (np.ndarray)       – Voice Cloning: reference audio array
    ref_text (str)               – Voice Cloning: transcript of reference audio
"""

from __future__ import annotations

import asyncio
import functools
import io
from typing import TYPE_CHECKING, Any

from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import TTSProviderError
from nagiflow.plugin.base import BaseTTSProvider, TTSConfig, TTSResult

if TYPE_CHECKING:
    import numpy as np


def _resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _numpy_to_wav(wav: "np.ndarray", sample_rate: int) -> bytes:
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, wav, sample_rate, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


class VoxCPM2Provider(BaseTTSProvider):
    provider_name = "voxcpm2"

    def __init__(
        self,
        model_id: str | None = None,
        device: str | None = None,
        load_denoiser: bool | None = None,
    ) -> None:
        self.model_id = model_id or settings.VOXCPM2_MODEL_ID
        self._device_str = device or settings.VOXCPM2_DEVICE
        self._load_denoiser = (
            load_denoiser if load_denoiser is not None else settings.VOXCPM2_LOAD_DENOISER
        )
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from voxcpm import VoxCPM
        except ImportError as exc:
            raise TTSProviderError(
                "VoxCPM2 not installed. Run: pip install voxcpm soundfile"
            ) from exc

        logger.info(f"Loading VoxCPM2 model '{self.model_id}' …")
        model = VoxCPM.from_pretrained(self.model_id, load_denoiser=self._load_denoiser)
        device = _resolve_device(self._device_str)
        try:
            model = model.to(device)
            logger.info(f"VoxCPM2 on device '{device}'.")
        except Exception as exc:
            logger.warning(f"Could not move VoxCPM2 to '{device}': {exc}")
        self._model = model
        return self._model

    def _do_generate(self, text: str, config: TTSConfig) -> tuple[bytes, int]:
        model = self._load()
        extra = config.extra or {}
        kwargs: dict[str, Any] = {
            "text": text,
            "cfg_value": float(extra.get("cfg_value", settings.VOXCPM2_CFG_VALUE)),
            "inference_timesteps": int(extra.get("inference_timesteps", settings.VOXCPM2_INFERENCE_TIMESTEPS)),
        }
        for key in ("voice_description", "ref_audio", "ref_text"):
            if key in extra:
                kwargs[key] = extra[key]
        try:
            wav = model.generate(**kwargs)
        except Exception as exc:
            raise TTSProviderError(f"VoxCPM2 generation failed: {exc}") from exc
        sample_rate: int = model.tts_model.sample_rate
        return _numpy_to_wav(wav, sample_rate), sample_rate

    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        if not text.strip():
            return TTSResult(audio_bytes=b"", sample_rate=48000)
        loop = asyncio.get_event_loop()
        try:
            audio_bytes, sample_rate = await loop.run_in_executor(
                None, functools.partial(self._do_generate, text, config)
            )
        except TTSProviderError:
            raise
        except Exception as exc:
            raise TTSProviderError(f"VoxCPM2 error: {exc}") from exc
        return TTSResult(audio_bytes=audio_bytes, sample_rate=sample_rate, format="wav")

    async def health_check(self) -> bool:
        try:
            import voxcpm  # noqa: F401
            return True
        except ImportError:
            logger.warning("VoxCPM2: 'voxcpm' package not installed.")
            return False
