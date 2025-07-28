"""
Please note that all these tests assume that key_cc works as advertised
"""

import pytest

from amads.core.basics import Score
from amads.pitch.kkcc import kkcc


def test_error_handling():
    dummy_score = Score.from_melody([])
    print("Warning! Test not implemented!")
    with pytest.raises(ValueError):
        kkcc(dummy_score, None)
    with pytest.raises(ValueError):
        kkcc(dummy_score, "invalid string")
    with pytest.raises(ValueError):
        kkcc(None)

    return


def test_empty_melody():
    print("Warning! Test not implemented!")
    return


def test_equal_prob_melody():
    """
    Equal prob melody containing 1 of each pitch.
    Without salience this should return all 24 coefficients
    as equivalent for all 3 profiles of kkcc
    """
    print("Warning! Test not implemented!")
    return


def test_crafted_nonempty_melodies():
    """
    These melodies are here to test the various codepaths
    and are specific to the implementation itself...
    """
    print("Warning! Test not implemented!")
    return


# ! this might not be a good idea...
def test_random_generated_melodies():
    print("Warning! Test not implemented!")
    test_iterations = 100
    return
