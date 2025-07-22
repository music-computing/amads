"""
Basic properties of rhythms, which is to say 1D representations of musical events,
without measures, beats etc., and certainly no scores.

Broadly, this is for stand-alone functions clearly intended for
short, simple representations of rhythmic cycles,
and is not suitable for calling on scores, for instance.
"""

__author__ = "Mark Gotham"

from fractions import Fraction
from typing import Union

from amads.core.vectors_sets import saturated_subsequence_repetition, vector_to_multiset


def has_oddity_property(vector: Union[list[int], tuple[int, ...]]):
    """
    Given a rhythm cycle (i.e., with the expectation of repetition) as a vector,
    check if it has Arom's "rhythmic-oddity" property:
    no two onsets partition the cycle into two equal parts.
    I.e., no repetition of a sub-rhythm.
    This is a specific case of `saturated_subsequence_repetition`, see notes there.

    Parameters
    ----------
    vector: A vector for either the event positions in the cycle time span, or the beat pattern (sic, either).

    Returns
    -------
    True if the rhythm has the rhythmic-oddity property, False otherwise.

    Examples
    --------

    Here are ten 12-unit bell pattern rhythms identified in Gomez et al. as "canonical":

    >>> Soli = (2, 2, 2, 2, 1, 2, 1)
    >>> Tambú = (2, 2, 2, 1, 2, 2, 1)
    >>> Bembé = (2, 2, 1, 2, 2, 2, 1)
    >>> Bembé_2 = (1, 2, 2, 1, 2, 2, 2)
    >>> Yoruba = (2, 2, 1, 2, 2, 1, 2)
    >>> Tonada = (2, 1, 2, 1, 2, 2, 2)
    >>> Asaadua = (2, 2, 2, 1, 2, 1, 2)
    >>> Sorsonet = (1, 1, 2, 2, 2, 2, 2)
    >>> Bemba = (2, 1, 2, 2, 2, 1, 2)
    >>> Ashanti = (2, 1, 2, 2, 1, 2, 2)
    >>> ten_tuples = (Asaadua, Ashanti, Bemba, Bembé, Bembé_2, Soli, Sorsonet, Tambú, Tonada, Yoruba)

    None has this property.

    >>> [has_oddity_property(x) for x in ten_tuples]
    [True, True, True, True, True, True, True, True, True, True]

    And here's a simple rhythm that does
    >>> has_oddity_property((1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1))
    False

    """
    if not isinstance(vector, (list, tuple)):
        raise TypeError("The `vector` must be a list or tuple.")

    vector_length = len(vector)
    if vector_length % 2 != 0:
        return True  # By definition
    half_length = int(vector_length / 2)

    subsequences = saturated_subsequence_repetition(
        vector, all_rotations=True, subsequence_period=half_length
    )
    return len(subsequences) == 0


def off_beatness(vector: Union[list[int], tuple[int, ...]]) -> int:
    """
    The "off-beatness" measure records the number of events in a rhythmic cycle
    at positions which cannot fall on a regular beat division of the cycle.
    For a more formal definition, see `totatives`.
    Currently, this measures the presence of any item at the given position
    (effectively assuming indicator vector).
    In future, we may add weighting functionality.

    Examples
    --------

    Gomez et al. explore 10 "canonical" 12-unit rhythms of which they find the Bembé notable
    for being "the most frequently used" and because it realizes
    the "highest value of off-beatness" among these 10.

    >>> bembé = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)
    >>> off_beatness(bembé)
    3

    Looking beyond these cases, the true highest value for a 12-unit cycle is 4
    (using indices 1, 5, 7, 11), as shown in the minimal case here:

    >>> off_beatness((0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1))
    4

    """
    t = totatives(len(vector))
    positions = vector_to_multiset(vector)
    count = 0
    for item in t:
        if item in positions:
            count += 1
    return count


def totatives(n):
    """
    Calculates the totatives of n, which are the positive integers less than n
    that are relatively prime to n.

    Parameters
    ----------
    n: A positive integer. In the rhythmic case, this denotes cycle length.

    Returns
    -------
    A list of integers representing the totatives of n.
    This list is empty if n is less than or equal to 1.
    Examples
    --------
    >>> totatives(12)
    [1, 5, 7, 11]

    >>> len(totatives(12))
    4

    >>> totatives(16)
    [1, 3, 5, 7, 9, 11, 13, 15]

    >>> len(totatives(16))
    8

    """

    if n <= 1:
        return []

    totatives_list = []
    for i in range(1, n):
        if gcd(n, i) == 1:
            totatives_list.append(i)
    return totatives_list


def gcd(a, b):
    """
    Calculates the greatest common divisor (GCD) of two integers using the
    Euclidean algorithm.

    TODO we should have this once centrally.
    """
    while b:
        a, b = b, a % b
    return a


def vector_to_onset_beat(
    vector: Union[list[int], tuple[int, ...]], beat_unit_length: int = 2
) -> tuple:
    """
    Map from a vector to onset beat data via `vector_to_multiset`.

    Examples
    --------
    >>> son = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1]  # Final 1 for cycle rotation
    >>> vector_to_onset_beat(vector=son, beat_unit_length=4)
    (Fraction(0, 1), Fraction(3, 4), Fraction(3, 2), Fraction(5, 2), Fraction(3, 1), Fraction(4, 1))

    """
    onsets = vector_to_multiset(
        vector
    )  # Or equivalently [i for i, count in enumerate(vector) for _ in range(count)]
    return tuple(Fraction(x, beat_unit_length) for x in onsets)


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
