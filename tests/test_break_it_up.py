"""
Tests for the `break_it_up` module.

Tests functionality for regrouping and quantizing musical durations.
"""

from amads.time.meter import PulseLengths
from amads.time.meter.break_it_up import MetricalSplitter


def test_from_pulse_length():
    """
    Test cases from pulse lengths for metrical structures.

    Tests practically plausible metrical structures built up in proportions of 2 or 3.
    Reproduced from Gotham 2015a: Attractor Tempos for Metrical Structures,
    Journal of Mathematics and Music.

    For convenience, this test takes the unit pulse as a quarter and builds everything
    up from there, choosing examples like 16/4 rather than 4/4 with divisions.
    Although not reflective of common time signatures, the metrical structures are
    equivalent, making this a valid test of rare signatures like 16/4.
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
        start_hierarchy = PulseLengths(pulse_lengths=entry[2]).to_start_hierarchy()
        g = MetricalSplitter(
            note_start=entry[0],
            note_length=entry[1],
            start_hierarchy=start_hierarchy,
            split_same_level=False,
        )
        assert g.start_duration_pairs == entry[3]


def test_split_same_level():
    """Test the split_same_level parameter with cases in 6/8."""
    start_hierarchy = PulseLengths(
        pulse_lengths=[3, 1.5, 0.5], cycle_length=3
    ).to_start_hierarchy()
    eg1 = MetricalSplitter(0.5, 1, start_hierarchy, split_same_level=False)
    assert eg1.start_duration_pairs == [(0.5, 1)]
    eg2 = MetricalSplitter(0.5, 1, start_hierarchy, split_same_level=True)
    assert eg2.start_duration_pairs == [(0.5, 0.5), (1, 0.5)]

    eg1 = MetricalSplitter(0.5, 2, start_hierarchy, split_same_level=False)
    assert eg1.start_duration_pairs == [(0.5, 1), (1.5, 1)]
    eg2 = MetricalSplitter(0.5, 2, start_hierarchy, split_same_level=True)
    assert eg2.start_duration_pairs == [(0.5, 0.5), (1, 0.5), (1.5, 1)]
