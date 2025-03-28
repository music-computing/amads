"""Test suite for tempo modelling functions inside amads/time/tempo.py"""

import numpy as np
import pytest

from amads.time.tempo import (
    _validate_beats,
    beats_to_tempo,
    tempo_fluctuation,
    tempo_mean,
    tempo_slope,
)

# Quarter note beat positions for different "performances"
STABLE_PERFORMANCE = [1.0, 2.0, 3.0, 4.0]
ACCELERATING_PERFORMANCE = [1.0, 1.9, 2.7, 3.4]
DECELERATING_PERFORMANCE = [1.0, 2.1, 3.3, 4.6]


def test_mean_tempo():
    stable_bpm_mean = 60.0
    assert pytest.approx(tempo_mean(STABLE_PERFORMANCE)) == stable_bpm_mean
    accelerating_bpm_mean = 75.7936
    assert (
        pytest.approx(tempo_mean(ACCELERATING_PERFORMANCE), abs=1e-4)
        == accelerating_bpm_mean
    )
    decelerating_bpm_mean = 50.2331
    assert (
        pytest.approx(tempo_mean(DECELERATING_PERFORMANCE), abs=1e-4)
        == decelerating_bpm_mean
    )


def test_tempo_slope():
    assert tempo_slope(STABLE_PERFORMANCE) == 0.0
    assert tempo_slope(ACCELERATING_PERFORMANCE) > 0
    assert tempo_slope(DECELERATING_PERFORMANCE) < 0


def test_tempo_fluctuation():
    # Stable performance should not fluctuate
    assert tempo_fluctuation(STABLE_PERFORMANCE) == 0.0
    # Unstable performances should fluctuate
    assert tempo_fluctuation(ACCELERATING_PERFORMANCE) > 0
    assert tempo_fluctuation(DECELERATING_PERFORMANCE) > 0


def test_beats_to_tempo():
    # With a stable performance with IBI = 1.0, we'll expect a full array of 60 BPMs
    stable_bpms = beats_to_tempo(STABLE_PERFORMANCE)
    assert np.array_equal(
        stable_bpms.round(1),
        np.array(
            [
                60.0,
                60.0,
                60.0,
            ]
        ),
    )
    # Test another performance that accelerates: IBIs decrease, BPMs increase
    accelerating_bpms = beats_to_tempo(ACCELERATING_PERFORMANCE)
    assert np.array_equal(accelerating_bpms.round(1), np.array([66.7, 75, 85.7]))
    # Test another performance that decelerates: IBIs increase, BPMs decrease
    decelerating_bpms = beats_to_tempo(DECELERATING_PERFORMANCE)
    assert np.array_equal(decelerating_bpms.round(1), np.array([54.5, 50.0, 46.2]))


def test_validate_beats():
    # Valid case (should not raise an error)
    valid_beats = [0.5, 1.0, 1.5, 2.0, 2.5]
    assert _validate_beats(valid_beats) is None
    # Too few beats
    with pytest.raises(ValueError):
        _validate_beats([0.5])
    # Non-1D array
    with pytest.raises(ValueError):
        _validate_beats([[0.5, 1.0], [1.5, 2.0]])
    # Unsorted beats
    with pytest.raises(ValueError):
        _validate_beats([0.5, 1.5, 1.0, 2.0])
    # Duplicate values
    with pytest.raises(ValueError):
        _validate_beats([0.5, 1.0, 1.0, 2.0])  # Duplicate 1.0
    # NaN values
    with pytest.raises(ValueError):
        _validate_beats([0.5, 1.0, None, 2.0])
