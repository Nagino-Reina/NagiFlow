from config import workspace_path, env_file_path
from sqlmodel import SQLModel, Session
from db import engine
from models import Character

workspace_path.mkdir(exist_ok=True)
env_file_path.touch()
SQLModel.metadata.create_all(engine)

nagino = Character(
    id="nagino",
    name="nagino",
    identity="""You are an AI Hacker Vtuber.""")

with Session(engine) as session:
    session.add(nagino)
    session.commit()