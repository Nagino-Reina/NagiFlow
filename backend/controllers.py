import uuid

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.sqlite import SqliteStore

from config import settings
from db import get_character, engine
from tools import default_tools

store = SqliteStore(engine.raw_connection())
checkpointer = SqliteSaver(engine.raw_connection())
model = ChatOllama(model=settings.AI_MODEL)


def make_backend(runtime):
    return CompositeBackend(
        default=StateBackend(runtime),  # Ephemeral storage
        routes={
            "/memories/": StoreBackend(runtime)  # Persistent storage
        }
    )


def load_char_agent(char_id: uuid.UUID):
    character = get_character(char_id)
    agent = create_deep_agent(
        model=model,
        store=store,
        backend=make_backend,
        checkpointer=checkpointer,
        tools=default_tools,
        system_prompt=character.identity
    )
    return agent
