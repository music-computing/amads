from amads.core.pitch import Pitch


def test_pitch_comparison():
    # B3 is lower than C4
    b_3 = Pitch(59, alt=0)
    c_4 = Pitch(60, alt=0)
    assert b_3 < c_4


def test_non_int_pitch():
    micro = Pitch(60.5)
    assert micro.num == 60.5
    assert micro.alt == 0.5


def test_meta_pitch():
    """Currently, Pitch accepts Pitch objects."""
    p = Pitch(60)
    Pitch(p)
