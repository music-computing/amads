"""
Tests for amads/time/onsetacorr.py
"""

import pytest

from amads.time.onsetacorr import *
from amads.io.readscore import read_score

def test_autocorr_sarabande():
    path = "/Users/anirudhs/amads/amads/music/midi/sarabande.mid"
    score = read_score(path)

    ac = onset_autocorr(score)

    expected = [ # output from miditoolbox
        1.000000,
        0.098494,
        0.679315,
        0.098057,
        0.760174,
        0.094977,
        0.689658,
        0.109276,
        0.752261,
        0.117179,
        0.680487,
        0.107911,
        0.722491,
        0.112678,
        0.676251,
        0.119348,
        0.716569,
        0.116744,
        0.663522,
        0.110114,
        0.732236,
        0.117638,
        0.661307,
        0.115416,
        0.807259,
        0.113926,
        0.649550,
        0.116682,
        0.690843,
        0.117153,
        0.661045,
        0.120281,
        0.704703
    ]

    assert ac == pytest.approx(expected, abs=1e-6)