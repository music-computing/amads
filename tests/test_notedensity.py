"""Test suite for functions in amads.time.notedensity"""

import pytest

from amads.core.basics import Note, Part, Score
from amads.core.timemap import TimeMap
from amads.time.notedensity import notedensity


def test_notedensity_empty_notes():
    """Empty score should return 0.0"""
    score = Score.from_melody([])
    result = notedensity(score, timetype="quarters")
    assert result == 0.0


def test_notedensity_seconds_score_seconds_timetype():
    """timetype is seconds, score.units_are_seconds = True"""
    # Create a score in seconds
    score = Score()
    score.convert_to_seconds()
    part = Part(parent=score)
    Note(parent=part, onset=0.0, duration=0.5, pitch=60)
    Note(parent=part, onset=0.5, duration=0.5, pitch=62)
    Note(parent=part, onset=1.0, duration=0.5, pitch=64)

    result = notedensity(score, timetype="seconds")
    # (3-1) / 1.0 = 2.0
    assert result == 2.0


def test_notedensity_quarters_score_seconds_timetype():
    """timetype is quarters, score.units_are_seconds = True"""
    # Create a score in seconds with time_map
    score = Score()
    score.convert_to_seconds()
    score.time_map = TimeMap(bpm=120)
    part = Part(parent=score)
    Note(parent=part, onset=0.0, duration=0.5, pitch=60)
    Note(parent=part, onset=0.5, duration=0.5, pitch=62)
    Note(parent=part, onset=1.0, duration=0.5, pitch=64)

    result = notedensity(score, timetype="quarters")
    # 0.0s = 0.0q, 1.0s = 2.0q (at 120 BPM)
    # duration = 2.0 - 0.0 = 2.0 quarters
    # density = (3-1) / 2.0 = 1.0
    assert result == 1.0


def test_notedensity_invalid_timetype():
    """Invalid timetype"""
    score = Score.from_melody([60, 62, 64])
    with pytest.raises(ValueError) as exc_info:
        notedensity(score, timetype="invalid")
    assert "Invalid timetype: invalid. Use 'quarters' or 'seconds'." in str(
        exc_info.value
    )


def test_notedensity_duration_zero():
    """duration is zero"""
    score = Score()
    part = Part(parent=score)
    Note(parent=part, onset=0.0, duration=1.0, pitch=60)
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)
    Note(parent=part, onset=0.0, duration=1.0, pitch=64)

    result = notedensity(score, timetype="quarters")
    assert result == 0.0


def test_notedensity_default_timetype():
    """make sure that the default timetype is quarters"""
    score = Score.from_melody([60, 62, 64, 65])
    result = notedensity(score)  # default timetype='quarters'
    assert result == 1.0
