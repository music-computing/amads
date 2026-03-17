"""
Functions for retrieving one pitch class set property directly from another.

Most of the retrieval function names are in the form
`<call-on-type>_to_<return-type>`
e.g.
`prime_to_combinatoriality`
Some are simple mappings from one entry to another.
Anything starting with pitches involves more calculation.

Broadly as implemented by Mark Gotham
for [Serial_Analyser](https://github.com/MarkGotham/Serial_Analyser)
after Robert Morris,
but the functions are general
and not really named algorithms in sense used elsewhere on this code base.

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"

from typing import Sequence

from amads.core.vectors_sets import multiset_to_vector, pairwise_differences
from amads.pitch import pc_sets
from amads.pitch import transformations as pitch_list_transformations


def set_classes_from_cardinality(cardinality: int) -> list:
    """
    Find pitch class set data matching given cardinality.

    Parameters
    ----------
    cardinality: int
        The cardinality of the set (2–10 inclusive).

    Returns
    -------
    list
        The pitch class set data for that cardinality.

    Examples
    --------
    >>> set_classes_from_cardinality(2)[0]
    ('2-1', (0, 1), (1, 0, 0, 0, 0, 0), 2)

    """
    if not (1 < cardinality < 11):
        raise ValueError("Invalid cardinality: must be 2-10 (inclusive).")
    return pc_sets.set_classes[cardinality]


def prime_to_combinatoriality(prime: tuple[int, ...]) -> int:
    """
    Find the combinatoriality status for a given prime form.

    Parameters
    ----------
    prime: tuple[int, ...]
        A prime form expressed as a tuple of integers.

    Returns
    -------
    int
        The number of distinct transformations (non-invariant transpositions and / or inversions).

    Examples
    --------
    >>> prime_to_combinatoriality((0, 1, 2, 3))
    12
    """
    data = set_classes_from_cardinality(len(prime))
    for x in data:
        if x[1] == prime:
            return x[3]
    raise ValueError(f"{prime} is not a valid prime form")


def interval_vector_to_combinatoriality(vector: tuple[int, ...]) -> str:
    """
    Find the combinatoriality status for a given interval vector.

    Parameters
    ----------
    vector: tuple[int, ...]
        An interval vector for any set with 2–10 distinct pitches,
        expressed as a tuple of 6 integers.

    Returns
    -------
    str
        The combinatoriality status: one of ``T``, ``I``, ``RI``, ``A``,
        or an empty string for non-combinatorial cases.

    Examples
    --------
    >>> interval_vector_to_combinatoriality((4, 3, 2, 1, 0, 0))  # 5-1
    12
    """
    if len(vector) != 6:
        raise ValueError(f"{vector} is not a valid interval vector")
    total = sum(vector)
    total_to_cardinality = {
        1: 2,
        3: 3,
        6: 4,
        10: 5,
        15: 6,
        21: 7,
        28: 8,
        36: 9,
        45: 10,
    }
    if total not in total_to_cardinality:
        raise ValueError(f"{vector} is not a valid interval vector")
    data = set_classes_from_cardinality(total_to_cardinality[total])
    for x in data:
        if x[2] == vector:
            return x[-1]
    raise ValueError(f"{vector} is not a valid interval vector")


def interval_to_interval_class(interval: int) -> int:
    """
    Map an interval (any integer, positive or negative and any size)
    to an interval class (integer in the range 0–6).

    Parameters
    ----------
    interval: int
        Any integer representing a pitch interval.

    Returns
    -------
    int
        The interval class in the range 0–6.

    Examples
    --------
    >>> interval_to_interval_class(0)
    0

    >>> interval_to_interval_class(-1)
    1

    >>> interval_to_interval_class(-2)
    2

    >>> interval_to_interval_class(11)
    1

    >>> interval_to_interval_class(7)
    5

    >>> interval_to_interval_class(-100)
    4
    """
    reduced = abs(interval) % 12
    return reduced if reduced <= 6 else 12 - reduced


def interval_vector_to_interval_class_vector(
    interval_vector: tuple[int, ...]
) -> tuple[int, ...]:
    """
    Map an interval vector of range(0, 12) to an interval class vector of range(1, 7).

    Parameters
    ----------
    interval_vector: tuple[int, ...]
        A 12-element interval vector.

    Returns
    -------
    tuple[int, ...]
        A 6-element interval class vector.

    Examples
    --------
    >>> interval_vector_to_interval_class_vector((1, 0, 5, 7, 2, 2, 0, 3, 5, 0, 8, 4))
    (4, 13, 7, 7, 5, 0)
    """
    interval_class_vector = [0] * 6
    for i in range(1, 6):
        interval_class_vector[i - 1] = (
            interval_vector[i] + interval_vector[12 - i]
        )
    interval_class_vector[5] = interval_vector[6]  # special case
    return tuple(interval_class_vector)


def pitches_to_combinatoriality(pitches: Sequence[int]) -> str:
    """
    Find the combinatoriality status for a given list of pitches.

    Parameters
    ----------
    pitches: Sequence[int]
        A sequence of integers (0–11) for sets with 2–10 distinct pitches.

    Returns
    -------
    str
        The combinatoriality status as a string.

    Examples
    --------
    >>> pitches_to_combinatoriality((0, 1, 2, 3, 4, 5, 6, 7, 8, 9))
    12
    """
    icv = set_to_interval_vector(pitches)
    return interval_vector_to_combinatoriality(icv)


def distinct_pcs(pitches: Sequence[int]) -> list[int]:
    """
    Find the distinct pitch classes for a given sequence of pitches.

    Parameters
    ----------
    pitches: Sequence[int]
        A sequence of pitches (any integers).

    Returns
    -------
    list[int]
        A list of distinct pitch classes in the range 0–11.

    Examples
    --------
    >>> distinct_pcs((0, 0, 1, 1))
    [0, 1]
    """
    return list({p % 12 for p in pitches})


def set_to_interval_vector(
    user_set: Sequence[int],
) -> tuple[int, ...]:
    """
    Generates the interval vector for a set of pitches:
    the counts of each interval class present between all pairs of elements.

    Parameters
    ----------
    user_set: Sequence[int]
        A sequence of integers representing pitch classes.
        Order does not affect the result.

    Returns
    -------
    tuple[int, ...]
        A tuple of length 6 where index ``i`` contains the count of
        interval class ``i+1`` among all pairs in ``user_set``.

    Examples
    --------
    >>> set_to_interval_vector([1, 3, 4, 6])
    (1, 2, 2, 0, 1, 0)

    >>> set_to_interval_vector([0, 4, 7])  # C major triad
    (0, 0, 1, 1, 1, 0)

    """
    differences = [
        interval_to_interval_class(x) for x in pairwise_differences(user_set)
    ]
    differences = multiset_to_vector(differences, max_index=6)
    return tuple(differences[1:])


def pitches_to_forte_class(pitches: Sequence[int]) -> str:
    """
    Find the Forte class for a given list of pitches.

    Parameters
    ----------
    pitches: Sequence[int]
        A sequence of integers (0–11) for sets with 2–10 distinct pitches.

    Returns
    -------
    str
        The Forte class.

    Examples
    --------
    >>> pitches_to_forte_class((0, 1, 2, 3, 4, 5, 6, 7, 8))
    '9-1'
    """
    data = set_classes_from_cardinality(len(pitches))
    prime = pitches_to_prime(pitches)
    for x in data:
        if x[1] == prime:
            return x[0]
    raise ValueError(f"{pitches} is not a valid entry.")


def pitches_to_prime(pitches: Sequence[int]) -> tuple[int, ...]:
    """
    Find the prime form for a given list of pitches.

    This function first converts the pitches to their interval vector.
    (That step is easy and fast).
    This vector can then unambiguously give the prime form except for Z-related pairs.
    This affects one pair of tetrachords (2 prime forms) and 15 pairs of hexachords (30 primes).
    In those cases, the prime form is worked out by comparing the pitch list against
    the pair of options in both inversions until a match is found.

    Parameters
    ----------
    pitches: Sequence[int]
        A sequence of integers (0–11) for sets with 2–10 distinct pitches.

    Returns
    -------
    tuple[int, ...]
        The prime form.

    Examples
    --------
    >>> pitches_to_prime((9, 0, 1, 2, 3, 4, 5, 6, 7, 8))
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    """
    pitches = distinct_pcs(pitches)
    vector = set_to_interval_vector(pitches)
    data = set_classes_from_cardinality(len(pitches))

    primes = [x[1] for x in data if x[2] == vector]

    if len(primes) == 1:
        return primes[0]
    elif len(primes) > 1:
        for prime in primes:
            inverted = pitch_list_transformations.invert(prime)
            for t in [prime, inverted]:
                if transposition_equivalent(t, pitches):
                    return prime
    raise ValueError(f"{pitches} did not match any prime form.")


def transposition_equivalent(
    set1: Sequence[int],
    set2: Sequence[int],
) -> bool:
    """
    Determine whether two pitch class sets are transposition equivalent.

    Parameters
    ----------
    set1: Sequence[int]
        A pitch class set as a sequence of integers (0–11).
    set2: Sequence[int]
        A pitch class set as a sequence of integers (0–11).

    Returns
    -------
    bool
        True if the two sets are transposition equivalent, False otherwise.

    Examples
    --------

    Meaningully True:
    >>> transposition_equivalent((0, 1, 2, 3, 4, 5, 6, 7, 8), (1, 2, 3, 4, 5, 6, 7, 8, 9))
    True

    Trivially True:
    >>> transposition_equivalent((0, 1, 2, 3, 4, 5, 6, 7, 8), (0, 1, 2, 3, 4, 5, 6, 7, 8))
    True

    False:
    >>> transposition_equivalent((0, 1, 2, 3, 4, 5, 6, 7, 8), (0, 1, 2, 3, 4, 5, 6, 7))
    False

    """
    sorted_set2 = sorted(set2)
    for i in range(12):
        if (
            sorted(pitch_list_transformations.transpose_by(set1, i))
            == sorted_set2
        ):
            return True
    return False


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
