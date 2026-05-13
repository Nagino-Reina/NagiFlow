"""
Built-in web search skill.

Uses DuckDuckGo's instant answer API (no API key required) to return a brief
summary for a search query.  For production use, replace or extend with a
paid search API (Brave, Bing, SerpAPI, etc.) via plugin.
"""

from typing import Any

import httpx
from loguru import logger

from nagiflow.skills.base import BaseSkill, SkillMeta, SkillParameter
from nagiflow.skills.registry import skill_registry


@skill_registry.register
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
            SkillParameter(
                name="query",
                type="string",
                description="The search query",
                required=True,
            ),
            SkillParameter(
                name="max_results",
                type="integer",
                description="Maximum number of results to return (1-10)",
                required=False,
                default=3,
            ),
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
                logger.warning(f"WebSearchSkill: DuckDuckGo request failed: {exc}")
                return f"Search failed: {exc}"

        parts: list[str] = []

        # Abstract (instant answer)
        if data.get("Abstract"):
            parts.append(f"Summary: {data['Abstract']}")
            if data.get("AbstractURL"):
                parts.append(f"Source: {data['AbstractURL']}")

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                parts.append(f"- {topic['Text']}")

        if not parts:
            return f"No results found for: {query}"

        return "\n".join(parts)
