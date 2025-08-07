"""
Please note that all these tests assume that key_cc works as advertised
"""

import pytest

from amads.core.basics import Score
from amads.pitch.kkkey import kkkey

"""
We are not testing error handling here because kkkey
inherits the error handling of key_cc
"""


def test_zero_pitch_variance_melodies():
    melody = Score.from_melody([])
    with pytest.raises(RuntimeError):
        kkkey(melody)

    pitches_in = list(range(56, 68))
    melody = Score.from_melody(pitches=pitches_in)
    with pytest.raises(RuntimeError):
        kkkey(melody)
    return


def test_crafted_nonempty_melody():
    """
    This is a sanity check nonempty crafted melody (so far)...
    I probably need some help with these tests...
    """
    pitches_in = list(range(56, 68)) + list(range(56, 68, 2))
    melody = Score.from_melody(pitches=pitches_in)
    max_coef_pair = kkkey(melody)
    desired_result = ("major", 8)
    assert max_coef_pair == desired_result

    return
