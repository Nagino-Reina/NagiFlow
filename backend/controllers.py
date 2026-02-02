from deepagents import create_deep_agent
from langchain_ollama import ChatOllama

from config import settings
from db import get_character
from tools import default_tools

model = ChatOllama(model=settings.AI_MODEL)

def load_character(char_id: str, tools=default_tools):
    character = get_character(char_id)
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=character.identity
    )
    return agent