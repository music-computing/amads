#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module implements various functions useful for analyzing swing in jazz, e.g. `beat_upbeat_ratio`."""

from math import log2
from itertools import chain
from typing import Iterable, Generator

import numpy as np


__all__ = ["beat_upbeat_ratio"]
__author__ = "Huw Cheston"


def _bur(
        beat1: float,
        beat2: float,
        upbeats: np.array,
        allow_multiple_burs_per_beat: bool,
        use_log2_burs: bool
) -> Generator:
    """BUR calculation function. Takes in two consecutive beats and gets BURs from provided upbeats."""

    # Beat 2 should always be later than beat 1
    assert beat2 > beat1, "Provided `beats` should be sorted"
    # Find all upbeats between these two beats
    upbeats_bw = upbeats[(beat1 <= upbeats) & (upbeats <= beat2)]
    # If we've found multiple upbeats, and we only want to get one BUR per beat
    if len(upbeats_bw) > 1 and not allow_multiple_burs_per_beat:
        # Just use the first upbeat we've found
        upbeats_bw = np.array([upbeats_bw[0]])  # keep as an array to allow iteration
    # Iterate over all upbeats found between the two beats
    for upbeat_bw in upbeats_bw:
        # Compute the inter-onset intervals
        ioi1 = upbeat_bw - beat1
        ioi2 = beat2 - upbeat_bw
        # Calculate the beat-upbeat ratio
        bur = ioi2 / ioi1
        # Express with base-2 log if required
        if use_log2_burs:
            bur = log2(bur)
        yield float(bur)


def beat_upbeat_ratio(
        beats: Iterable,
        upbeats: Iterable,
        use_log2_burs: bool = False,
        allow_multiple_burs_per_beat: bool = False
) -> list:
    """
    Extracts beat-upbeat ratio (BUR) values from an array of onsets.

    The beat-upbeat ratio (BUR) is introduced in [1] as a concept for analyzing the individual amount of "swing"
    in two consecutive eighth-note beat durations. It is calculated by dividing the duration of the first
    ("long") eighth note beat by the second ("short") beat. A BUR value of 2 indicates "perfect" swing
    (e.g., a triplet quarter note followed by a triplet eighth note), while a BUR of 1 indicates "even"
    eighth-note durations.

    Accepts two iterables of timestamps, corresponding to `beats` and `upbeats`. These lists should be sorted,
    but missing values can be included and will be handled internally in the function.

    By default, the function assumes there is exactly one upbeat between every two consecutive beats. If there
    are multiple upbeats between two beats, only the first upbeat is used for BUR calculation unless
    `allow_multiple_burs_per_beat=True`, in which case a BUR is calculated for every upbeat.

    Following [2], it is also common to calculate log_2 BUR values, which means that a value of 0.0 corresponds
    to "triplet" swing. This can be enabled by setting `use_log2_burs=True`.

    Parameters
    ----------
    beats : iterable
        An array of beat timestamps. Should not overlap with `upbeats`.
    upbeats : iterable
        An array of upbeat timestamps.
    use_log2_burs : bool, optional
        Whether to use the log_2 of inter-onset intervals to calculate BURs, as employed in [2]. Defaults to False.
    allow_multiple_burs_per_beat : bool, optional
        If True, calculates a beat-upbeat ratio for every upbeat between two consecutive beats. Otherwise,
        calculates a BUR only for the first upbeat. Defaults to False.

    Returns
    -------
    list
        The calculated BUR values.

    Raises
    ------
    ValueError
        If too few consecutive beats are provided

    Examples
    --------
    >>> my_upbeats = np.array([0.6, 1.4])
    >>> my_beats = np.array([0., 1., 2.])
    >>> returned = beat_upbeat_ratio(my_beats, my_upbeats)
    >>> [round(r, 2) for r in returned]
    [0.67, 1.5]

    >>> my_upbeats = np.array([0.6, 1.4])
    >>> my_beats = np.array([0., 1., 2.])
    >>> returned = beat_upbeat_ratio(my_beats, my_upbeats, use_log2_burs=True)
    >>> [round(r, 2) for r in returned]
    [-0.58, 0.58]

    >>> my_upbeats = np.array([0.6, 0.7, 1.4])
    >>> my_beats = np.array([0., 1., 2.])
    >>> returned = beat_upbeat_ratio(my_beats, my_upbeats, allow_multiple_burs_per_beat=True)
    >>> [round(r, 2) for r in returned]
    [0.67, 0.43, 1.5]

    References
    ----------
    [1] Benadon, F. (2006). Slicing the Beat: Jazz Eighth-Notes as Expressive Microrhythm. Ethnomusicology,
        50/1 (pp. 73–98). https://doi.org/10.2307/20174424
    [2] Corcoran, C., & Frieler, K. (2021). Playing It Straight: Analyzing Jazz Soloists’ Swing Eighth-Note
        Distributions with the Weimar Jazz Database. Music Perception, 38(4), 372–385.
        https://doi.org/10.1525/mp.2021.38.4.372

    """

    # Parse beats and upbeats to an array
    beats = np.array(beats)
    upbeats = np.array(upbeats)
    # Remove any values from our `upbeats` variable that are also contained in `beats`
    upbeats_ = upbeats[~np.isin(upbeats, beats)]
    beats_ = beats[~np.isin(beats, upbeats)]
    # Assert that there is no overlap between both arrays
    assert not any(np.isin(beats_, upbeats_)), "`beats` and `upbeats` must be exclusive but they overlap"
    assert not any(np.isin(upbeats_, beats_)), "`beats` and `upbeats` must be exclusive but they overlap"
    # Get consecutive pairs of (non-missing) beats
    consecutive_beats = [(b1, b2) for b1, b2 in zip(beats_, beats_[1:]) if not any((np.isnan(b1), np.isnan(b2)))]
    # Raise if we don't have enough beats to calculate BURs for
    if len(consecutive_beats) < 1:
        raise ValueError('Not enough consecutive `beats` provided')
    # Calculate the BUR for upbeats between consecutive beats
    found_burs = [_bur(b1, b2, upbeats_, allow_multiple_burs_per_beat, use_log2_burs) for b1, b2 in consecutive_beats]
    # Unpack list of generators to a flat list
    return list(chain.from_iterable(found_burs))
