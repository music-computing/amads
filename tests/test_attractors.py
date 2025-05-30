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
    return MetricalSalience(pulse_array, quarter_bpm=100)


def test_symbolic(metrical_salience_instance):
    """Tests the initialization of the MetricalSalience class."""
    np.testing.assert_allclose(
        metrical_salience_instance.symbolic_pulses[0, :],
        np.array([4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    )


def test_absolute_pulse_lengths(metrical_salience_instance):
    np.testing.assert_allclose(
        metrical_salience_instance.absolute_pulses,
        np.array(
            [
                [2.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [1.2, 0.0, 0.0, 0.0, 1.2, 0.0, 0.0, 0.0],
                [0.6, 0.0, 0.6, 0.0, 0.6, 0.0, 0.6, 0.0],
                [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
            ]
        ),
    )


def test_get_salience_values(metrical_salience_instance):
    """Tests the `calculate_salience_values` method."""
    metrical_salience_instance.calculate_salience_values()
    assert metrical_salience_instance.salience_values.shape == (4, 8)


def test_get_cumulative_salience_values(metrical_salience_instance):
    """Tests the `calculate_cumulative_salience_values` method."""
    assert metrical_salience_instance.cumulative_salience_values is not None
    assert metrical_salience_instance.cumulative_salience_values.shape == (8,)
    np.testing.assert_allclose(
        metrical_salience_instance.cumulative_salience_values,
        np.array(
            [
                2.342383,
                0.604448,
                1.604448,
                0.604448,
                2.208897,
                0.604448,
                1.604448,
                0.604448,
            ]
        ),
        atol=1e-06,
    )


def test_plot(metrical_salience_instance):
    """Tests the plot method with symbolic, and then salience data, showing the difference."""
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


def test_log_gaussian_raises():
    """Tests the `log_gaussian` function raises errors in these cases."""
    with pytest.raises(ValueError):
        log_gaussian(0.6, mu=-1)
    with pytest.raises(ValueError):
        log_gaussian(0.6, sig=-100)
