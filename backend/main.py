from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel
from starlette.responses import FileResponse

from config import web_path
from db import engine
from routers import thread, character


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(thread.router, prefix="/api")
app.include_router(character.router, prefix="/api")

app.mount("/assets", StaticFiles(directory=web_path / "assets"))

@app.get("/{full_path:path}", tags=["static"])
async def handle_spa(full_path: str):
    return FileResponse(web_path / "index.html")

