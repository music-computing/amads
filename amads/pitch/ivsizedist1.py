"""
Provides the `ivsizedist1` function
"""

from ..core.basics import Score
from .ivdist1 import ivdist1


def ivsizedist1(score: Score, weighted=True) -> list[float]:
    """
    Returns the interval size distribution of a musical score.

    Args:
        score (Score): The musical score to analyze.
        weighted (bool, optional): If True, the interval distribution is
                                   weighted by note durations (default True).

    Returns:
        list[float]: A 13-element list representing the interval size
                     distribution. The first element corresponds to unison
                     intervals, and the last element corresponds to octave
                     intervals. If the score is empty, the function returns
                     a list with all elements set to zero.
    """
    id = ivdist1(score, weighted)

    isd = [0] * 13
    isd[0] = id[12]
    for i in range(1, 13):
        isd[i] = id[i + 12] + id[12 - i]

    return isd
