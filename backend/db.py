from sqlmodel import create_engine, Session, select

from config import db_path
from models import Character

engine = create_engine(f"sqlite:///{db_path}")

def get_characters():
    with Session(engine) as session:
        statement = select(Character)
        characters = session.exec(statement).all()
    return characters


def get_character(char_id: str):
    with Session(engine) as session:
        statement = select(Character).where(Character.id == char_id)
        character = session.exec(statement).first()
    return character