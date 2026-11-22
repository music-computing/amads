""" test_timemap.py -- tests for timemap class
"""

import pytest

from amads.core.timemap import TimeMap


def test_timemap_deepcopy():
    """Test that deepcopying a TimeMap works as expected."""
    import copy

    tm1 = TimeMap()
    tm1.append_change(0.0, 100)
    tm1.append_change(1.0, 120)
    tm1.append_change(2.0, 140)

    tm1.show()

    tm2 = copy.deepcopy(tm1)
    tm2.show()

    assert tm1 is not tm2
    for q1, q2 in zip(tm1.changes, tm2.changes):
        assert q1 is not q2
        assert q1.time == q2.time
        assert q1.quarter == q2.quarter


def test_timemap_mapping():
    """Test quarter_to_tempo method of TimeMap."""
    tm1 = TimeMap()
    tm1.append_change(0.0, 100)
    tm1.append_change(1.0, 120)
    tm1.append_change(2.0, 140)

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


def test_time_shift_forward():
    """Forward shift leaves (0, 0) and moves later breakpoints."""
    tm = TimeMap(qpm=120)
    tm.append_change(4.0, 60)

    tm._time_shift(1.0)

    assert len(tm.changes) == 2
    assert tm.changes[0].time == pytest.approx(0.0)
    assert tm.changes[0].quarter == pytest.approx(0.0)
    assert tm.changes[1].time == pytest.approx(2.5)  # 2.0 + 0.5s
    assert tm.changes[1].quarter == pytest.approx(5.0)


def test_time_shift_backward_existing_breakpoint():
    """Backward shift when a breakpoint already exists at the cut."""
    tm = TimeMap(qpm=120)
    tm.append_change(4.0, 60)
    tm.append_change(10.0, 120)
    tm.append_change(13.0, 90)

    tm._time_shift(-10.0)

    # Cut at quarter 10; later breakpoint at 13 is kept and shifted.
    assert len(tm.changes) == 2
    assert tm.changes[0].time == pytest.approx(0.0)
    assert tm.changes[0].quarter == pytest.approx(0.0)
    assert tm.changes[1].time == pytest.approx(1.5)  # 3 quarters at 120 qpm
    assert tm.changes[1].quarter == pytest.approx(3.0)
    assert tm.quarter_to_tempo(0.0) == pytest.approx(120)
    assert tm.quarter_to_tempo(3.0) == pytest.approx(90)


def test_time_shift_backward_insert_cut_breakpoint():
    """Backward shift inserts a cut breakpoint when none exists there."""
    tm = TimeMap(qpm=120)
    tm.append_change(4.0, 60)
    tm.append_change(10.0, 120)

    # Cut between breakpoints at 4 and 10; must insert at quarter 7.
    tm._time_shift(-7.0)

    assert tm.changes[0].time == pytest.approx(0.0)
    assert tm.changes[0].quarter == pytest.approx(0.0)
    # From cut (quarter 7) to former quarter 10 is 3 quarters at 60 qpm → 3s.
    assert len(tm.changes) == 2
    assert tm.changes[1].quarter == pytest.approx(3.0)
    assert tm.changes[1].time == pytest.approx(3.0)
    assert tm.quarter_to_tempo(0.0) == pytest.approx(60)
    assert tm.quarter_to_tempo(3.0) == pytest.approx(120)
