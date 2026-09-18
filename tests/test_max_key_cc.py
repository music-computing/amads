"""
Please note that all these tests assume that key_cc works as advertised
"""

import pytest

from amads.core.basics import Score
from amads.pitch.key import profiles as prof
from amads.pitch.key.key_cc import key_cc
from amads.pitch.key.max_key_cc import max_key_cc

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
    """
    Testing the chromatic scale is deprecated because there are floating point
    discrepancies that may cause undefined behavior
    """
    melody = Score.from_melody([])
    with pytest.raises(RuntimeError):
        max_key_cc(melody)


def test_max_key_cc_matches_c_major_on_scale_up_down_melody():
    melody = Score.from_melody(C_MAJOR_SCALE_UP_SI_DOWN)
    pairs = key_cc(melody, prof.krumhansl_kessler, ["major", "minor"], False)
    major_coefs = dict(pairs)["major"]
    assert major_coefs is not None
    assert max_key_cc(melody) == pytest.approx(major_coefs[0])
