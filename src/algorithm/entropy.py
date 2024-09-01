"""
Provides the `entropy` function.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=60
"""
import numpy as np


def entropy(d):
    """
    Calculate the relative entropy of a distribution.

    Parameters:
    d (list): The input distribution.

    Returns:
    float: The relative entropy (0 <= H <= 1).
    """
    # The following algorithm is from the original MATLAB implementation
    # https://github.com/miditoolbox/1.1/blob/master/miditoolbox/entropy.m
    
    d = np.asarray(d).flatten()  # Convert to a 1D numpy array
    d = d / (np.sum(d) + 1e-12)  # Normalize
    logd = np.log(d + 1e-12)  
    h = -np.sum(d * logd) / np.log(len(d))  # Compute the entropy and normalize

    return h
