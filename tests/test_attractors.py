"""
Tests for the `attractor_tempos` module.

Tests functionality for calculating salience.
"""

import numpy as np
import pytest

from amads.time.meter import PulseLengths
from amads.time.meter.attractor_tempos import MetricalSalience, log_gaussian


@pytest.fixture
def metrical_salience_instance():
    """
    Provides a sample set of pulse lengths for testing
    and initialises an instance of MetricalSalience with them.
    """
    pl = [4, 2, 1, 0.5]
    pls = PulseLengths(pulse_lengths=pl, cycle_length=4)
    pulse_array = pls.to_array()
    return MetricalSalience(pulse_array)


def test_init(metrical_salience_instance):
    """Tests the initialization of the MetricalSalience class."""
    assert metrical_salience_instance.quarter_bpm is None
    assert metrical_salience_instance.absolute_pulse_length_array is None
    assert metrical_salience_instance.salience_values_array is None
    assert metrical_salience_instance.cumulative_salience_values is None
    assert metrical_salience_instance.indicator is None
    np.testing.assert_allclose(
        metrical_salience_instance.symbolic_pulse_length_array[0, :],
        np.array([4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    )


def test_calculate_absolute_pulse_lengths(metrical_salience_instance):
    """Tests the `calculate_absolute_pulse_lengths` method."""
    bpm = 100
    metrical_salience_instance.calculate_absolute_pulse_lengths(bpm)
    expected_array = np.array(
        [
            [2.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.2, 0.0, 0.0, 0.0, 1.2, 0.0, 0.0, 0.0],
            [0.6, 0.0, 0.6, 0.0, 0.6, 0.0, 0.6, 0.0],
            [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
        ]
    )
    np.testing.assert_allclose(
        metrical_salience_instance.absolute_pulse_length_array, expected_array
    )


def test_get_salience_values(metrical_salience_instance):
    """Tests the `calculate_salience_values` method."""
    bpm = 120
    metrical_salience_instance.calculate_absolute_pulse_lengths(bpm)
    metrical_salience_instance.calculate_salience_values()
    assert metrical_salience_instance.salience_values_array.shape == (4, 8)


def test_get_cumulative_salience_values(metrical_salience_instance):
    """Tests the `calculate_cumulative_salience_values` method."""
    bpm = 120
    metrical_salience_instance.calculate_absolute_pulse_lengths(bpm)
    metrical_salience_instance.calculate_salience_values()
    metrical_salience_instance.calculate_cumulative_salience_values()
    assert metrical_salience_instance.cumulative_salience_values is not None
    assert metrical_salience_instance.cumulative_salience_values.shape == (8,)


def test_plot(metrical_salience_instance):
    """Tests the plot method with symbolic, and then salience data, showing the difference."""
    bpm = 120
    metrical_salience_instance.calculate_absolute_pulse_lengths(bpm)
    plt, fig = metrical_salience_instance.plot(symbolic_not_absolute=True)
    plt.close(fig)

    metrical_salience_instance.calculate_salience_values()
    plt, fig = metrical_salience_instance.plot(symbolic_not_absolute=False)
    plt.close(fig)


def test_log_gaussian():
    """Tests the `log_gaussian` function."""
    assert np.isclose(log_gaussian(0.6), np.float64(1.0))
    assert np.isclose(log_gaussian(1.2), np.float64(0.604448254722616))
    assert np.isclose(log_gaussian(0.5), np.float64(0.96576814))
    assert np.isclose(log_gaussian(0.0), np.float64(0.0))
