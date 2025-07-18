"""
Maximal correlation from Krumhansl-Kessler algorithm.

Author(s):
Tai Nakamura
Di Wang (diwang2)

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=69
"""

from kkcc import kkcc

from .core.basics import Score


def maxkkcc(score: Score) -> float:
    """
    provides the maximal correlation from calling kkcc with krumhansl-kessler
    profile (default) option.

    Parameters
    ----------
    score (Score): The musical score to analyze.

    Returns
    -------
    float
    Maximal correlation from calling kkcc with default options
    """
    return max(kkcc(score))
