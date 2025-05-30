"""
This module implements various functions useful for analyzing swing in jazz and other genres.

References:
    - Benadon, F. (2006). Slicing the Beat: Jazz Eighth-Notes as Expressive Microrhythm.
      Ethnomusicology, 50(1), 73–98. https://doi.org/10.2307/20174424
    - Corcoran, C., & Frieler, K. (2021). Playing It Straight: Analyzing Jazz Soloists’ Swing
      Eighth-Note Distributions with the Weimar Jazz Database. Music Perception, 38(4), 372–385.
      https://doi.org/10.1525/mp.2021.38.4.372

Author:
    Huw Cheston (2025)

"""

from math import log2 as log2_
from typing import Iterable

import numpy as np

__author__ = "Huw Cheston"

TINY = 1e-8
LOW_BUR, HIGH_BUR = (
    0.25,
    4.0,
)  # the range of BURs to keep as defined in Corcoran & Frieler (2021)


# flake8: noqa: W605
def beat_upbeat_ratio(
    beats: Iterable[float],
    upbeats: Iterable[float],
    log2: bool = False,
    bounded: bool = False,
    lower_bound: float = LOW_BUR,
    upper_bound: float = HIGH_BUR,
) -> list[float]:
    r"""
    Extracts beat-upbeat ratio (BUR) values from an array of beats and upbeats.

    The beat-upbeat ratio (BUR) is used to analyze the amount of "swing" in two consecutive
    eighth-note beat durations. It is calculated by dividing the duration of the first ("long")
    eighth-note beat by the duration of the second ("short") eighth-note beat. A BUR value of 2
    represents "perfect" swing (e.g., a triplet quarter note followed by a triplet eighth note),
    while a BUR of 1 represents "even" eighth-note durations.

    The formula for BUR is:

    .. math::
        \text{BUR} = \frac{t_{a,b} - t_{a}}{t_{b} - t_{a,b}},

    where :math:`t_a` is the beat at position :math:`a`, :math:`t_b` is the beat at position :math:`b`,
    and :math:`t_{a,b}` is the single upbeat between beats :math:`a` and :math:`b`.

    The function takes two iterables of timestamps: `beats` and `upbeats`. Both lists should be
    unique, and missing values should not be present. The function returns an array of BUR values with
    a size of `len(beats) - 1`. If multiple `upbeats` are found between two consecutive `beats`
    or if no `upbeat` is found, the BUR for those beats will be omitted and the corresponding value
    will be `None`.

    Additionally, the function can calculate the :math:`log_2` of the BUR values, where a value of 0.0
    corresponds to "triplet" swing. This can be enabled by setting `log2=True`. The values can also
    be filtered to remove outliers by setting `bounded=True`, with the default values for the boundaries
    coming from Corcoran & Frieler (2021).

    Parameters
    ----------
    beats : Iterable[float]
        An array of beat timestamps. Should not overlap with `upbeats`.
    upbeats : Iterable[float]
        An array of upbeat timestamps.
    log2 : bool, optional
        If True, computes the log base 2 of BUR values, as used in [2]. Defaults to False.
    bounded : bool, optional
        If True, filters out BUR values outside the specified range. Defaults to False.
    lower_bound : float, optional
        Lower boundary for filtering BUR values. Defaults to 0.25 (:math:`log_2` -2).
    upper_bound : float, optional
        Upper boundary for filtering BUR values. Defaults to 4.0 (:math:`log_2` 2).

    Returns
    -------
    list[float]
        A list of the calculated BUR values.

    Examples
    --------
    >>> my_beats = [0., 1., 2., 3.]
    >>> my_upbeats = [0.5, 1.75, 2.2]
    >>> beat_upbeat_ratio(my_beats, my_upbeats)
    [1., 3., 0.25]

    >>> # Consecutive beats without a matching upbeat will be skipped.
    >>> my_beats = [0., 1., 2., 3.]
    >>> my_upbeats = [0.5, 2.2]
    >>> beat_upbeat_ratio(my_beats, my_upbeats)
    [1., None, 0.25]

    >>> # Consecutive beats with multiple matching upbeats will be skipped.
    >>> my_beats = [0., 1., 2., 3.]
    >>> my_upbeats = [0.5, 1.5, 1.75, 1.8, 2.2]
    >>> beat_upbeat_ratio(my_beats, my_upbeats)
    [1., None, 0.25]

    >>> # Filter out outlying values by setting `bounded=True`.
    >>> my_beats = [0., 1., 2., 3.]
    >>> my_upbeats = [0.5, 1.75, 2.99]
    >>> beat_upbeat_ratio(my_beats, my_upbeats, bounded=True)
    [1., 3., None]

    """

    # Parse beats and upbeats to an array, sorting as required
    beats = np.sort(np.array(beats))
    upbeats = np.sort(np.array(upbeats))
    # Validate inputs and raise an errors if required
    _validate_bur_inputs(beats, upbeats)
    # Match beats with upbeats and return a 2d array of shape [[beat1, upbeat, beat2], [beat2, upbeat, beat3]]
    matched = match_beats_and_upbeats(beats, upbeats)
    # Raise an error if we cannot find any matches between beats and upbeats
    if all([np.isnan(i) for i in matched[:, 1]]):
        raise ValueError(
            "No matches found between beats and upbeats, cannot calculate BUR"
        )
    # Calculate the BUR for upbeats between consecutive beats
    burs = [
        _bur(b1, upbeat, b2) if not np.isnan(upbeat) else None
        for b1, upbeat, b2 in matched
    ]
    # Apply our filtering if required
    # Filter before log_2 transform to make things simpler
    if bounded:
        burs = [i if lower_bound < i < upper_bound else None for i in burs]
    # Express as base-2 log if required
    if log2:
        burs = [log2_(b) if b is not None else None for b in burs]
    return burs


