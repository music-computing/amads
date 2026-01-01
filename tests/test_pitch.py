import pytest

from amads.core.pitch import Pitch


def test_pitch_comparison():
    # B3 is lower than C4
    b_3 = Pitch(59, alt=0)
    c_4 = Pitch(60, alt=0)
    assert b_3 < c_4


def test_non_int_pitch():
    micro = Pitch(60.5)
    assert micro.key_num == 60.5
    assert micro.alt == 0.5


def test_meta_pitch():
    """Currently, Pitch accepts Pitch objects."""
    p = Pitch(60)
    Pitch(p)


def test_constructor():
    p = Pitch(60, alt=-1.4)  # since alt is invalid, spell key_num "C4"
    assert p.key_num == 60
    assert p.alt == 0
    assert p.name == "C"
    assert p.name_with_octave == "C4"
    # invalid integer alt, and pitch class is not diatonic
    p1 = Pitch(61, alt=0)
    assert p1.key_num == 61
    assert p1.alt == 1
    assert p1.name == "C#"
    assert p1.name_with_octave == "C#4"
    # favor Bb over A#
    p1 = Pitch(70, alt=1.4)  # invalid alt forces default
    assert p1.key_num == 70
    assert p1.alt == -1
    assert p1.name == "Bb"
    assert p1.name_with_octave == "Bb4"
    # negative microtone
    p2 = Pitch(59.5, alt=-0.5)
    assert p2.key_num == 59.5
    assert p2.alt == -0.5
    assert p2.name == "C?"
    assert p2.name_with_octave == "C?4"
    # Valid specification with negative microtone alteration
    p3 = Pitch(64.4, alt=-0.6)
    assert p3.key_num == 64.4
    assert p3.alt == pytest.approx(-0.6)
    assert p3.name == "F?"
    assert p3.name_with_octave == "F?4"
    # between E and F, invalid microtone alteration
    p4 = Pitch(64.7, alt=1.7)
    assert p4.key_num == 64.7
    assert p4.alt == pytest.approx(-0.3)
    assert p4.name == "F?"
    assert p4.name_with_octave == "F?4"
    # microtone alteration near F#
    p5 = Pitch(66.3, alt=0.8)  # invalid alt forces default
    assert p5.key_num == 66.3
    assert p5.alt == pytest.approx(-0.7)
    assert p5.name == "G?"
    assert p5.name_with_octave == "G?4"
    # None for pitch
    p6 = Pitch(None)
    assert p6.key_num is None
    assert p6.alt == 0
    assert p6.name == "unpitched"
    assert p6.name_with_octave == "unpitched"

    # test enharmonic
    p7 = Pitch("A5").enharmonic()
    assert p7.key_num == 81
    assert p7.alt == -2
    assert p7.name == "Bbb"
    assert p7.name_with_octave == "Bbb5"

    # test simplest_enharmonic
    p8 = Pitch("B##4").simplest_enharmonic(sharp_or_flat="sharp")
    assert p8.key_num == 73
    assert p8.alt == 1
    assert p8.name == "C#"
    assert p8.name_with_octave == "C#5"


def test_from_name():
    info = Pitch.from_name("C#4")
    assert info == (61, 1)
    info = Pitch.from_name("Db4")
    assert info == (61, -1)
    info = Pitch.from_name("")
    assert info == (60, 0)
    info = Pitch.from_name("", 4)
    assert info == (60, 0)
    info = Pitch.from_name("Gm", 3, "mp")
    assert info == (54, -1)
    info = Pitch.from_name("Ap3", 4, "mp")
    assert info == (58, 1)
