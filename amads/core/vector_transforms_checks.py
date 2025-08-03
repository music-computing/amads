"""
Shared functionality for basic operations on vectors
(applicable to more than one musical parameter).
Includes
transformations (e.g., `rotate`) and
checks (e.g., `is_rotation_equivalent`) on vectors.
"""

__author__ = "Mark Gotham"

from collections import Counter
from itertools import combinations
from typing import Optional, Union

from .vectors_sets import is_indicator_vector, vector_to_set

# ----------------------------------------------------------------------------

# Transformations


def rotate(
    vector: Union[tuple[int, ...], list[int]], steps: Union[int, None] = None
) -> list:
    """
    Rotate a vector by N steps.
    This serves equivalently for
    "phase shifting" of rhythm and
    "transposition" of pitch.

    Parameters
    ----------
    vector : Union[tuple[int, ...], list[int]]
        Any tuple or list of any elements.
        We expect to work with a list of integers representing a vector.
    steps: how many steps to rotate.
        Or, equivalently, the nth index of the input list becomes the 0th index of the new.
        If unspecified, use the half cycle: int(<cycle lenth>/2).

    Returns
    -------
    tuple: The input (tuple or list), rotated. Same length.

    Examples
    --------

    >>> start = (0, 1, 2, 3)
    >>> rotate(start, 1)
    (1, 2, 3, 0)

    >>> rotate(start, -1)
    (3, 0, 1, 2)

    >>> rotate(start) # note no steps specified
    (2, 3, 0, 1)

    """
    if not steps:
        steps = int(len(vector) / 2)

    return vector[steps:] + vector[:steps]


def mirror(
    vector: tuple, index_of_symmetry: Union[int, None] = None
) -> Union[list, tuple]:
    """
    Reverse a vector (or any ordered iterable).

    Parameters
    ----------
    vector: tuple
        The tuple accepts any ordered succession of any elements.
        We expect integers representing a vector, but do not enforce it.
    index_of_symmetry: Union[int, None] = None
        Defaults to None, in which case, standard reflection of the form `[::-1]`.
        Alternatively, specify an index to rotate about, e.g., for the reverse function in convolution use 0.
        This is equivalent to mirror and rotation.
        See notes at `rotate`.

    Returns
    -------
    list, tuple: The input (list or tuple), mirrored. Same length.

    Examples
    --------
    >>> test_case = (0, 1, 2, 3, 4, 5)
    >>> mirror(test_case)
    (5, 4, 3, 2, 1, 0)

    >>> mirror(test_case, index_of_symmetry=0)
    (0, 5, 4, 3, 2, 1)

    >>> mirror(test_case, index_of_symmetry=1)
    (1, 0, 5, 4, 3, 2)

    """
    if index_of_symmetry is not None:
        rotated = vector[index_of_symmetry::-1] + vector[-1:index_of_symmetry:-1]
    else:
        rotated = vector[::-1]
    return tuple(rotated)


def complement(indicator_vector: tuple[int, ...]) -> tuple:
    """
    Provide the complement of an indicator vector.
    >>> complement((1, 0, 1, 0))
    (0, 1, 0, 1)
    """
    if not is_indicator_vector(indicator_vector):
        raise ValueError(
            "This is to be called only on binary tuples representing indicator vectors."
        )
    return tuple(1 - x for x in indicator_vector)


# ----------------------------------------------------------------------------

# Checks


def is_rotation_equivalent(vector_a: tuple, vector_b: tuple) -> bool:
    """
    Given two vectors, test for rotation equivalence.

    Examples
    --------
    >>> is_rotation_equivalent((1, 0, 0), (0, 1, 0))
    True

    >>> is_rotation_equivalent((1, 0, 0), (1, 1, 0))
    False
    """
    vector_length = len(vector_a)
    if len(vector_b) != vector_length:
        raise ValueError(
            f"The vectors msy be of the same length (currently {vector_length} and {len(vector_b)}."
        )

    for steps in range(vector_length):
        if vector_a == rotate(vector_b, steps):
            return True

    return False


