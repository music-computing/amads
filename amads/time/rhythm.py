"""
Basic properties of rhythms, which is to say 1D representations of musical events,
without measures, beats etc., and certainly no scores.

Broadly, this is for stand-alone functions clearly intended for
short, simple representations of rhythmic cycles,
and is not suitable for calling on scores, for instance.

This also includes some measures of rhythmic _complexity_
 (which is clearly not the same as syncopation, but related, and often studied together.
"""

__author__ = "Mark Gotham"

import math
from fractions import Fraction
from typing import Union

from amads.core.vector_transforms_checks import (
    indicator_to_indices,
    indicator_to_interval,
)
from amads.core.vectors_sets import vector_to_multiset


def has_oddity_property(vector: Union[list[int], tuple[int, ...]]) -> bool:
    """
    Given a rhythm cycle (i.e., with the expectation of repetition) as a vector,
    check if it has Arom's "rhythmic-oddity" property:
    no two onsets partition the cycle into two equal parts.
    This is slightly confusing to get the right way around:
    the function returns `True` (i.e., yes, has the property) in the _absence_ of this equal division.

    Parameters
    ----------
    vector: A vector for either the event positions in the cycle time span, or the beat pattern (sic, either).

    Returns
    -------
    True if the rhythm has the rhythmic-oddity property, False otherwise.

    Examples
    --------

    >>> son = (1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0)
    >>> has_oddity_property(son)
    True

    >>> bembé = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)
    >>> has_oddity_property(bembé)
    False

    And here's a simple rhythm that does have the equal division
    >>> has_oddity_property((1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1))
    False

    Note that there does not need to be any further similarity between the two halves:
    >>> has_oddity_property((1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1))
    False

    """
    if not isinstance(vector, (list, tuple)):
        raise TypeError("The `vector` must be a list or tuple.")

    vector_length = len(vector)
    if vector_length % 2 != 0:
        return True  # By definition
    half_length = int(vector_length / 2)

    indices = indicator_to_indices(vector)
    for i in indices:
        opposite = (i + half_length) % vector_length
        if opposite in indices:
            return False

    return True


def keith_via_toussaint(vector):
    """
    Although Keith's measures is described in terms of beats,
    it is inflexible to metric structure and fully defined by the onset pattern.

    >>> son = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]
    >>> keith_via_toussaint(son)
    2

    """
    power = math.log2(len(vector))
    if int(power) != power:
        raise ValueError(
            f"Vector length (currently {len(vector)}) must be a power of 2."
        )

    indices = indicator_to_indices(vector)  # Keith/Toussaint's `S`
    deltas = indicator_to_interval(vector, wrap=True)  # Keith/Toussaint also `delta`
    powers_of_2 = [2 ** int(math.log2(x)) for x in deltas]  # Keith/Toussaint's big D
    count = 0
    for i in range(len(indices)):
        this_case = indices[i] / powers_of_2[i]
        if int(this_case) != this_case:
            count += 1
    return count


def has_deep_property(vector: Union[list[int], tuple[int, ...]]) -> bool:
    """
    So-called "Deep" rhythms have distinct numbers of each interval class among all
    (not-necessarily adjacent) intervals.
    See `indicator_to_interval` with the arguments `wrap=True`, `adjacent_not_all=False`

    Examples
    --------

    >>> shiko = (1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0)
    >>> indicator_to_interval(shiko, wrap=True, adjacent_not_all=False)
    (0, 2, 0, 3, 0, 4, 0, 1)

    Note the distinct numbers in the above.

    >>> has_deep_property(shiko)
    True

    TODO false case

    """
    intervals = indicator_to_interval(vector, wrap=True, adjacent_not_all=False)
    non_zero_uses = [x for x in intervals if x != 0]
    if len(non_zero_uses) == len(set(non_zero_uses)):
        return True
    # TODO consider storing interval vectors as Counter object. Then after the pop:
    # if len(intervals_counter.values()) == len(set(intervals_counter.values())):
    #     return True
    return False


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

    [Note: we may more this to somewhere more central if used beyond rhythm.

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
