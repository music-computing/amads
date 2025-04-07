"""Test suite for functions in amads.time.npvi"""

import pytest

from amads.time.npvi import normalized_pairwise_variability_index


def test_daniele_patel_2013_example_1():
    """Tests the first example given in the Appendix of Daniele & Patel (2013, p. 18)"""
    durations = [
        1.0,
        1 / 2,
        1 / 2,
        1.0,
        1 / 2,
        1 / 2,
        1 / 3,
        1 / 3,
        1 / 3,
        2.0,
        1 / 3,
        1 / 3,
        1 / 3,
        1 / 3,
        1 / 3,
        1 / 3,
        3 / 2,
        1.0,
        1 / 2,
    ]
    expected = 42.2
    actual = normalized_pairwise_variability_index(durations)
    assert round(actual, 1) == expected


def test_daniele_patel_2013_example_2():
    """Tests the second example given in the Appendix of Daniele & Patel (2013, p. 18)"""
    durations = [
        1.0,
        3 / 2,
        1 / 2,
        2 / 3,
        2 / 3,
        2 / 3,
        3 / 2,
        1 / 2,
        3 / 2,
        1 / 2,
        3 / 2,
        1 / 2,
        2 / 3,
        2 / 3,
        2 / 3,
        3 / 2,
        1 / 2,
        3 / 2,
        1 / 2,
        2 / 3,
        2 / 3,
        2 / 3,
        3 / 2,
    ]
    expected = 57.1
    actual = normalized_pairwise_variability_index(durations)
    assert round(actual, 1) == expected


def test_schultz_figure_1():
    """Tests all the examples given in Figure 1 of Condit-Schultz (2019, p. 301)"""
    all_durations = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1 / 2, 1 / 2, 1.0, 1 / 2, 1 / 2],
        [1.0, 1 / 2, 1.0, 1 / 2],
        [3 / 2, 1 / 2, 3 / 2, 1 / 2],
        [7 / 16, 1 / 16, 7 / 16, 1 / 16],
    ]
    expected_results = [0.0, 40.0, 66.7, 100.0, 150.0]
    for durations, expected in zip(all_durations, expected_results):
        actual = normalized_pairwise_variability_index(durations)
        assert round(actual, 1) == expected


def test_not_enough_durations():
    """Test we raise an error with not enough durations"""
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([2.0])
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([])


def test_non_positive_durations():
    """Test we raise an error with negative or non-positive durations"""
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([1.0, 0.0, 3.0, 2.0])
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([3.0, 3.0, -3.0, 2.0])
