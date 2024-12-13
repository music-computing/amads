"""
Implements the `entropy` function.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=60
"""

from typing import List

import numpy as np


def entropy(d: List[float]) -> float:
    """
    Calculate the relative entropy of a distribution.

    Parameters
    ----------
    d
        The input distribution.

    Returns
    -------
    float
        The relative entropy (0 <= H <= 1).

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/entropy.m

    Examples
    --------
    >>> entropy([0.5, 0.5])
    1.0

    >>> entropy([0.0, 1.0])
    0.0
    """
    d = np.asarray(d).flatten()  # Convert to a 1D numpy array
    d = d / (np.sum(d) + 1e-12)  # Normalize
    logd = np.log(d + 1e-12)
    h = -np.sum(d * logd) / np.log(len(d))  # Compute the entropy and normalize

    return float(h)
