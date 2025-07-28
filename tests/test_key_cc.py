import pytest

from amads.core.basics import Note, Part, Score
from amads.pitch.key_cc import key_cc


def test_error_handling():
    print("Warning! Test not implemented!")
    return


def test_empty_melody():
    print("Warning! Test not implemented!")
    return


def test_equal_prob_melody():
    """
    Equal prob melody containing 1 of each pitch.
    Without salience this should return all 24 coefficients as equivalent
    for all 3 profiles of kkcc
    """
    print("Warning! Test not implemented!")
    return


def test_crafted_nonempty_melodies():
    """
    These melodies are here to test the various codepaths and are specific
    to the implementation itself...
    """
    print("Warning! Test not implemented!")
    return


def test_random_generated_melodies():
    """
    These are randomly generated (but deterministic due to fixed seed) melodies
    Are we sure we have a reference implementation or a decent set of
    verification properties to test against to pull this one off?
    """
    print("Warning! Test not implemented!")
    test_iterations = 100
    return
