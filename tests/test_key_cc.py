import numpy as np
import pytest

from amads.core.basics import Score
from amads.pitch.key import profiles as prof
from amads.pitch.key_cc import key_cc


def test_error_handling():
    """Invalid attribute name should return None"""
    score = Score.from_melody([60, 62, 64])
    result = key_cc(score, prof.krumhansl_kessler, ["invalid_attribute"])
    assert result == [("invalid_attribute", None)]


def test_empty_melody():
    score = Score.from_melody([])
    with pytest.raises(RuntimeError):
        key_cc(score, prof.krumhansl_kessler, ["major", "minor"])


def test_equal_prob_melody():
    """
    Equal prob melody containing 1 of each pitch.
    Without salience this should return all 24 coefficients as equivalent
    for all 3 profiles of kkcc
    """
    melody = list(range(60, 72))  # C4 to B4
    score = Score.from_melody(melody)
    for profile in [prof.krumhansl_kessler, prof.temperley, prof.albrecht_shanahan]:
        with pytest.raises(RuntimeError):
            key_cc(score, profile, ["major", "minor"])
    return


def test_crafted_nonempty_melodies():
    """
    These melodies are here to test the various codepaths and are specific
    to the implementation itself...
    """
    # C major scale
    score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])

    # transpositionally equivalent
    result = key_cc(score, prof.bellman_budge, ["major", "minor"])
    assert isinstance(result, list)
    assert len(result) == 2
    for (attr, corr), expected in zip(result, ["major", "minor"]):
        assert attr == expected
        assert corr is not None
        assert len(corr) == 12
        assert all(isinstance(x, float) for x in corr)  # floats expected

    # transpositionally unequivalent
    result2 = key_cc(score, prof.quinn_white, ["major_assym", "minor_assym"])
    assert isinstance(result2, list)
    assert len(result2) == 2
    for (attr, corr), expected in zip(result2, ["major_assym", "minor_assym"]):
        assert attr == expected
        assert corr is not None
        assert len(corr) == 12
        assert all(isinstance(x, float) for x in corr)  # floats expected


def test_random_generated_melodies():
    """
    These are randomly generated (but deterministic due to fixed seed) melodies
    Are we sure we have a reference implementation or a decent set of
    verification properties to test against to pull this one off?
    """
    np.random.seed(42)
    test_iterations = 10
    for _ in range(test_iterations):
        pitches = np.random.randint(60, 72, size=16)  # length 16, pitches from C4 to B4
        score = Score.from_melody(pitches.tolist())
        result = key_cc(score, prof.sapp, ["major", "minor"])
        assert isinstance(result, list)
        assert len(result) == 2
        for (attr, corr), expected in zip(result, ["major", "minor"]):
            assert attr == expected
            assert corr is not None
            assert len(corr) == 12
            assert all(isinstance(x, float) for x in corr)  # floats expected
