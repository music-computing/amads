"""
Tests for break_it_up module.

Tests functionality for regrouping and quantizing musical durations.
"""

import pytest

from amads.time.meter.break_it_up import (
    ReGrouper,
    start_hierarchy_examples,
    start_hierarchy_from_ts,
    start_list_from_pulse_lengths,
    starts_from_ts_and_levels,
)


@pytest.fixture
def test_metres():
    metres = []
    for x in (
        (
            "4/4",
            [1, 2],
            [4, 2, 1],
            [[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]],
        ),
        (
            "4/4",
            [3],
            [4, 0.5],
            [[0.0, 4.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]],
        ),
        (
            "6/8",
            [1, 2],
            [3, 1.5, 0.5],
            [[0.0, 3.0], [0.0, 1.5, 3.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]],
        ),
    ):
        new_dict = {"ts": x[0], "levels": x[1], "pulses": x[2], "starts": x[3]}
        metres.append(new_dict)
    return metres


def test_get_starts_from_ts_and_levels(test_metres):
    for tc in test_metres:
        t = starts_from_ts_and_levels(tc["ts"], tc["levels"])
        assert t == tc["starts"]


def test_pulse_lengths_to_start_list(test_metres):
    for tc in test_metres:
        t = start_list_from_pulse_lengths(
            pulse_lengths=tc["pulses"], require_2_or_3_between_levels=False
        )
        assert t == tc["starts"]


def test_require_2_or_3():
    """Test a case with `require_2_or_3_between_levels` = True."""
    with pytest.raises(ValueError):
        start_list_from_pulse_lengths(
            pulse_lengths=[4, 1], require_2_or_3_between_levels=True
        )


def test_start_hierarchy_from_ts():
    """Test start_hierarchy_from_ts by running through test cases."""
    for k in start_hierarchy_examples:
        oh = start_hierarchy_from_ts(k, minimum_pulse=32)
        assert oh == start_hierarchy_examples[k]


def test_from_pulse_length():
    """
    Test cases from pulse lengths for metrical structures.

    Tests practically plausible metrical structures built up in proportions of 2 or 3.
    Reproduced from Gotham 2015a: Attractor Tempos for Metrical Structures,
    Journal of Mathematics and Music.

    For convenience this test takes the unit pulse as a quarter and builds everything
    up from there, choosing examples like 16/4 rather than 4/4 with divisions.
    Although not reflective of common time signatures, the metrical structures are
    equivalent making this a valid test of rare signatures like 16/4.
    """
    all_plausible = [
        [7, 6, [1, 2, 4, 8, 16, 32], [(7, 1), (8, 5)]],
        [15, 1, [1, 2, 4, 8, 16], [(15, 1)]],
        [4, 4, [1, 2, 4, 8], [(4, 4)]],
        [1, 3, [1, 2, 4], [(1, 1), (2, 2)], 4],
        [1, 1, [1, 2], [(1, 1)], 2],
        [0, 1, [1], [(0, 1)], 77],
        [8, 3, [1, 2, 4, 8, 16, 48], [(8, 3)]],
        [6, 4, [1, 2, 4, 8, 24, 48], [(6, 2), (8, 2)]],
        [13, 6, [1, 2, 4, 8, 24], [(13, 1), (14, 2), (16, 3)]],
        [6, 4, [1, 2, 4, 12, 24, 48], [(6, 2), (8, 2)]],
        [16, 7, [1, 2, 4, 12, 24], [(16, 7)]],
        [7, 4, [1, 2, 4, 12], [(7, 1), (8, 3)]],
        [15, 12, [1, 2, 6, 12, 24, 48], [(15, 1), (16, 2), (18, 6), (24, 3)]],
        [6, 15, [1, 2, 6, 12, 24], [(6, 6), (12, 9)]],
        [7, 5, [1, 2, 6, 12], [(7, 1), (8, 4)]],
        [3, 2, [1, 2, 6], [(3, 1), (4, 1)]],
        [6, 40, [1, 3, 6, 12, 24, 48], [(6, 6), (12, 12), (24, 22)]],
        [13, 4, [1, 3, 6, 12, 24], [(13, 2), (15, 2)]],
        [8, 4, [1, 3, 6, 12], [(8, 1), (9, 3)]],
        [2, 4, [1, 3, 6], [(2, 1), (3, 3)]],
        [2, 1, [1, 3], [(2, 1)]],
        [20, 9, [1, 2, 4, 12, 36], [(20, 4), (24, 5)]],
        [16, 7, [1, 2, 6, 12, 36], [(16, 2), (18, 5)]],
        [16, 7, [1, 3, 6, 12, 36], [(16, 2), (18, 5)]],
        [4, 12, [1, 2, 6, 18, 36], [(4, 2), (6, 10)]],
        [13, 3, [1, 3, 6, 18, 36], [(13, 2), (15, 1)]],
        [4, 12, [1, 3, 9, 18, 36], [(4, 2), (6, 3), (9, 7)]],
        [14, 25, [1, 2, 6, 18, 54], [(14, 4), (18, 21)]],
        [8, 16, [1, 3, 6, 18, 54], [(8, 1), (9, 3), (12, 6), (18, 6)]],
        [8, 15, [1, 3, 9, 18, 54], [(8, 1), (9, 9), (18, 5)]],
        [12, 30, [1, 3, 9, 27, 54], [(12, 6), (18, 9), (27, 15)]],
        [4, 9, [1, 3, 9, 27], [(4, 2), (6, 3), (9, 4)]],
    ]

    for entry in all_plausible:
        g = ReGrouper(entry[0], entry[1], pulse_lengths=entry[2])
        assert g.start_duration_pairs == entry[3]


def test_split_same_level():
    """Test the split_same_level parameter with cases in 6/8."""
    eg1 = ReGrouper(0.5, 1, time_signature="6/8", split_same_level=False)
    assert eg1.start_duration_pairs == [(0.5, 1)]
    eg2 = ReGrouper(0.5, 1, time_signature="6/8", split_same_level=True)
    assert eg2.start_duration_pairs == [(0.5, 0.5), (1, 0.5)]

    eg1 = ReGrouper(0.5, 2, time_signature="6/8", split_same_level=False)
    assert eg1.start_duration_pairs == [(0.5, 1), (1.5, 1)]
    eg2 = ReGrouper(0.5, 2, time_signature="6/8", split_same_level=True)
    assert eg2.start_duration_pairs == [(0.5, 0.5), (1, 0.5), (1.5, 1)]
