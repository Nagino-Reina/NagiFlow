import uuid

from sqlmodel import create_engine, Session, select

from config import db_path
from models import Character, Thread

engine = create_engine(f"sqlite:///{db_path}")


def get_characters():
    statement = select(Character)
    with Session(engine) as session:
        characters = session.exec(statement).all()
    return characters


def create_character(name: str, identity: str):
    new_char = Character(name=name, identity=identity)
    with Session(engine) as session:
        session.add(new_char)
        session.commit()
        session.refresh(new_char)
    return new_char


def get_character(char_id: uuid.UUID):
    statement = select(Character).where(Character.id == char_id)
    with Session(engine) as session:
        character = session.exec(statement).first()
    return character


def get_threads():
    statement = select(Thread)
    with Session(engine) as session:
        threads = session.exec(statement).all()
    return threads


def create_thread(char_id: uuid.UUID):
    new_thread = Thread(char_id=char_id)
    with Session(engine) as session:
        session.add(new_thread)
        session.commit()
        session.refresh(new_thread)
    return new_thread


def get_thread(thread_id: uuid.UUID):
    statement = select(Thread).where(Thread.id == thread_id)
    with Session(engine) as session:
        thread = session.exec(statement).first()
    return thread
