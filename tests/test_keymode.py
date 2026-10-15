"""
Please note that all these tests assume that key_cc works as advertised
"""

import pytest

from amads.core.basics import Score
from amads.pitch.key.keymode import keymode

# C major diatonic: ascend to high C, descend from B (no repeated high C at the turn).
C_MAJOR_SCALE_UP_SI_DOWN = [
    60,
    62,
    64,
    65,
    67,
    69,
    71,
    72,
    71,
    69,
    67,
    65,
    64,
    62,
    60,
]


def test_zero_pitch_variance_melodies():
    melody = Score.from_melody([])
    with pytest.raises(RuntimeError):
        keymode(melody)

    pitches_in = list(range(56, 68))
    melody = Score.from_melody(pitches=pitches_in)
    with pytest.raises(RuntimeError):
        keymode(melody)
    return


def test_c_major_scale_mode_major():
    """
    keymode assumes tonic C: it compares major vs minor using only the
    correlation at rotation 0 (C-rooted profiles). A C major scale should
    favor the major template.
    """
    melody = Score.from_melody(C_MAJOR_SCALE_UP_SI_DOWN)
    assert keymode(melody) == ["major"]

    return


def test_c_natural_minor_scale_mode_minor():
    """C natural minor collection should favor the minor profile at C."""
    melody = Score.from_melody([60, 62, 63, 65, 67, 68, 70, 72])
    assert keymode(melody) == ["minor"]

    return
