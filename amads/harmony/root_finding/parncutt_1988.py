"""
Parncutt's 1988 model for finding the root of a chord.
"""

from typing import List

weights = [0.0 for _ in range(12)]
weights[0] = 1.0
weights[7] = 0.50
weights[4] = 0.33
weights[10] = 0.25
weights[2] = 0.20
weights[3] = 0.10


def root_strengths(chord: List[int]) -> List[float]:
    """
    Calculate the root strengths for a given chord using Parncutt's 1988 model.
    """
    if len(chord) == 0:
        raise ValueError("Chord must contain at least one pitch")
    pitch_class_set = set([pitch % 12 for pitch in chord])
    strengths = []
    for pitch_class in range(12):
        strength = 0.0
        for root_support_interval, weight in zip(range(12), weights):
            if (pitch_class + root_support_interval) % 12 in pitch_class_set:
                strength += weight
        strengths.append(strength)
    return strengths


def root(chord: List[int]) -> int:
    """
    Estimates the root of a chord using Parncutt's 1988 model.

    Parameters
    ----------
    chord: List[int]
        A list of MIDI pitches representing a chord.

    Returns
    -------
    int
        The pitch class of the estimated root.


    Examples
    --------
    >>> root([0, 4, 7])
    0
    >>> root([0, 4, 7, 10])
    0
    >>> root([2, 5, 9])
    2
    """
    strengths = root_strengths(chord)
    return strengths.index(max(strengths))
