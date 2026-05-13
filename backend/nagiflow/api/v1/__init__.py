"""Aggregate all v1 routers into a single APIRouter."""

from fastapi import APIRouter

from nagiflow.api.v1 import auth, audio, characters, conversations, health, knowledge, memory, skills, streaming

def users_router():
    from nagiflow.api.v1 import users
    return users.router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users_router())
api_router.include_router(characters.router)
api_router.include_router(conversations.router)
api_router.include_router(memory.router)
api_router.include_router(knowledge.router)
api_router.include_router(skills.router)
api_router.include_router(audio.router)
api_router.include_router(streaming.router)
