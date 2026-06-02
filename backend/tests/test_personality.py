"""Unit tests for the Big Five → behavior mapping (docs/08 §3.2, docs/14 §6)."""

from __future__ import annotations

import pytest

from nagiflow.services import personality as p


def _profile(**overrides: int) -> dict[str, int]:
    base = {t: 50 for t in p.TRAITS}
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("score", "band"),
    [
        (0, "very_low"), (19, "very_low"),
        (20, "low"), (39, "low"),
        (40, "moderate"), (59, "moderate"),
        (60, "high"), (79, "high"),
        (80, "very_high"), (100, "very_high"),
    ],
)
def test_band_thresholds(score: int, band: str) -> None:
    assert p.band_of(score) == band


def test_resolve_has_all_five_traits_with_matching_directives() -> None:
    mapping = p.resolve(_profile(openness=82, extraversion=70, neuroticism=28))
    assert [e.trait for e in mapping.traits] == list(p.TRAITS)
    for e in mapping.traits:
        assert e.band == p.band_of(e.score)
        assert e.directive  # non-empty, picked from the band table


def test_out_of_range_scores_are_clamped() -> None:
    mapping = p.resolve(_profile(openness=999, conscientiousness=-50))
    by = {e.trait: e for e in mapping.traits}
    assert by["openness"].score == 100
    assert by["conscientiousness"].score == 0


def test_temperature_is_monotonic_in_openness_and_clamped() -> None:
    temps = [p.temperature_for(_profile(openness=s)) for s in (0, 25, 50, 75, 100)]
    assert temps == sorted(temps)
    assert all(0.2 <= t <= 1.2 for t in temps)


def test_speech_rate_and_verbosity_track_extraversion() -> None:
    low = p.resolve(_profile(extraversion=5))
    high = p.resolve(_profile(extraversion=95))
    assert low.speech_rate < high.speech_rate
    assert low.verbosity == "minimal"
    assert high.verbosity == "expansive"
    assert 0.85 <= low.speech_rate <= 1.15
    assert 0.85 <= high.speech_rate <= 1.15


def test_voice_style_tags_emit_at_extremes_only() -> None:
    assert p.resolve(_profile()).voice_style == []  # neutral profile → no tags
    energetic = p.resolve(_profile(extraversion=90, agreeableness=90))
    assert "energetic" in energetic.voice_style
    assert "warm" in energetic.voice_style


def test_system_prompt_includes_roleplay_scores_bands_and_persona() -> None:
    prompt = p.build_system_prompt("Stay in character.", "A warm co-host.", _profile(openness=82))
    assert prompt.startswith("Stay in character.")
    assert "A warm co-host." in prompt
    assert "Openness 82/100 (very high)" in prompt
    assert "Big Five" in prompt


def test_spec_is_self_consistent() -> None:
    spec = p.spec()
    assert spec["bands"] == list(p.BANDS)
    assert spec["thresholds"] == list(p.THRESHOLDS)
    assert set(spec["directives"]) == set(p.TRAITS)
    for directives in spec["directives"].values():
        assert len(directives) == len(p.BANDS)
    # The served formula reproduces the server-side computation.
    cfg = spec["params"]["temperature"]
    profile = _profile(openness=80, conscientiousness=20)
    expected = round(
        max(cfg["min"], min(cfg["max"], cfg["base"]
            + cfg["coefficients"]["openness"] * (80 - 50) / 50
            + cfg["coefficients"]["conscientiousness"] * (20 - 50) / 50)),
        3,
    )
    assert expected == p.temperature_for(profile)
