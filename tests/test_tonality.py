"""Tests for tonality."""

import pytest

from amads.core.basics import Score
from amads.pitch.key import profiles as prof
from amads.pitch.key.tonality import tonality


def test_tonality_empty_score():
    assert tonality(Score.from_melody([])) == []


def test_tonality_c_major_scale_length():
    melody = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    values = tonality(melody)
    assert len(values) == 8


def test_tonality_uses_kk_major_weights_for_c_major():
    melody = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    values = tonality(melody)
    expected = [
        prof.krumhansl_kessler.major.data[i] for i in (0, 2, 4, 5, 7, 9, 11, 0)
    ]
    assert values == pytest.approx(expected)


def test_tonality_c_minor_uses_minor_profile():
    melody = Score.from_melody([60, 62, 63, 65, 67, 68, 70, 72])
    values = tonality(melody)
    expected = [
        prof.krumhansl_kessler.minor.data[i] for i in (0, 2, 3, 5, 7, 8, 10, 0)
    ]
    assert values == pytest.approx(expected)


def test_tonality_alternate_profile():
    melody = Score.from_melody([60, 64, 67])
    values = tonality(melody, profile=prof.temperley)
    assert values[0] == prof.temperley.major.data[0]
