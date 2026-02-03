import uuid

from fastapi import APIRouter
from pydantic import BaseModel

import db
from controllers import load_char_agent

router = APIRouter(tags=["Thread"])


@router.get("/threads")
def get_threads():
    threads = db.get_threads()
    return threads


class CreateThreadData(BaseModel):
    char_id: uuid.UUID


@router.post("/threads")
def create_thread(request_data: CreateThreadData):
    new_thread = db.create_thread(char_id=request_data.char_id)
    return new_thread


@router.get("/threads/{thread_id}")
def get_thread(thread_id: uuid.UUID):
    thread = db.get_thread(thread_id)
    return thread


class ChatData(BaseModel):
    message: str


@router.post("/threads/{thread_id}/chat")
def chat(thread_id: uuid.UUID, request_data: ChatData):
    thread = db.get_thread(thread_id)
    agent = load_char_agent(thread.char_id)
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [
        {"role": "user", "content": request_data.message}
    ]}, config=config)
    ai_message = result["messages"][-1].content
    return {"message": ai_message}