def mean_bur(beats: Iterable[float], upbeats: Iterable[float], **kwargs) -> float:
    """Calculates mean BUR (or :math:`log_2` BUR) given a list of beats and upbeats"""
    # We use nanmean here as we may have null values in cases where multiple upbeats match with a
    #  single pair of beats, or where no upbeats match with a beat.
    #  I think this makes sense to avoid the user having to chop a large list into multiple sublists
    #  depending on the presence of nans.
    return float(np.nanmean(beat_upbeat_ratio(beats, upbeats, **kwargs)))


def std_bur(beats: Iterable[float], upbeats: Iterable[float], **kwargs) -> float:
    """Calculates standard deviation BUR (or :math:`log_2` BUR) given a list of beats and upbeats"""
    return np.nanstd(beat_upbeat_ratio(beats, upbeats, **kwargs))


def _validate_bur_inputs(beats: np.ndarray, upbeats: np.ndarray) -> None:
    """Validate beats and upbeats before calculating BURs"""
    if len(beats) < 2:
        raise ValueError("Must have at least two beats to calculate BURs")
    if len(upbeats) < 1:
        raise ValueError("Must have at least one upbeat to calculate BURs")
    if len(beats.shape) > 1 or len(upbeats.shape) > 1:
        raise ValueError("Beats and upbeats must be one-dimensional arrays")
    if np.isnan(np.sum(beats)) or np.isnan(np.sum(upbeats)):
        raise ValueError("Missing values found in beats or upbeats")
    for b1 in beats:
        if any(np.isclose(b1, upbeats, atol=TINY)):
            raise ValueError("Intersection found between beats and upbeats")


def match_beats_and_upbeats(beats: np.ndarray, upbeats: np.ndarray) -> np.ndarray:
    """Iterates over consecutive beats and creates an array of `[[beat1, upbeat, beat2], [beat2, upbeat, beat3]]`"""

    matched = []
    # Iterate over consecutive pairs of beats
    for b1, b2 in zip(beats, beats[1:]):
        # Get the upbeats that are between both pairs of beats
        upbeat_bw = upbeats[(b1 < upbeats) & (upbeats < b2)]
        # Add a missing value in cases where multiple upbeats match with a single pair of beats, or no upbeats match
        #  We do not consider cases where multiple upbeats match with a single beat, as these are not "swing 8ths"
        #  Adding a missing value means that we'll have the shape len(beats) - 1
        if len(upbeat_bw) > 1 or len(upbeat_bw) == 0:
            matched.append([b1, None, b2])
        # This will only catch cases where we have matched a single upbeat
        else:
            matched.append([b1, upbeat_bw[0], b2])
    # Create a 2d array of [[beat1, upbeat, beat2], [beat2, upbeat, beat3]]
    return np.array(matched, dtype=float)


def _bur(beat1: float, upbeat: float, beat2: float) -> float:
    """BUR calculation function. Takes in two consecutive beats and gets BURs from provided upbeats."""

    # Everything should be in order
    assert beat1 - TINY < upbeat < beat2 + TINY
    # Calculate IOIs
    ioi1 = upbeat - beat1
    ioi2 = beat2 - upbeat
    # Calculate BUR
    return ioi1 / ioi2
