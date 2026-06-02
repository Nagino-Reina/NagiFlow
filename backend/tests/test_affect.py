"""Unit tests for the emotion & affect engine (docs/10, docs/15 §6)."""

from __future__ import annotations

from nagiflow.services.affect import (
    VAD,
    EMOTION_CENTROIDS,
    _parse_vad,
    build_directive,
    discretize,
    dynamics_for,
    expression_for,
    lexicon_appraise,
    step,
    voice_style_for,
)

_CALM = {
    "openness": 50,
    "conscientiousness": 70,
    "extraversion": 40,
    "agreeableness": 60,
    "neuroticism": 10,
}
_VOLATILE = {
    "openness": 50,
    "conscientiousness": 40,
    "extraversion": 60,
    "agreeableness": 80,
    "neuroticism": 90,
}


def test_dynamics_reactivity_tracks_neuroticism():
    calm = dynamics_for(_CALM)
    volatile = dynamics_for(_VOLATILE)
    assert volatile.reactivity > calm.reactivity
    # high agreeableness/extraversion → warmer resting valence
    assert volatile.baseline.v > 0


def test_dynamics_bounds():
    dyn = dynamics_for(_VOLATILE)
    assert 0.25 <= dyn.reactivity <= 0.9
    assert 0.05 <= dyn.drift <= 0.3
    assert 0.2 <= dyn.decay <= 0.7


def test_lexicon_valence_sign():
    assert lexicon_appraise("this is great, I love it, thanks!").v > 0
    assert lexicon_appraise("this is terrible and awful, I hate it").v < 0
    assert lexicon_appraise("the meeting is at noon").v == 0.0


def test_lexicon_clamped():
    vad = lexicon_appraise("AWFUL TERRIBLE HORRIBLE!!!")
    assert -1.0 <= vad.v <= 1.0
    assert 0.0 <= vad.a <= 1.0


def test_discretize_neutral_near_origin():
    label, intensity = discretize(VAD(0.02, -0.01, 0.0))
    assert label == "neutral"
    assert intensity < 0.1


def test_discretize_nearest_centroid():
    label, _ = discretize(EMOTION_CENTROIDS["joy"])
    assert label == "joy"
    label, _ = discretize(EMOTION_CENTROIDS["sadness"])
    assert label == "sadness"


def test_step_reacts_and_clamps():
    dyn = dynamics_for(_VOLATILE)
    emotion, mood = step(VAD(), VAD(), VAD(-0.6, 0.6, 0.2), dyn)
    # volatile character swings toward the negative stimulus
    assert emotion.v < 0
    for c in (emotion.v, emotion.a, emotion.d, mood.v, mood.a, mood.d):
        assert -1.0 <= c <= 1.0


def test_step_calm_swings_less_than_volatile():
    stim = VAD(-0.6, 0.6, 0.2)
    calm_emotion, _ = step(VAD(), VAD(), stim, dynamics_for(_CALM))
    volatile_emotion, _ = step(VAD(), VAD(), stim, dynamics_for(_VOLATILE))
    assert abs(volatile_emotion.v) > abs(calm_emotion.v)


def test_build_directive_empty_when_neutral():
    assert build_directive("neutral", 0.0, VAD()) == ""
    assert "anger" in build_directive("anger", 0.5, VAD(-0.5, 0.5, 0.2))


def test_voice_and_expression_maps():
    tags, rate = voice_style_for("joy", EMOTION_CENTROIDS["joy"])
    assert tags == ["cheerful"] and rate > 0
    assert expression_for("anger") == "angry"
    assert expression_for("affection") == "happy"
    assert expression_for("unknown") == "neutral"


def test_parse_vad():
    vad = _parse_vad('noise {"valence": 0.5, "arousal": -0.2, "dominance": 0.1} tail')
    assert vad is not None and vad.v == 0.5 and vad.a == -0.2
    assert _parse_vad("no json here") is None
    assert _parse_vad('{"valence": 2.0, "arousal": 0.0, "dominance": 0.0}').v == 1.0