def is_maximally_even(indicator_vector: tuple) -> bool:
    """
    Checks if an indicator vector (tuple of 0s and 1s) is maximally even,
    meaning the 1s and 0s are as evenly distributed as possible.

    Specifically, this works simply by converting to intervals and running the following basic checks:
    First, there must be no more than 2 interval types.
    If there is only 1 type, True (perfectly even).
    If there are 2 types, then those two must differ in value by 1.

    Parameters
    ----------
    indicator_vector (tuple of ints): An indicator_vector (only 0s and/or 1s).

    Returns
    -------
    bool: True if the pattern is maximally even, False otherwise.

    Examples
    --------

    >>> is_maximally_even((1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0))
    True
    >>> is_maximally_even((1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0))
    False
    >>> is_maximally_even((0, 0, 1, 0, 0, 1, 0, 0, 1))
    True
    >>> is_maximally_even((1, 1, 0, 0, 1))
    False
    >>> is_maximally_even((0, 1, 0, 1, 0, 1))
    True
    """
    if not is_indicator_vector(indicator_vector):
        raise ValueError(
            f"The `indicator_vector` argument (set as {indicator_vector}) should be an indicator vector."
        )

    interval_pattern = indices_to_interval(indicator_vector)
    interval_pattern_counter = Counter(interval_pattern)

    if len(interval_pattern_counter) > 2:
        return False
    elif len(interval_pattern_counter) == 1:
        return True
    else:  # len(interval_pattern_counter) == 2: # Cannot be 0 or negenative.
        intervals = list(interval_pattern_counter.keys())
        if abs(intervals[0] - intervals[1]) == 1:
            return True
        else:
            return False


# ----------------------------------------------------------------------------

# Other


def rotation_distinct_patterns(vector_patterns: tuple[tuple, ...]) -> tuple[tuple, ...]:
    """
    Given two or more vectors of the same length,
    test rotation equivalence among them.
    Return the list of rotation distinct pattens:
    the returned patterns are not rotation equivalent to each other,
    but all tested rhythms (in the argument) are rotation equivalent to one of those returned patterns.

    Examples
    --------
    Here are ten canonical 12-unit bell pattern rhythms:

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

    Collectively, they have 3 distinct patterns.

    >>> len(rotation_distinct_patterns(ten_tuples))
    3

    """
    return_values = [vector_patterns[0]]  # At least one
    for index in range(1, len(vector_patterns)):
        for prototype in return_values:
            if is_rotation_equivalent(prototype, vector_patterns[index]):
                return_values.append(vector_patterns[index])
                break

    return tuple(return_values)


def indicator_to_indices(
    vector: Union[list[int], tuple[int, ...]], wrap: bool = False
) -> tuple:
    """
    Simple mapping from an indicator vector for where events fall,
    to a tuple of the corresponding indices.

    Examples
    --------
    >>> bembé = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1) # adjacent only
    >>> indicator_to_indices(bembé)
    (0, 2, 4, 5, 7, 9, 11)

    >>> indicator_to_indices(bembé, wrap=True)
    (0, 2, 4, 5, 7, 9, 11, 12)

    >>> shiko = (1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0) # adjacent only
    >>> indicator_to_indices(shiko)
    (0, 4, 6, 10, 12)

    >>> indicator_to_indices(shiko, wrap=True)
    (0, 4, 6, 10, 12, 16)

    """
    if wrap:
        vector += (vector[0],)

    set_as_list = list(vector_to_set(vector))
    set_as_list.sort()
    return tuple(set_as_list)


