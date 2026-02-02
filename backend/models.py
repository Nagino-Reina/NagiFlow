from sqlmodel import SQLModel, Field

class Character(SQLModel):
    id: str = Field(primary_key=True)
    name: str
    identity: str
