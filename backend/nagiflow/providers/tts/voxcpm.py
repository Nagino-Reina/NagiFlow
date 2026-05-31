"""VoxCPM TTS provider — in-process generation (docs/06 §12, docs/08 §4 — default TTS).

Uses the official `voxcpm` Python package directly (no server): `VoxCPM.from_pretrained(...)`
then `model.generate(...)`, which returns a NumPy waveform encoded here to WAV. Zero-shot
cloning passes `prompt_wav_path` + `prompt_text` (the reference transcript). The heavy deps
(torch, voxcpm, soundfile) are optional and imported lazily, so the base install runs on the
offline silent stub until VoxCPM is wanted. For a remote engine instead, see
`voxcpm_server.VoxCPMServerTTS`.
"""

from __future__ import annotations

import asyncio
import io

from ..base import ProviderError, TTSCaps, VoiceRef


class VoxCPMTTS:
    name = "voxcpm"

    def __init__(
        self,
        model_id: str = "openbmb/VoxCPM2",
        load_denoiser: bool = False,
        sample_rate: int = 48000,
        *,
        cfg_value: float = 2.0,
        inference_timesteps: int = 10,
    ) -> None:
        self.model_id = model_id
        self.load_denoiser = load_denoiser
        self.cfg_value = cfg_value
        self.inference_timesteps = inference_timesteps
        self._sample_rate = sample_rate
        self._model = None  # lazily loaded on first synthesis
        # VoxCPM clones from a reference clip + transcript; it has no text-only voice design
        # and the simple API returns a full waveform (no streaming).
        self.capabilities = TTSCaps(
            streaming=False, voice_clone=True, voice_design=False, fine_tune=False,
            sample_rate=sample_rate,
        )

    def _load(self):  # noqa: ANN202 - third-party model object
        if self._model is None:
            try:
                from voxcpm import VoxCPM
            except ImportError as exc:
                raise ProviderError(
                    "VoxCPM is not installed. Install the optional extra: "
                    "`uv pip install -e '.[voxcpm]'` (requires PyTorch + CUDA)."
                ) from exc
            self._model = VoxCPM.from_pretrained(self.model_id, load_denoiser=self.load_denoiser)
        return self._model

    def _synthesize_sync(self, text: str, voice: VoiceRef) -> bytes:
        try:
            import soundfile as sf
        except ImportError as exc:
            raise ProviderError(
                "soundfile is not installed. Install the optional extra: "
                "`uv pip install -e '.[voxcpm]'`."
            ) from exc

        model = self._load()
        kwargs: dict = {
            "text": text,
            "cfg_value": self.cfg_value,
            "inference_timesteps": self.inference_timesteps,
        }
        if voice.kind == "zero_shot" and voice.reference_paths:
            kwargs["prompt_wav_path"] = voice.reference_paths[0]
            transcript = voice.params.get("sample_text")
            if transcript:
                kwargs["prompt_text"] = transcript

        try:
            wav = model.generate(**kwargs)
        except Exception as exc:  # noqa: BLE001 - isolate any model/runtime failure
            raise ProviderError(f"VoxCPM generation failed: {exc}") from exc

        sample_rate = getattr(getattr(model, "tts_model", None), "sample_rate", self._sample_rate)
        buf = io.BytesIO()
        sf.write(buf, wav, sample_rate, format="WAV", subtype="PCM_16")
        return buf.getvalue()

    async def synthesize(
        self,
        *,
        text: str,
        voice: VoiceRef,
        style: str | None = None,
        speech_rate: float = 1.0,
    ) -> bytes:
        # Model load + generation are blocking/CPU-GPU bound — keep them off the event loop.
        return await asyncio.to_thread(self._synthesize_sync, text, voice)

    async def health(self) -> bool:
        try:
            import voxcpm  # noqa: F401
        except ImportError:
            return False
        return True
