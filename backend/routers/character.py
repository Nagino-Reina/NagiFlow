from fastapi import APIRouter

import db

router = APIRouter(tags=["character"])


@router.get("/characters")
def get_characters():
    return db.get_characters()


@router.get("/characters/{char_id}")
def get_character(char_id: str):
    return db.get_character(char_id)
