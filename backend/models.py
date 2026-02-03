from sqlmodel import SQLModel, Field


class Character(SQLModel, table=True):
    id: str = Field(primary_key=True)
    identity: str
