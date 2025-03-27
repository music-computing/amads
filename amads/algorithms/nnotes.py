"""
Provides the `nnotes` function

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=77
"""

from ..core.basics import Note, Score


def nnotes(score: Score):
    """
    Returns the number of notes in a musical score.

    Args:
        score (Score): The musical score to analyze

    Returns:
        int: The number of notes in the score
    """

    total = 0
    for note in score.find_all(Note):
        total += 1
    return total
