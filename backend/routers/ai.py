from fastapi import APIRouter
from pydantic import BaseModel

from controllers import load_character

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatData(BaseModel):
    content: str


@router.post("/chat")
def chat(request_data: ChatData, char_id: str = 'nagino'):
    agent = load_character(char_id)
    result = agent.invoke({"messages": [
        {"role": "user", "content": request_data.content}
    ]})
    result_message: ChatData = result["messages"][-1]
    return result_message
