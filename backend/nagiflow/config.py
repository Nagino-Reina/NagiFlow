"""
NagiFlow application settings.

All configuration is read from environment variables and/or a .env file via
pydantic-settings. Import the singleton `settings` object instead of
instantiating Settings directly.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    APP_NAME: str = "NagiFlow"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -------------------------------------------------------------------------
    # Workspace
    # -------------------------------------------------------------------------
    WORKSPACE_DIR: Path = Path("workspace")

    # Sub-paths (derived from WORKSPACE_DIR; do not override individually)
    @property
    def characters_dir(self) -> Path:
        return self.WORKSPACE_DIR / "characters"

    @property
    def knowledge_dir(self) -> Path:
        return self.WORKSPACE_DIR / "knowledge"

    @property
    def plugins_dir(self) -> Path:
        return self.WORKSPACE_DIR / "plugins"

    @property
    def audio_cache_dir(self) -> Path:
        return self.WORKSPACE_DIR / "audio_cache"

    @property
    def db_path(self) -> Path:
        return self.WORKSPACE_DIR / "nagiflow.db"

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DATABASE_URL: str = "sqlite+aiosqlite:///workspace/nagiflow.db"

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------------------------------------------------------
    # LLM
    # -------------------------------------------------------------------------
    DEFAULT_LLM_PROVIDER: Literal["ollama", "openai_compat"] = "ollama"
    DEFAULT_LLM_MODEL: str = "gpt-oss:20b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # -------------------------------------------------------------------------
    # TTS
    # -------------------------------------------------------------------------
    DEFAULT_TTS_PROVIDER: str = "voxcpm2"
    VOICEVOX_BASE_URL: str = "http://localhost:50021"
    DEFAULT_VOICEVOX_SPEAKER: int = 1

    # -------------------------------------------------------------------------
    # VoxCPM2 TTS (local inference)
    # -------------------------------------------------------------------------
    VOXCPM2_MODEL_ID: str = "openbmb/VoxCPM2"
    VOXCPM2_DEVICE: str = "auto"          # "auto" | "cpu" | "cuda" | "cuda:0"
    VOXCPM2_CFG_VALUE: float = 2.0        # classifier-free guidance strength
    VOXCPM2_INFERENCE_TIMESTEPS: int = 10  # diffusion steps
    VOXCPM2_LOAD_DENOISER: bool = False

    # -------------------------------------------------------------------------
    # Embedding
    # -------------------------------------------------------------------------
    EMBEDDING_PROVIDER: Literal["ollama_embed", "openai_embed", "simple"] = "ollama_embed"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSION: int = 768

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    CORS_ORIGINS: list[str] = ["*"]

    # -------------------------------------------------------------------------
    # Initial admin (bootstrapped on first startup)
    # -------------------------------------------------------------------------
    FIRST_ADMIN_EMAIL: str = ""
    FIRST_ADMIN_PASSWORD: str = ""

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @field_validator("WORKSPACE_DIR", mode="before")
    @classmethod
    def parse_workspace_dir(cls, v: str | Path) -> Path:
        return Path(v)

    @model_validator(mode="after")
    def _sync_db_url(self) -> "Settings":
        """If the default SQLite URL is used, anchor it to WORKSPACE_DIR."""
        if self.DATABASE_URL == "sqlite+aiosqlite:///workspace/nagiflow.db":
            self.DATABASE_URL = (
                f"sqlite+aiosqlite:///{self.WORKSPACE_DIR / 'nagiflow.db'}"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Convenience singleton
settings = get_settings()
