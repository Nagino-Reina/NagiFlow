from fastapi import FastAPI

from routers import ai, character

app = FastAPI()

app.include_router(ai.router)
app.include_router(character.router)
