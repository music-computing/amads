"""
This module provides functions for analyzing tempo characteristics in musical performances.
It includes calculations for tempo slope, tempo drift, and tempo fluctuation.

References:
    - Cheston, H., Schlichting, J. L., Cross, I., & Harrison, P. M. C. (2024).
      Jazz Trio Database: Automated Annotation of Jazz Piano Trio Recordings Processed Using
      Audio Source Separation. Transactions of the International Society for Music Information
      Retrieval, 7(1), 144–158. https://doi.org/10.5334/tismir.186

    - Cheston, H., Cross, I., & Harrison, P. (2024). Trade-offs in Coordination Strategies
      for Duet Jazz Performances Subject to Network Delay and Jitter.
      Music Perception, 42(1), 48–72. https://doi.org/10.1525/mp.2024.42.1.48

Author:
    Huw Cheston (2025)
"""

from typing import Iterable, Union

import numpy as np

__author__ = "Huw Cheston"


# flake8: noqa: W605
def tempo_slope(beats: Iterable[float]) -> float:
    r"""
    Calculates the tempo slope for a sequence of beat timestamps.

    The tempo slope represents the overall tempo change per second in a performance.
    It is determined by the slope of a linear regression of instantaneous tempo against
    beat onset time. A negative slope indicates deceleration, while a positive slope
    indicates acceleration. The units are (quarter-note) beats-per-minute-per-second

    The equation is:

    .. math::
        \hat{S} = \frac{\sum\limits_{i=1}^N (x_i - \bar{x}) (y_i - \bar{y})}{\sum\limits_{i=1}^N (x_i - \bar{x})^2},

    where :math:`x_i` is the time of beat :math:`i` and :math:`y_i` is the tempo value in
    (quarter-note) beats-per-minute.

    Parameters
    ----------
    beats : Iterable[float]
        An iterable of beat timestamps in seconds, such as quarter-note onsets.

    Returns
    -------
    float
        The computed tempo slope value.

    """

    return float(fit_tempo_linear_regression(beats).slope)


# flake8: noqa: W605
def tempo_fluctuation(beats: Iterable[float]) -> float:
    r"""
    Calculates the fluctuation around the overall tempo of a sequence of beats.

    Tempo fluctuation is measured as the standard deviation of the instantaneous tempo,
    normalized by the mean tempo. Higher values indicate greater variability in tempo.

    The equation is:

    .. math::
        \text{F} = \dfrac{\sqrt{\frac{1}{N-1} \sum\limits_{i=1}^N (y_i - \bar{y})^2}}{\bar{y}},

    where :math:`y_i` is the tempo value in (quarter-note) beats-per-minute at beat :math:`i`.

    Parameters
    ----------
    beats : Iterable[float]
        An iterable of beat timestamps in seconds, such as quarter-note onsets.

    Returns
    -------
    float
        The computed tempo fluctuation value.

    """

    # Compute instantaneous tempo values: this will also validate the input
    tempos = beats_to_tempo(beats)
    # Compute tempo fluctuation
    # No need for np.nanstd etc. here, we won't have NaN values
    return float(np.std(tempos) / np.mean(tempos))


def tempo_mean(beats: Iterable[float]):
    r"""
    Calculates the mean tempo from an iterable of timestamps in quarter-note beats-per-minute.

    The mean tempo can be calculated simply as:

    .. math::
        \bar{y} = \dfrac{\sum\limits_{i=1}^N\frac{60}{x_i - x_{i-1}}}{N-1}

    where :math:`x_i` is the time of beat :math:`i` (and :math:`i \geq 1`) and :math:`N` is the number of beats.

    Parameters
    ----------
    beats : Iterable[float]
        An iterable of beat timestamps in seconds, such as quarter-note onsets.

    Returns
    -------
    float
        The computed mean tempo value.

    """

    return np.mean(beats_to_tempo(beats))


def _validate_beats(beats: Union[Iterable[float], np.ndarray]) -> None:
    """Checks an iterable of beat timestamps and raises errors as required"""

    if not isinstance(beats, np.ndarray):
        beats = np.array(beats, dtype=float)  # expecting a float dtype
    if np.isnan(np.sum(beats)):
        raise ValueError(
            "Cannot calculate instantaneous tempo measurements from array of beats with missing values"
        )
    if len(beats) < 2:
        raise ValueError("Must pass at least two beat timestamps")
    if len(beats.shape) != 1:
        raise ValueError("Beat timestamps must be 1-dimensional")
    if not np.array_equal(np.sort(beats), beats):
        raise ValueError("Beat timestamps must increase linearly")
    if len(np.unique(beats)) != len(beats):
        raise ValueError("Beat timestamps must not contain duplicates")


def beats_to_tempo(beats: np.ndarray) -> np.ndarray:
    """Converts beat timestamps to instantaneous tempo measurements."""

    # Raise error on invalid inputs
    _validate_beats(beats)
    return np.array(60 / np.diff(beats))


def fit_tempo_linear_regression(beats: Iterable[float]):
    """Fits linear regression of BPM measurements vs. onset time."""

    from scipy.stats import linregress

    # Target variable: BPM measurements
    # This will also validate the input
    beats_arr = np.array(beats)
    y = beats_to_tempo(beats_arr)
    # Predictor variable: the onset time
    x = beats_arr[1:]
    return linregress(x, y)
