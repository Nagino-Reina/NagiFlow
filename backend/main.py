from fastapi import FastAPI

from routers import thread, character

app = FastAPI()

app.include_router(thread.router)
app.include_router(character.router)
