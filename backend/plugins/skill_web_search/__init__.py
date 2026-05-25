"""Web search skill plugin."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from nagiflow.plugin.base import BasePlugin, BaseSkill, PluginMeta, SkillMeta, SkillParameter
from nagiflow.plugin.registry import registry


class WebSearchSkill(BaseSkill):
    """Search the web and return a brief summary of results."""

    meta = SkillMeta(
        name="web_search",
        display_name="Web Search",
        description=(
            "Search the web for current information. Use this when you need facts "
            "that might be outside your training data or require up-to-date information."
        ),
        parameters=[
            SkillParameter(name="query", type="string", description="The search query", required=True),
            SkillParameter(name="max_results", type="integer", description="Maximum results (1-10)", required=False, default=3),
        ],
        is_builtin=True,
    )

    _DDG_URL = "https://api.duckduckgo.com/"

    async def execute(self, query: str, max_results: int = 3, **kwargs: Any) -> str:
        max_results = max(1, min(10, max_results))
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    self._DDG_URL,
                    params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                logger.warning(f"WebSearchSkill: DuckDuckGo failed: {exc}")
                return f"Search failed: {exc}"

        parts: list[str] = []
        if data.get("Abstract"):
            parts.append(f"Summary: {data['Abstract']}")
            if data.get("AbstractURL"):
                parts.append(f"Source: {data['AbstractURL']}")
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                parts.append(f"- {topic['Text']}")
        return "\n".join(parts) if parts else f"No results found for: {query}"


class SkillWebSearchPlugin(BasePlugin):
    meta = PluginMeta(name="skill_web_search", version="1.0.0", description="DuckDuckGo web search skill.")

    async def setup(self) -> None:
        registry.register_skill(WebSearchSkill)
