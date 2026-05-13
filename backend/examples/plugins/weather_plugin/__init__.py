"""
Example NagiFlow plugin: Weather Skill.

Drop this directory into ``workspace/plugins/`` to activate.

This plugin registers a ``get_weather`` skill that characters can use
to answer questions about the current weather.
"""

from nagiflow.plugins.base import BasePlugin, PluginMeta
from nagiflow.skills.base import BaseSkill, SkillMeta, SkillParameter
from nagiflow.skills.registry import skill_registry


class WeatherSkill(BaseSkill):
    """Fetch current weather conditions for a given city."""

    meta = SkillMeta(
        name="get_weather",
        display_name="Get Weather",
        description=(
            "Get the current weather for a specified city. "
            "Use this when the user asks about weather conditions."
        ),
        parameters=[
            SkillParameter(
                name="city",
                type="string",
                description="City name (e.g. 'Tokyo', 'London')",
                required=True,
            ),
        ],
        is_builtin=False,
    )

    async def execute(self, city: str, **kwargs) -> str:
        import httpx

        api_key = self.config.get("api_key", "")
        if not api_key:
            return (
                f"Weather skill is not configured (missing API key). "
                f"Cannot retrieve weather for {city}."
            )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={"q": city, "appid": api_key, "units": "metric"},
                )
                resp.raise_for_status()
                data = resp.json()
                desc = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                feels = data["main"]["feels_like"]
                return (
                    f"Weather in {city}: {desc}, {temp:.1f}°C "
                    f"(feels like {feels:.1f}°C)."
                )
        except Exception as exc:
            return f"Could not fetch weather for {city}: {exc}"


class WeatherPlugin(BasePlugin):
    meta = PluginMeta(
        name="weather_plugin",
        version="1.0.0",
        author="Example Author",
        description="Adds a weather skill to NagiFlow characters.",
    )

    async def setup(self) -> None:
        skill_registry.register(WeatherSkill)
