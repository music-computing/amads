"""Tests for tonality."""

import warnings

import pytest

from amads.core.basics import Score
from amads.pitch.key import profiles as prof
from amads.pitch.key.tonality import (
    _mode_from_keymode_result,
    _stability_for_note,
    _weights_c_tonic,
    tonality,
)


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


def test_mode_from_keymode_result_major_and_minor():
    """Test that the mode from a keymode result is major or minor."""
    assert _mode_from_keymode_result(["major"]) == "major"
    assert _mode_from_keymode_result(["minor"]) == "minor"


def test_mode_from_keymode_result_unspecified():
    """Test that the mode from a keymode result is unspecified."""
    assert _mode_from_keymode_result(["major", "minor"]) == "unspecified"
    assert _mode_from_keymode_result([]) == "unspecified"


def test_weights_c_tonic_unspecified_warns_and_uses_major():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        weights = _weights_c_tonic("unspecified")
    assert len(caught) == 1
    assert "Key mode not specified" in str(caught[0].message)
    assert weights == list(prof.krumhansl_kessler.major.data)


def test_tonality_undefined_pitch_raises():
    note = Score.from_melody([60]).get_sorted_notes()[0]
    note.pitch = None
    weights = list(prof.krumhansl_kessler.major.data)
    with pytest.raises(ValueError, match="defined pitch"):
        _stability_for_note(note, weights)
