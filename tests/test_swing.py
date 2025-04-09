"""Test suite for amads.time.swing.py"""

import numpy as np
import pytest

from amads.time.swing import _validate_bur_inputs, beat_upbeat_ratio, mean_bur, std_bur

TEST_BEATS = [
    [0.0, 1.0, 2.0],
    [0.0, 1.0, 2.0, 3.0, 4.0],
    [0.0, 1.3, 2.2, 3.3, 5.5, 6.1],
]
TEST_UPBEATS = [
    [0.6, 1.4],  # example 1, straightforward
    [0.5, 1.2, 2.6, 3.5, 4.9],  # example 2, slightly harder
    [
        0.5,
        1.2,
        2.7,
        3.5,
        3.6,
    ],  # example 3: b1 + b4 skipped as two upbeats, b2 + b5 skipped as have no upbeat
]
TEST_BURS = [[1.5, 2 / 3], [1.0, 0.25, 1.5, 1.0], [None, None, 0.5 / 0.6, None, None]]


@pytest.mark.parametrize(
    "beats,upbeats,expecteds", zip(TEST_BEATS, TEST_UPBEATS, TEST_BURS)
)
def test_bur(beats, upbeats, expecteds):
    burs = beat_upbeat_ratio(beats, upbeats)
    assert pytest.approx(burs) == expecteds
    assert len(burs) == len(beats) - 1


def test_validate_bur_inputs():
    # Test 1: Invalid input - Less than two beats
    beats = np.array([1.0])
    upbeats = np.array([1.5])
    with pytest.raises(ValueError):
        _validate_bur_inputs(beats, upbeats)

    # Test 2: Invalid input - No upbeats
    beats = np.array([1.0, 2.0, 3.0])
    upbeats = np.array([])
    with pytest.raises(ValueError):
        _validate_bur_inputs(beats, upbeats)

    # Test 3: Invalid input - Multi-dimensional beats
    beats = np.array([[1.0, 2.0], [3.0, 4.0]])
    upbeats = np.array([1.5])
    with pytest.raises(ValueError):
        _validate_bur_inputs(beats, upbeats)

    # Test 4: Invalid input - Multi-dimensional upbeats
    beats = np.array([1.0, 2.0, 3.0])
    upbeats = np.array([[1.5]])
    with pytest.raises(ValueError):
        _validate_bur_inputs(beats, upbeats)

    # Test 5: Invalid input - NaN in beats
    beats = np.array([1.0, np.nan, 3.0])
    upbeats = np.array([1.5])
    with pytest.raises(ValueError):
        _validate_bur_inputs(beats, upbeats)

    # Test 6: Invalid input - NaN in upbeats
    beats = np.array([1.0, 2.0, 3.0])
    upbeats = np.array([np.nan])
    with pytest.raises(ValueError):
        _validate_bur_inputs(beats, upbeats)

    # Test 7: Invalid input - Intersection between beats and upbeats
    beats = np.array([1.0, 2.0, 3.0])
    upbeats = np.array([2.0])
    with pytest.raises(ValueError):
        _validate_bur_inputs(beats, upbeats)


def test_no_matches():
    beats = [
        0.0,
        1.0,
        2.0,
        3.0,
    ]
    upbeats = [5.0, 6.0, 7.0, 8.0]
    with pytest.raises(ValueError):
        _ = beat_upbeat_ratio(beats, upbeats)


def test_bounded_burs():
    beats = [
        0.0,
        1.0,
        2.0,
        3.0,
    ]
    upbeats = [0.5, 1.5, 2.99]
    expected = [1.0, 1.0, None]
    actual = beat_upbeat_ratio(beats, upbeats, bounded=True)
    assert pytest.approx(actual) == expected


def test_log2_burs():
    beats = [0.0, 1.0, 2.0, 3.0]
    upbeats = [1 / 3, 5 / 3, 2.5]
    expected = [-1.0, 1.0, 0.0]
    actual = beat_upbeat_ratio(beats, upbeats, log2=True)
    assert pytest.approx(actual) == expected


def test_agg_funcs():
    beats = [
        0.0,
        1.0,
        2.0,
        3.0,
    ]
    upbeats = [0.5, 1.75, 2.8]
    mean = 8 / 3  # burs = [1., 3., 4.]
    sd = 1.247219
    assert pytest.approx(mean_bur(beats, upbeats)) == mean
    assert pytest.approx(std_bur(beats, upbeats)) == sd
