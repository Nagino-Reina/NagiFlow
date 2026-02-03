import uuid
from datetime import datetime
from typing import List

from sqlmodel import SQLModel, Field, Relationship


class Character(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    name: str = Field(unique=True)
    identity: str

    threads: List["Thread"] = Relationship(
        back_populates="char",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Thread(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    char_id: uuid.UUID = Field(foreign_key="character.id", nullable=False)
    char: Character = Relationship(back_populates="threads")
