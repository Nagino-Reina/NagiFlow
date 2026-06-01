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

    # TTS (docs/08 §4). Default to the offline stub so the base install runs with no heavy
    # deps. "voxcpm" = in-process generation (needs the [voxcpm] extra: torch + voxcpm);
    # "voxcpm_server" = a remote VoxCPM/OpenAI-compatible server.
    default_tts: str = "silent"  # "voxcpm" | "voxcpm_server" | "silent"
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
