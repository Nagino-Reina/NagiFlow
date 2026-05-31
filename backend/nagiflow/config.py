"""Layered configuration (docs/03 §5, docs/13 §4).

Precedence (lowest → highest): built-in defaults → workspace config → environment
→ runtime overrides. This module covers defaults + environment (the `.env` / `NAGIFLOW_*`
layer); workspace TOML and runtime overrides layer on top later.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NAGIFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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

    # --- auth / sessions (docs/05 §2, docs/15 §3) ---
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
