from typing import Literal

from tavily import TavilyClient

from config import settings

tavily_client = None
default_tools = []

def web_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic
    )

if (settings.TAVILY_API_KEY or "").strip():
    tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    default_tools.append(web_search)