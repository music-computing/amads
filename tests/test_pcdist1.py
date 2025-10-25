"""
Test suite for pcdist1
"""

from amads.core.basics import Score
from amads.pitch.pcdist1 import pcdist1


def test_empty_melody():
    score = Score.from_melody([])
    val = pcdist1(score)
    test = [0] * 12
    assert val == test
