__author__ = "Yiwen Zhao"

import numpy as np
from ..core.basics import Score
from ..algorithms import pcdist1, pcdist2, ivdist1, ivdist2

def calculate_mel_distance(score1: Score, score2: Score, repr='pcdist1', metric='taxi', samples=10, rescale=0) -> float:
    """
    Measurement of distance between two Score objects.

    Parameters
    ----------
    score1 : Score
        The first Score object.
    score2 : Score
        The second Score object.
    repr : str
        The representation used for comparison.
    metric : str
        The distance metric used for comparison.
    samples : int
        Number of samples for contour representation.
    rescale : int
        Rescale distance to similarity value between 0 and 1.

    Returns
    -------
    float
        Value representing the distance between the two scores under the given representation and metric.

    Examples
    --------
    >>> calculate_mel_distance(score1, score2, 'pcdist1', 'taxi')
    0.16666666666666666  # Example output
    """
    if repr == 'pcdist1':
        dist1 = pcdist1(score1)
        dist2 = pcdist1(score2)
    elif repr == 'pcdist2':
        dist1 = pcdist2(score1)
        dist2 = pcdist2(score2)
    elif repr == 'ivdist1':
        dist1 = ivdist1(score1)
        dist2 = ivdist1(score2)
    elif repr == 'ivdist2':
        dist1 = ivdist2(score1)
        dist2 = ivdist2(score2)
    else:
        raise ValueError("Unsupported representation type.")

    if metric == 'taxi':
        distance = np.sum(np.abs(dist1 - dist2))
    elif metric == 'euc':
        distance = np.sqrt(np.sum((dist1 - dist2) ** 2))
    elif metric == 'cosine':
        distance = 1 - np.dot(dist1, dist2) / (np.linalg.norm(dist1) * np.linalg.norm(dist2))
    else:
        raise ValueError("Unsupported metric type.")

    if rescale == 1:
        max_distance = np.max([np.sum(dist1), np.sum(dist2)])
        distance = distance / max_distance if max_distance > 0 else 0

    return distance
