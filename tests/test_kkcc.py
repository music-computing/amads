"""
Please note that all these tests assume that key_cc works as advertised
Also note that this test file is by no means exhaustive...
"""

import math

import pytest

from amads.core.basics import Score
from amads.pitch.kkcc import kkcc


def test_error_handling():
    dummy_score = Score.from_melody([])
    with pytest.raises(ValueError):
        kkcc(dummy_score, None)
    with pytest.raises(ValueError):
        kkcc(dummy_score, "invalid string")
    with pytest.raises(ValueError):
        kkcc(None)

    return


def test_empty_melody():
    melody = Score.from_melody([])
    with pytest.raises(RuntimeError):
        kkcc(melody)
    return


def test_equal_prob_melody():
    """
    Equal prob melody containing 1 of each pitch.
    Without salience this should return 24 NANs since variance is 0
    """
    pitches_in = list(range(56, 68))
    melody = Score.from_melody(pitches=pitches_in)
    with pytest.raises(RuntimeError):
        kkcc(melody)
    return


def test_crafted_nonempty_melody():
    """
    This is a sanity check nonempty crafted melody (so far)...
    I probably need some help with these tests...
    """
    print("Warning! Test not implemented!")
    pitches_in = list(range(56, 68)) + list(range(56, 68, 2))
    melody = Score.from_melody(pitches=pitches_in)
    coefs = kkcc(melody)
    desired_coefs = (
        0.06795243480111307,
        -0.06795243480111302,
        0.06795243480111307,
        -0.0679524348011131,
        0.06795243480111304,
        -0.06795243480111308,
        0.06795243480111303,
        -0.0679524348011131,
        0.0679524348011131,
        -0.06795243480111308,
        0.06795243480111306,
        -0.06795243480111304,
        0.007936807483930946,
        -0.007936807483930976,
        0.007936807483930953,
        -0.007936807483930882,
        0.007936807483930934,
        -0.007936807483930976,
        0.007936807483930953,
        -0.007936807483930969,
        0.00793680748393098,
        -0.00793680748393103,
        0.007936807483930997,
        -0.007936807483930969,
    )
    assert all(
        math.isclose(coef, desired_coef, rel_tol=1e-15)
        for coef, desired_coef in zip(coefs, desired_coefs)
    )

    return
