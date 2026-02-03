import uuid

from fastapi import APIRouter
from pydantic import BaseModel

import db

router = APIRouter(tags=["Character"])


@router.get("/characters")
def get_characters():
    chars = db.get_characters()
    return chars


class CreateCharacterData(BaseModel):
    name: str
    identity: str


@router.post("/characters")
def create_character(request_data: CreateCharacterData):
    new_char = db.create_character(name=request_data.name, identity=request_data.identity)
    return new_char


@router.get("/characters/{char_id}")
def get_character(char_id: uuid.UUID):
    char = db.get_character(char_id)
    return char