def indices_to_interval(
    vector: Union[list[int], tuple[int, ...]],
    wrap: bool = True,
    adjacent_not_all: bool = True,
    sequence_not_vector: bool = True,
) -> tuple:
    """
    Given a vector (assumed to be indicator)
    convert from 1/0 at each index to the intervals between the 1s.

    Parameters
    ----------
    vector: an indicator vector for position usage.
    wrap: wrap the cycle, duplicating the first element at the end to include that interval.
    adjacent_not_all: intervals between pais of adjacent elements in the sequencs or between all pairs.
    sequence_not_vector:
        In the case of adjacent intervals, express the result as an interval sequence,
        or as an interval vector.
        (No such option in the ase of all intervals: hat must be a vector).

    Examples
    --------

    Example 1:
    >>> bembé = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)

     Adjacent intervals expressed as a sequence:
    >>> indices_to_interval(bembé)
    (2, 2, 1, 2, 2, 2, 1)

    Adjacent intervals expressed as an interval vector:
    >>> indices_to_interval(bembé, sequence_not_vector=False)
    (2, 5, 0, 0, 0, 0)

    All distances (not just the adjacent pairs), which is necessarily expressed as an interval vector:
    >>> indices_to_interval(bembé, adjacent_not_all=False)
    (2, 5, 4, 3, 6, 1)

    Example 2:
    >>> shiko = (1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0)

    Adjacent intervals expressed as a sequence:
    >>> indices_to_interval(shiko)
    (4, 2, 4, 2, 4)

    Adjacent intervals expressed as an interval vector:
    >>> indices_to_interval(shiko, sequence_not_vector=False)
    (0, 2, 0, 3, 0, 0, 0, 0)

    All distances (not just the adjacent pairs), which is necessarily expressed as an interval vector:
    >>> indices_to_interval(shiko, adjacent_not_all=False)
    (0, 2, 0, 3, 0, 4, 0, 1)

    """
    if adjacent_not_all and wrap:
        vector += (vector[0],)  # TODO DRY

    indices = indicator_to_indices(vector)

    if adjacent_not_all:
        sequence = tuple([indices[i + 1] - indices[i] for i in range(len(indices) - 1)])
        if sequence_not_vector:
            return sequence
        else:
            ics = sequence
    else:  # all
        ics = [p[1] - p[0] for p in combinations(indices, 2)]

    vector_length = len(vector)
    half_vector_length = int(vector_length / 2)
    interval_vector = [0] * half_vector_length

    for ic in ics:
        if ic < 0:
            ic *= -1
        if ic > half_vector_length:
            ic = vector_length - ic
        interval_vector[ic - 1] += 1
    return tuple(interval_vector)


def saturated_subsequence_repetition(
    sequence: Union[list[int], tuple[int, ...]],
    all_rotations: bool = True,
    subsequence_period: Optional[int] = None,
):
    """
    Check if a sequence contains a repeated subsequence such that
    the subsequence saturates the whole (no sequence items "left over").
    This is broadly equivalent to a "periodic sequence", with the additional constraint of saturatation.

    This property is a wrapper for an abstraction provided at `vectors_sets.saturated_sublist_repetition`

    Parameters
    ----------
    sequence: A vector for event positions in the cycle time span.
    all_rotations: If True, check all rotations of the sequence.
    subsequence_period: If specified, check only that period length. Otherwise check all factors of n.

    Returns
    -------
    If there is a repeated sub-rhythm, that is returned (the first, longest one found). None otherwise.

    Examples
    --------

    >>> test_sequence = [1, 2, 1, 2, 1, 2, 1, 2]

    All rotations, all subsequence lengths:

    >>> saturated_subsequence_repetition(test_sequence, all_rotations=True)
    [[1, 2], [2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]

    No rotations, all subsequence lengths:

    >>> saturated_subsequence_repetition(test_sequence, all_rotations=False)
    [[1, 2], [1, 2, 1, 2]]

    All rotations, subsequence length fixed at 2:

    >>> saturated_subsequence_repetition(test_sequence, subsequence_period=2, all_rotations=True)
    [[1, 2], [2, 1]]

    All rotations, subsequence length fixed at 4:

    >>> saturated_subsequence_repetition(test_sequence, subsequence_period=4, all_rotations=True)
    [[1, 2, 1, 2], [2, 1, 2, 1]]

    No rotations, subsequence length fixed at 2:
    >>> saturated_subsequence_repetition(test_sequence, subsequence_period=2, all_rotations=False)
    [[1, 2]]

    No rotations, subsequence length fixed at 4:
    >>> saturated_subsequence_repetition(test_sequence, subsequence_period=4, all_rotations=False)
    [[1, 2, 1, 2]]

    """
    subsequence_periods = []
    subsequences = []

    if subsequence_period is None:
        for length in range(1, len(sequence) // 2 + 1):
            if len(sequence) % length == 0:  # Valid divisor
                subsequence_periods.append(length)
    else:
        subsequence_periods = [subsequence_period]

    for period in subsequence_periods:
        subsequence = sequence[:period]
        if subsequence not in subsequences:
            if all(
                sequence[i : i + period] == subsequence
                for i in range(0, len(sequence), period)
            ):
                subsequences.append(subsequence)

        if all_rotations:
            for i in range(
                1, period
            ):  # sic, from 1 (0 is done) and only up to the length of the subsequence
                this_sequence = rotate(sequence, i)
                subsequence = this_sequence[:period]
                if subsequence not in subsequences:
                    if all(
                        this_sequence[i : i + period] == subsequence
                        for i in range(0, len(this_sequence), period)
                    ):
                        subsequences.append(subsequence)

    return subsequences


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
