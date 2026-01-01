""" test_timemap.py -- tests for timemap class
"""

import pytest

from amads.core.timemap import TimeMap


def test_timemap_deepcopy():
    """Test that deepcopying a TimeMap works as expected."""
    import copy

    tm1 = TimeMap()
    tm1.append_quarter_tempo(0.0, 100)
    tm1.append_quarter_tempo(1.0, 120)
    tm1.append_quarter_tempo(2.0, 140)

    tm1.show()

    tm2 = copy.deepcopy(tm1)
    tm2.show()

    assert tm1 is not tm2
    for q1, q2 in zip(tm1.quarters, tm2.quarters):
        assert q1 is not q2
        assert q1.time == q2.time
        assert q1.quarter == q2.quarter


def test_timemap_mapping():
    """Test quarter_to_tempo method of TimeMap."""
    tm1 = TimeMap()
    tm1.append_quarter_tempo(0.0, 100)
    tm1.append_quarter_tempo(1.0, 120)
    tm1.append_quarter_tempo(2.0, 140)

    assert tm1.quarter_to_tempo(0) == pytest.approx(100)
    assert tm1.quarter_to_tempo(0.5) == pytest.approx(100)
    assert tm1.quarter_to_tempo(1) == pytest.approx(120)
    assert tm1.quarter_to_tempo(1.5) == pytest.approx(120)
    assert tm1.quarter_to_tempo(2) == pytest.approx(140)
    assert tm1.quarter_to_tempo(3) == pytest.approx(140)

    assert tm1.time_to_tempo(0) == pytest.approx(100)
    assert tm1.time_to_tempo(0.5 * 60 / 100) == pytest.approx(100)
    assert tm1.time_to_tempo(1 * 60 / 100) == pytest.approx(120)
    assert tm1.time_to_tempo(1 * 60 / 100 + 0.5 * 60 / 120) == pytest.approx(
        120
    )
    assert tm1.time_to_tempo(1 * 60 / 100 + 1 * 60 / 120) == pytest.approx(140)
    assert tm1.time_to_tempo(10) == pytest.approx(140)
