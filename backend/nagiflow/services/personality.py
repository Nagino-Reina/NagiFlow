"""Big Five → behavior mapping (docs/08 §3.2).

Transparent, editable transform: each trait maps to (a) prompt directives appended to the
persona and (b) bounded parameter offsets (here, temperature). Mid-range (~40–60) is neutral.
"""

from __future__ import annotations

_HIGH = 60
_LOW = 40

_DIRECTIVES = {
    "openness": (
        "Offer imaginative tangents and novel framings; reference varied topics.",
        "Stay concrete and conventional; avoid abstract tangents.",
    ),
    "conscientiousness": (
        "Be precise and structured; follow through; avoid careless claims.",
        "Be spontaneous and loose; don't over-structure.",
    ),
    "extraversion": (
        "Be talkative and upbeat; initiate and react with enthusiasm.",
        "Keep replies short and measured; don't volunteer extra.",
    ),
    "agreeableness": (
        "Be warm, validating, and cooperative; soften disagreement.",
        "Be blunt and challenging; don't over-accommodate.",
    ),
    "neuroticism": (
        "Show emotional reactivity; express worry or excitement vividly.",
        "Stay calm and even-keeled.",
    ),
}


def directives_for(big_five: dict[str, int]) -> list[str]:
    out: list[str] = []
    for trait, (high, low) in _DIRECTIVES.items():
        value = int(big_five.get(trait, 50))
        if value >= _HIGH:
            out.append(high)
        elif value <= _LOW:
            out.append(low)
    return out


def temperature_for(big_five: dict[str, int], base: float = 0.7) -> float:
    """Openness↑ raises temperature; Conscientiousness↑ lowers it. Clamped to [0.2, 1.2]."""
    o = (int(big_five.get("openness", 50)) - 50) / 50.0
    c = (int(big_five.get("conscientiousness", 50)) - 50) / 50.0
    temp = base + 0.2 * o - 0.2 * c
    return max(0.2, min(1.2, round(temp, 3)))


def build_system_prompt(persona: str, big_five: dict[str, int]) -> str:
    parts: list[str] = []
    if persona.strip():
        parts.append(persona.strip())
    directives = directives_for(big_five)
    if directives:
        parts.append("Behavioral directives:\n- " + "\n- ".join(directives))
    return "\n\n".join(parts) if parts else "You are a helpful AI character."
