from sqlmodel import SQLModel

from config import workspace_path, env_file_path
from db import engine

# Workspace

workspace_path.mkdir(exist_ok=True)
env_file_path.touch()

# Database

SQLModel.metadata.create_all(engine)
