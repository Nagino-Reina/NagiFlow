"""
VoxCPM2 TTS provider (local inference).

VoxCPM2 is a tokenizer-free, diffusion autoregressive TTS model by OpenBMB
that supports 30 languages, voice design from text descriptions, and voice cloning.

Requirements:
    pip install "nagiflow[voxcpm2]"   # or: pip install voxcpm soundfile
    Python >=3.10, PyTorch >=2.5.0, CUDA >=12.0 (optional, CPU works but is slow)

The model (~2 GB) is downloaded from Hugging Face on first use and cached in
the standard HuggingFace cache directory.

Config (via TTSConfig.extra):
    cfg_value (float)         – Classifier-free guidance strength (default 2.0)
    inference_timesteps (int) – Diffusion steps; more steps → higher quality but slower
    voice_description (str)   – Natural-language description for Voice Design mode
    ref_audio (np.ndarray)    – Reference audio array for Voice Cloning mode
    ref_text (str)            – Transcript of the reference audio
"""

from __future__ import annotations

import asyncio
import functools
import io
from typing import TYPE_CHECKING, Any

from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import TTSProviderError
from nagiflow.tts.base import BaseTTSProvider, TTSConfig, TTSResult

if TYPE_CHECKING:
    import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_device(device: str) -> str:
    """Resolve "auto" to "cuda" or "cpu" depending on torch availability."""
    if device != "auto":
        return device
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _numpy_to_wav(wav: "np.ndarray", sample_rate: int) -> bytes:
    """Encode a float32 numpy array as a PCM-16 WAV in memory."""
    import soundfile as sf

    buf = io.BytesIO()
    sf.write(buf, wav, sample_rate, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class VoxCPM2Provider(BaseTTSProvider):
    """
    TTS provider backed by VoxCPM2 running locally.

    The model is loaded lazily on the first synthesis call and cached for the
    lifetime of the provider instance.  Blocking inference is dispatched to a
    thread executor so it does not stall the async event loop.
    """

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
        self._model: Any = None  # VoxCPM instance, populated on first use

    # ------------------------------------------------------------------
    # Internal helpers (run in thread executor)
    # ------------------------------------------------------------------

    def _load(self) -> Any:
        """Load (or return the cached) VoxCPM2 model."""
        if self._model is not None:
            return self._model

        try:
            from voxcpm import VoxCPM
        except ImportError as exc:
            raise TTSProviderError(
                "VoxCPM2 is not installed. "
                "Run: pip install voxcpm  (or: pip install 'nagiflow[voxcpm2]')"
            ) from exc

        logger.info(f"Loading VoxCPM2 model '{self.model_id}' …")
        model = VoxCPM.from_pretrained(self.model_id, load_denoiser=self._load_denoiser)

        device = _resolve_device(self._device_str)
        try:
            model = model.to(device)
            logger.info(f"VoxCPM2 loaded on device '{device}'.")
        except Exception as exc:
            logger.warning(f"Could not move VoxCPM2 to '{device}': {exc}. Using default device.")

        self._model = model
        return self._model

    def _do_generate(self, text: str, config: TTSConfig) -> tuple[bytes, int]:
        """Blocking synthesis — intended to run inside a thread executor."""
        model = self._load()
        extra = config.extra or {}

        kwargs: dict[str, Any] = {
            "text": text,
            "cfg_value": float(extra.get("cfg_value", settings.VOXCPM2_CFG_VALUE)),
            "inference_timesteps": int(
                extra.get("inference_timesteps", settings.VOXCPM2_INFERENCE_TIMESTEPS)
            ),
        }

        # Voice Design mode – generate a novel voice from a text description
        if "voice_description" in extra:
            kwargs["voice_description"] = extra["voice_description"]

        # Voice Cloning mode – clone a voice from reference audio + transcript
        if "ref_audio" in extra:
            kwargs["ref_audio"] = extra["ref_audio"]
        if "ref_text" in extra:
            kwargs["ref_text"] = extra["ref_text"]

        try:
            wav = model.generate(**kwargs)
        except Exception as exc:
            raise TTSProviderError(f"VoxCPM2 generation failed: {exc}") from exc

        sample_rate: int = model.tts_model.sample_rate
        return _numpy_to_wav(wav, sample_rate), sample_rate

    # ------------------------------------------------------------------
    # BaseTTSProvider interface
    # ------------------------------------------------------------------

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
            raise TTSProviderError(f"VoxCPM2 unexpected error: {exc}") from exc

        return TTSResult(audio_bytes=audio_bytes, sample_rate=sample_rate, format="wav")

    async def health_check(self) -> bool:
        """Returns True when the voxcpm package is importable (no model load)."""
        try:
            import voxcpm  # noqa: F401

            return True
        except ImportError:
            logger.warning("VoxCPM2 health check failed: 'voxcpm' package not installed.")
            return False
