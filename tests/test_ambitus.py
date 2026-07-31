from amads.core.basics import Score
from amads.melody.ambitus import ambitus


def test_empty():
    score = Score()
    assert ambitus(score) is None


def test_single_note_score():
    pitches = [60]
    score = Score.from_melody(pitches=pitches)
    desired_ambitus = 0
    assert ambitus(score) == desired_ambitus


def test_double_note_score():
    pitches = [60, 72]
    score = Score.from_melody(pitches=pitches)
    desired_ambitus = 72 - 60
    assert ambitus(score) == desired_ambitus


def test_toy_score():
    pitches = [60, 72, 10, 99]
    score = Score.from_melody(pitches=pitches)
    desired_ambitus = 99 - 10
    assert ambitus(score) == desired_ambitus
