from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

workspace_path: Path = Path.home() / "NagiFlow"
env_file_path: Path = workspace_path / ".env"
db_path: Path = workspace_path / "db.sqlite"


class NagiFlowSettings(BaseSettings):
    AI_MODEL: str = ""
    TAVILY_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=env_file_path)


settings = NagiFlowSettings()
