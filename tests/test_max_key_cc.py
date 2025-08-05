"""
Please note that all these tests assume that key_cc works as advertised
"""

import math

import pytest

from amads.core.basics import Score
from amads.pitch.max_key_cc import max_key_cc

"""
We are not testing error handling here because max_key_cc
inherits the error handling of key_cc
"""


def test_empty_melody():
    melody = Score.from_melody([])
    with pytest.raises(RuntimeError):
        max_key_cc(melody)
    return


def test_equal_prob_melody():
    """
    Equal prob melody containing 1 of each pitch.
    result should be NAN
    """
    pitches_in = list(range(56, 68))
    durations_in = [0.5] * len(pitches_in)
    melody = Score.from_melody(pitches=pitches_in, durations=durations_in)
    with pytest.raises(RuntimeError):
        max_key_cc(melody)
    return


def test_crafted_nonempty_melody():
    """
    This is a sanity check nonempty crafted melody (so far)...
    I probably need some help with these tests...
    """
    pitches_in = list(range(56, 68)) + list(range(56, 68, 2))
    durations_in = [0.5] * len(pitches_in)
    melody = Score.from_melody(pitches=pitches_in, durations=durations_in)
    max_coef = max_key_cc(melody)
    target_coef = 0.0679524348011131
    assert math.isclose(max_coef, target_coef, rel_tol=1e-15)

    return
