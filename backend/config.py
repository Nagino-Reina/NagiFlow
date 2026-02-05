from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

workspace_path: Path = Path.home() / "NagiFlow"
web_path: Path = workspace_path / "web"
env_file_path: Path = workspace_path / ".env"
db_path: Path = workspace_path / "db.sqlite"


class NagiFlowSettings(BaseSettings):
    AI_MODEL: str = "gpt-oss:20b"
    TAVILY_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=env_file_path)


settings = NagiFlowSettings()
