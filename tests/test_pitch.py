from amads.core.basics import Pitch


def test_pitch_comparison():
    # B3 is lower than C4
    b_3 = Pitch(keynum=59, alt=0)
    c_4 = Pitch(keynum=60, alt=0)
    assert b_3 < c_4

    # B#3 is lower than C4
    b_sharp_3 = Pitch(keynum=60, alt=1)
    c_4 = Pitch(keynum=60, alt=0)
    assert b_sharp_3 < c_4

    # Dbb4 is higher than C4
    d_bb_4 = Pitch(keynum=60, alt=-2)
    c_4 = Pitch(keynum=60, alt=0)
    assert d_bb_4 > c_4
