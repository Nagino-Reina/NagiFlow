"""Layered configuration (docs/03 §5, docs/14 §4).

Precedence (lowest → highest): built-in defaults → workspace config (`workspace/config/app.toml`)
→ environment (`.env` / `NAGIFLOW_*`). Runtime overrides (settings UI) layer on top later.
Secrets come from the environment only and are never read from the committed workspace TOML.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

_WORKSPACE_CONFIG = Path("workspace") / "config" / "app.toml"

# System default roleplay framing prepended to every character's persona (docs/03 §4, docs/08
# §4). Editable at runtime via the settings API (stored in `app_setting`); this is the fallback
# when no override is set. Actions are wrapped in parentheses so TTS can skip them.
DEFAULT_ROLEPLAY_PROMPT = (
    "You are this character in a live roleplay. Stay fully in character at all times and "
    "speak in the first person as them, never as an assistant. Reply in the user's language, "
    "naturally and conversationally, letting personality show through word choice and rhythm.\n\n"
    "Put physical actions, gestures, and expressions in parentheses, e.g. (smiles softly) or "
    "(glances away) — keep them short and only when they add to the moment. Everything outside "
    "parentheses is spoken aloud, so write it as natural speech.\n\n"
    "Never break character: do not mention being an AI, a model, or a prompt; add no "
    "disclaimers, no meta-commentary, no out-of-character notes. Keep replies focused and "
    "human-length — a few sentences unless the moment genuinely calls for more."
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NAGIFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        toml_file=_WORKSPACE_CONFIG,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Highest precedence first: init/runtime > env > .env > workspace TOML > secrets.
        # Missing TOML resolves to an empty layer, so it is safe to always include.
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    # --- workspace & data ---
    workspace_dir: Path = Field(default=Path("workspace"))

    # --- http server ---
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # --- providers (docs/06 §12) ---
    default_llm: str = "ollama"  # "ollama" | "echo"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"

    # TTS (docs/08 §4). Default is in-process VoxCPM (needs the [voxcpm] extra: torch + voxcpm;
    # the model downloads on first synthesis). "voxcpm_server" = a remote VoxCPM/OpenAI-compatible
    # server; "silent" = offline stub (a soft tone) for installs without a real TTS engine.
    # If the engine is missing, reply synthesis is skipped (best-effort) — chat still works.
    default_tts: str = "voxcpm"  # "voxcpm" | "voxcpm_server" | "silent"
    # Synthesize audio for each chat reply so it can be played back (docs/11 §4.6). Best-effort:
    # a TTS failure never blocks the text reply. Disable to skip synthesis entirely.
    synthesize_replies: bool = True
    voxcpm_model: str = "openbmb/VoxCPM2"  # HF id (in-process) or server model name
    voxcpm_load_denoiser: bool = False
    voxcpm_base_url: str = "http://127.0.0.1:9880"  # voxcpm_server only
    tts_sample_rate: int = 48000

    # Emotion & affect (docs/10). Appraisal engine: "hybrid" (LLM with deterministic
    # fallback), "deterministic" (lexicon/heuristic only — offline, reproducible), or "off".
    affect_appraisal: str = "hybrid"

    # --- roleplay / dialogue (docs/03 §4, docs/08 §4) ---
    # System default; the runtime override lives in `app_setting` and is edited in Settings.
    roleplay_prompt: str = DEFAULT_ROLEPLAY_PROMPT
    # Recent-turn window sent to the LLM as context (docs/03 §4). P1 keeps the last N turns
    # verbatim; a rolling summary for older history lands later.
    chat_history_window: int = 20

    # --- observability (docs/12 §2) ---
    # Push interval (seconds) for the system-status WebSocket (docs/05 §5.1). The client
    # holds one connection instead of polling several REST endpoints on a timer.
    status_stream_interval: float = 5.0

    # --- auth / sessions (docs/05 §2, docs/16 §3) ---
    session_ttl: int = 60 * 60 * 24 * 30  # 30 days
    guest_ttl: int = 60 * 60 * 24  # 1 day

    # --- misc ---
    log_level: str = "INFO"
    debug: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def db_path(self) -> Path:
        return self.workspace_dir / "nagiflow.db"

    @property
    def db_url(self) -> str:
        # async driver for SQLAlchemy
        return f"sqlite+aiosqlite:///{self.db_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
