"""
Please note that all these tests assume that key_cc works as advertised
Also note that this test file is by no means exhaustive...
"""

import pytest

from amads.core.basics import Score
from amads.pitch.key.kkcc import kkcc

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


def test_c_major_scale_peaks_at_c_major():
    melody = Score.from_melody(C_MAJOR_SCALE_UP_SI_DOWN)
    coefs = kkcc(melody)
    major_coefs = coefs[:12]
    minor_coefs = coefs[12:]
    assert (
        major_coefs.index(max(major_coefs)) == 0
    )  # best major key should be C (index 0)
    assert max(major_coefs) > max(minor_coefs)  # major should beat minor


def test_salience_for_c_diatonic_melody():
    melody = Score.from_melody(C_MAJOR_SCALE_UP_SI_DOWN)
    coefs_plain = kkcc(melody, salience_flag=False)
    major_plain = coefs_plain[:12]
    minor_plain = coefs_plain[12:]
    assert major_plain.index(max(major_plain)) == 0
    assert max(major_plain) > max(minor_plain)

    coefs_sal = kkcc(melody, salience_flag=True)
    major_sal = coefs_sal[:12]
    minor_sal = coefs_sal[12:]
    assert max(major_sal) > max(minor_sal)
