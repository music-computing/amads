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


def test_zero_pitch_variance_melodies():
    melody = Score.from_melody([])
    with pytest.raises(RuntimeError):
        kkcc(melody)

    pitches_in = list(range(56, 68))
    melody = Score.from_melody(pitches=pitches_in)
    with pytest.raises(RuntimeError):
        kkcc(melody)


def test_crafted_nonempty_melody():
    """
    This is a sanity check nonempty crafted melody (so far)...
    I probably need some help with these tests...
    """
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
        math.isclose(coef, desired_coef, rel_tol=1e-13)
        for coef, desired_coef in zip(coefs, desired_coefs)
    )

    return


def test_salience():
    pitches_in = list(range(56, 68)) + list(range(56, 68, 2))
    melody = Score.from_melody(pitches=pitches_in)
    coefs = kkcc(melody, salience_flag=True)
    # salience coefficients were slightly off...
    desired_coefs = (
        0.06795243480111307,
        -0.06795243480111297,
        0.06795243480111299,
        -0.06795243480111306,
        0.06795243480111308,
        -0.0679524348011131,
        0.06795243480111313,
        -0.06795243480111308,
        0.06795243480111315,
        -0.06795243480111325,
        0.06795243480111311,
        -0.06795243480111306,
        0.007936807483931043,
        -0.007936807483930925,
        0.00793680748393091,
        -0.007936807483930879,
        0.007936807483930955,
        -0.007936807483930877,
        0.00793680748393086,
        -0.007936807483930962,
        0.007936807483931012,
        -0.00793680748393106,
        0.007936807483931023,
        -0.007936807483930984,
    )

    assert all(
        math.isclose(coef, desired_coef, rel_tol=1e-13)
        for coef, desired_coef in zip(coefs, desired_coefs)
    )

    return
