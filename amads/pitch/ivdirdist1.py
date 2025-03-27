"""
Provides the `ivdirdist1` function

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=64
"""

from ..core.basics import Score
from .ivdist1 import ivdist1


def ivdirdist1(score: Score, weighted=True) -> list[float]:
    """
    Returns the proportion of upward intervals for each interval size

    Currently, intervals greater than an octave will be ignored.

    Args:
        score (Score): The musical score to analyze
        weighted (bool, optional): If True, the interval distribution is
                                   weighted by note durations (default True)

    Returns:
        list[float]: A 12-element list representing the proportion of
                     upward intervals for each interval size. The components
                     are spaced at semitone distances with the first component
                     representing a minor second and the last component
                     the octave. If the score is empty, the function
                     returns a list with all elements set to zero.
    """

    id = ivdist1(score, weighted)

    idd = [0] * 12

    for i in range(12):
        # id[i + 13] is the upward interval
        # id[11 - i] is the downward interval
        if (id[i + 13] + id[11 - i]) != 0:
            idd[i] = id[i + 13] / (id[i + 13] + id[11 - i])
        else:
            idd[i] = 0

    return idd
