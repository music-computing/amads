"""
Calculate the relative entropy of a distribution. (MTB)

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=60
"""

from typing import List

import numpy as np


def entropy(
    d: List[float], in_bits=False, miditoolbox_compatible: bool = False
) -> float:
    """
    Calculate the relative entropy of a distribution.

    This function computes the relative entropy (also known as normalized
    entropy) of a given distribution `d`. The result is a value between 0
    and 1, where 0 indicates no uncertainty (all probability mass is
    concentrated in one outcome) and 1 indicates maximum uncertainty
    (uniform distribution).

    If `in_bits` is set to True, the result will be in bits
    (base 2 logarithm) instead of relative entropy. The `in_bits`
    result gives the expected number of bits needed to encode an outcome
    drawn from the distribution.

    The distribution `d` will be normalized if it does not already sum
    to 1. If `d` is all zeros, the function will return 1.0 to avoid
    division by zero. If `miditoolbox_compatible` is set to True, division
    by zero is avoided by adding a small constant to the distribution,
    which will slightly alter the result. (This is to maintain compatibility
    with the original MIDI Toolbox implementation.)

    Parameters
    ----------
    d
        The input distribution.

    in_bits : bool, optional
        If True, returns unnormalized entropy in bits (base 2 logarithm).
        Default is False: returns relative entropy (0 <= H <= 1).

    miditoolbox_compatible : bool, optional
        If True, uses the original MIDI Toolbox method of calculation.
        Default is False.

    Returns
    -------
    float
        The relative entropy (0 <= H <= 1) unless `in_bits` is True,
        in which case the unnormalized entropy in bits is returned.

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/entropy.m

    Examples
    --------
    Entropy is maximized when all outcomes are equally likely:
    >>> entropy([0.5, 0.5])
    1.0

    Entropy is minimized when one outcome is certain:
    >>> entropy([0.0, 1.0])
    0.0
    """
    d = np.asarray(d).flatten()  # Convert to a 1D numpy array
    sum = np.sum(d)
    if miditoolbox_compatible:
        sum += 1e-12  # Avoid division by zero
    elif sum == 0:
        return 1.0  # Avoid division by zero; return maximum entropy
    d = d / sum  # Normalize
    if miditoolbox_compatible:
        logd = np.log(d + 1e-12)  # Avoid log(0)
    else:
        logd = np.where(
            d > 0, np.log(d), 0
        )  # Compute log(d), treating log(0) as 0
    h = -np.sum(d * logd)
    if in_bits:
        h = h / np.log(2)  # Unnormalized entropy in bits
    else:
        h = h / np.log(len(d))  # Normalize to relative entropy
    return float(h)
