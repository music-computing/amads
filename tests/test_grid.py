"""
Basic tests of error raising in metrical grid module.
"""

__author__ = "Mark Gotham"

from collections import Counter

import pytest

from amads.time.meter import grid, profiles


def test_tatum_counter():
    with pytest.raises(ValueError):
        grid.get_tatum(starts=Counter({0: 4, 1.5: 2}))


def test_tatum_bins():
    # Not a list
    with pytest.raises(ValueError):
        grid.get_tatum(starts=[0, 1, 2, 3], pulse_priority_list=1)

    # List items not integers
    with pytest.raises(ValueError):
        grid.get_tatum(starts=[0, 1, 2, 3], pulse_priority_list=[1.6])

    # List items negative integer
    with pytest.raises(ValueError):
        grid.get_tatum(starts=[0, 1, 2, 3], pulse_priority_list=[-1])


def test_tatum_distance_threshold():
    with pytest.raises(ValueError):
        grid.get_tatum(starts=[0, 1, 2, 3], distance_threshold=-1)


def test_tatum_proportion_threshold():
    with pytest.raises(ValueError):
        grid.get_tatum(
            starts=[0, 1, 2, 3],
            proportion_threshold=3,
        )


def test_BPSD():
    """Tests all measure-relative values of the BPSD dataset"""
    all_files = [
        "op002No1_01",
        "op002No2_01",
        "op002No3_01",
        "op007_01",
        "op010No1_01",
        "op010No2_01",
        "op010No3_01",
        "op013_01",
        "op014No1_01",
        "op014No2_01",
        "op022_01",
        "op026_01",
        "op027No1_01",
        "op027No2_01",
        "op028_01",
        "op031No1_01",
        "op031No2_01",
        "op031No3_01",
        "op049No1_01",
        "op049No2_01",
        "op053_01",
        "op054_01",
        "op057_01",
        "op078_01",
        "op079_01",
        "op081a_01",
        "op090_01",
        "op101_01",
        "op106_01",
        "op109_01",
    ]
    all_positions = []

    bpsd = profiles.BPSD()
    for file_name in all_files:
        these_keys = getattr(bpsd, file_name).keys()
        all_positions += list(these_keys)
        for k in these_keys:
            n, d = grid.approximate_fraction(k)
            assert n < 200
            assert d < 600

    assert len(set(all_positions)) == len(set(bpsd.all.keys())) == 205
