"""Provider registry + configuration-driven selection (docs/03 §6).

Holds the active provider per capability and a fallback. P1 wires the LLM (Ollama default,
echo fallback) and TTS (VoxCPM default, offline silent fallback) capabilities; module-supplied
providers register here later (docs/06).
"""

from __future__ import annotations

from ..config import Settings
from ..core.logging import get_logger
from .base import LLMProvider, TTSProvider
from .llm.echo import EchoLLM
from .llm.ollama import OllamaLLM
from .tts.silent import SilentTTS
from .tts.voxcpm import VoxCPMTTS
from .tts.voxcpm_server import VoxCPMServerTTS

log = get_logger("nagiflow.providers")


class ProviderRegistry:
    def __init__(self) -> None:
        self._llm: dict[str, LLMProvider] = {}
        self._default_llm: str = "echo"
        self._echo = EchoLLM()
        self._tts: dict[str, TTSProvider] = {}
        self._default_tts: str = "silent"
        self._silent = SilentTTS()

    # --- LLM ---

    def register_llm(self, provider: LLMProvider, *, default: bool = False) -> None:
        self._llm[provider.name] = provider
        if default:
            self._default_llm = provider.name

    def get_llm(self, name: str | None = None) -> LLMProvider:
        return self._llm.get(name or self._default_llm, self._echo)

    @property
    def echo_llm(self) -> LLMProvider:
        return self._echo

    # --- TTS ---

    def register_tts(self, provider: TTSProvider, *, default: bool = False) -> None:
        self._tts[provider.name] = provider
        if default:
            self._default_tts = provider.name

    def get_tts(self, name: str | None = None) -> TTSProvider:
        return self._tts.get(name or self._default_tts, self._silent)

    @property
    def silent_tts(self) -> TTSProvider:
        return self._silent


def build_registry(settings: Settings) -> ProviderRegistry:
    reg = ProviderRegistry()

    reg.register_llm(EchoLLM())
    if settings.default_llm == "ollama":
        reg.register_llm(OllamaLLM(settings.ollama_base_url, settings.ollama_model), default=True)
    else:
        reg.register_llm(EchoLLM(), default=True)
        log.info("LLM default set to offline echo provider")

    reg.register_tts(SilentTTS())
    if settings.default_tts == "voxcpm":
        reg.register_tts(
            VoxCPMTTS(
                settings.voxcpm_model,
                settings.voxcpm_load_denoiser,
                settings.tts_sample_rate,
            ),
            default=True,
        )
    elif settings.default_tts == "voxcpm_server":
        reg.register_tts(
            VoxCPMServerTTS(
                settings.voxcpm_base_url,
                settings.voxcpm_model,
                settings.tts_sample_rate,
            ),
            default=True,
        )
    else:
        reg.register_tts(SilentTTS(), default=True)
        log.info("TTS default set to offline silent provider")

    return reg
