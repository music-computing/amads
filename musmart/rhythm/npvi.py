#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module implements the `normalized_pairwise_variability_index` function."""

from typing import Iterable

import numpy as np


__all__ = ["normalized_pairwise_variability_index"]
__author__ = "Huw Cheston"


def normalized_pairwise_variability_index(sequence: Iterable) -> float:
    """
    Extracts the normalised pairwise variability index (nPVI).

    The nPVI is a measure of variability between successive elements in a sequence, commonly used
    in music analysis to quantify rhythmic variability [1].

    Parameters
    ----------
    sequence : iterable
        The data to calculate the nPVI for. 1D iterables (list, array) are supported.

    Returns
    -------
    float
        The extracted nPVI value.

    Examples
    --------
    >>> res = normalized_pairwise_variability_index(np.array([1, 2, 3]))
    >>> round(res)
    53

    References
    ----------
    [1] Daniele, J. R., & Patel, A. D. (2013). An Empirical Study of Historical Patterns in Musical Rhythm.
        Music Perception, 31/1 (pp. 10-18). https://doi.org/10.1525/mp.2013.31.1.10

    """

    numerator = sum([abs((k - k1) / ((k + k1) / 2)) for (k, k1) in zip(sequence, sequence[1:])]) * 100
    denominator = sum(range(len(sequence))) - 1
    return numerator / denominator
