"""
Shared functionality for basic transformation operations on vectors
(applicable to more than one musical parameter).
Includes
transformations (e.g., `rotate`)
checks (e.g., `is_rotation_equivalent`), and
generator (e.g., `rotation_distinct_patterns`)
on vectors.

While there's a case for moving some of these to vectors_sets,
the contents here (and there) helps avoids circular dependencies.

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"

from itertools import combinations
from typing import Optional, Sequence, Union

from amads.core.vectors_sets import (
    is_indicator_vector,
    multiset_to_vector,
    pairwise_differences,
)

# ----------------------------------------------------------------------------

# Transformations


def rotate(
    vector: Union[tuple[int, ...], list[int]], steps: Union[int, None] = None
) -> Union[tuple[int, ...], list[int]]:
    """
    this serves equivalently for
    "phase shifting" of rhythm and
    "transposition" of pitch.

    Parameters
    ----------
    vector : Union[tuple[int, ...], list[int]]
        Any tuple or list of any elements.
        We expect to work with a list of integers representing a vector.
    steps: Optional[int]
        How many steps to rotate.
        Or, equivalently, the nth index of the input list becomes the 0th index of the new.
        If unspecified, use the half cycle: int(cycle_length / 2).

    Returns
    -------
    Union[tuple[int, ...], list[int]]
        The input (tuple or list), rotated. Same length.

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
    if steps is None:
        steps = int(len(vector) / 2)

    return vector[steps:] + vector[:steps]


def mirror(
    vector: Sequence, index_of_symmetry: Union[int, None] = None
) -> Sequence:
    """
    Reverse a vector (or any ordered iterable).

    Parameters
    ----------
    vector: Sequence
        Any ordered succession of any elements.
        We expect integers representing a vector, but do not enforce it.
    index_of_symmetry: Union[int, None]
        Defaults to None, in which case, standard reflection of the
        form `[::-1]`. Alternatively, specify an index to rotate about,
        e.g., for the reverse function in convolution use 0. This is
        equivalent to mirror and rotation. See notes at [`rotate`]
        [amads.core.vector_transforms_checks.rotate].

    Returns
    -------
    Sequence
        The input (tuple, list, etc.), mirrored. Same length, but return is always a tuple.

    Examples
    --------
    >>> test_case = (0, 1, 2, 3, 4, 5)
    >>> mirror(test_case)
    (5, 4, 3, 2, 1, 0)

    >>> mirror(test_case, index_of_symmetry=0)
    (0, 5, 4, 3, 2, 1)

    >>> mirror(test_case, index_of_symmetry=1)
    (1, 0, 5, 4, 3, 2)

    We will often use this for a 12-element indicator vector.
    >>> c_vector = (1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0)
    >>> mirror(c_vector, index_of_symmetry=0)
    (1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0)

    """
    if index_of_symmetry is not None:
        return vector[index_of_symmetry::-1] + vector[-1:index_of_symmetry:-1]
    else:
        return vector[::-1]


def complement(indicator_vector: tuple[int, ...]) -> tuple[int, ...]:
    """
    Provide the complement of an indicator vector.

    Returns
    -------
    tuple[int]

    Examples
    --------
    >>> complement((1, 0, 1, 0))
    (0, 1, 0, 1)
    """
    if not is_indicator_vector(indicator_vector):
        raise ValueError(
            "This is to be called only on binary tuples representing indicator vectors."
        )
    return tuple(1 - x for x in indicator_vector)


def change_cycle_length(
    start_vector: tuple,
    destination_length: int,
    return_indices_not_indicator: bool = True,
) -> tuple:
    """
    Change the cycle length of a vector by mapping each point to the nearest equivalent in the new length.

    Examples
    --------
    >>> tresillo = (1, 0, 0, 1, 0, 0, 1, 0)
    >>> change_cycle_length(tresillo, 9)
    (0, 3, 7)

    >>> change_cycle_length(tresillo, 12)
    (0, 4, 9)

    >>> change_cycle_length(start_vector=tresillo, destination_length=9,
    ...                     return_indices_not_indicator=False)
    (1, 0, 0, 1, 0, 0, 0, 1, 0)

    """
    start_indices = indicator_to_indices(start_vector)
    start_len = len(start_vector)
    new_indices = [
        round(destination_length * i / start_len) for i in start_indices
    ]
    if return_indices_not_indicator:
        return tuple(new_indices)
    else:
        return indices_to_indicator(
            new_indices, indicator_length=destination_length
        )


def convolve(
    vector_1: Sequence, vector_2: Sequence, return_indicator: bool = False
) -> tuple:
    """
    Convolution combines two vectors,
    with a scalar product of corresponding entries
    where they are rotated relative to one another by k steps.

    Parameters
    ----------
    vector_1: Sequence
        A vector of numeric values.
    vector_2: Sequence
        Another vector of numeric values, must be the same length as `vector_1` (otherwise, raises).
    return_indicator: bool
        If True, return an indicator vector (only 1s and 0s).

    Returns
    -------
    tuple
        The convolution of the two input vectors.
        If `return_indicator` is True, values are reduced to 1s and 0s.

    Examples
    --------
    This function is agnostic wrt musical parameter;
    the following example as applied to pitch is illustrative.

    >>> c_major_triad = (1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0)
    >>> min_7_dyad = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0)
    >>> convolve(c_major_triad, min_7_dyad)
    (1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0)

    """
    number_elements = len(vector_1)
    if len(vector_2) != number_elements:
        raise ValueError(
            "The lengths of two vectors must match. "
            f"Currently {vector_1} ({number_elements}) "
            f"and {vector_2} ({len(vector_2)})."
        )

    combined_list = []
    for k in range(number_elements):
        combined_list.append(
            sum(
                vector_1[i] * vector_2[(k - i) % number_elements]
                for i in range(number_elements)
            )
        )

    if return_indicator:
        combined_list = [1 if x > 0 else 0 for x in combined_list]
    return tuple(combined_list)


def interval_function(
    vector_1: Sequence[int],
    vector_2: Sequence[int],
    return_vector: bool = True,
) -> tuple[int, ...]:
    """
    All directed intervals between two vectors.
    The interval _function_ was introduced to music theory by Lewin, 2001 [1]

    [1] David Lewin, Special Cases of the Interval Function between Pitch-Class Sets X and Y,
    Journal of Music Theory (2001) 45 (1): 1–29. https://doi.org/10.2307/3090647

    Parameters
    ----------
    vector_1: Sequence[int]
        A sequence representing a starting condition.
    vector_2: Sequence[int]
        A sequence representing a following condition.
    return_vector: bool
        If True (default), return a count vector indexed by interval size
        (length ``max_interval + 1``).
        If False, return the raw multiset of directed intervals mod 12.

    Returns
    -------
    tuple[int, ...]
        If ``return_vector`` is True, a 13-element tuple where index ``i``
        is the count of directed interval ``i`` (mod 12) from ``vector_1``
        to ``vector_2``.
        If ``return_vector`` is False, the raw multiset of directed intervals.

    Examples
    --------
    >>> start_set = [1, 2, 6]
    >>> end_set = [1, 5, 7]

    With `return_vector=False` we get the pairwise differences as a set multiset of intervals in the range 0–12.
    >>> interval_function(start_set, end_set, return_vector=False)
    (0, 4, 6, 11, 3, 5, 7, 11, 1)

    With `return_vector=True` we get an interval vector with usage per position (/interval).
    For example, note that we have two instance of interval 11 in the above.
    >>> interval_function(start_set, end_set, return_vector=True)
    (1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 2)

    """
    differences = pairwise_differences(vector_1, vector_2, modulo=12)

    if return_vector:
        differences = multiset_to_vector(differences, max_index=11)

    return tuple(differences)


# ----------------------------------------------------------------------------

# Checks


def is_rotation_equivalent(a: tuple, b: tuple) -> bool:
    """
    Test for rotation equivalence.
    This is applicable to indicator vectors, interval sequences, and more
    (any tuple, list, or even string).

    Examples
    --------

    Indicator:

    >>> is_rotation_equivalent((1, 0, 0), (0, 1, 0))
    True

    >>> is_rotation_equivalent((1, 0, 0), (1, 1, 0))
    False

    Intervals:

    >>> is_rotation_equivalent((3, 3, 2), (3, 2, 3))
    True

    >>> is_rotation_equivalent((3, 3, 2), (2, 3, 2))
    False

    Trivial case:
    >>> is_rotation_equivalent((1, 0, 0), (1, 0, 0))
    True

    """
    if len(a) != len(b):
        raise ValueError("The vectors must be of the same length.")

    doubled = b + b
    return len(a) == 0 or any(
        doubled[i : i + len(a)] == a for i in range(len(b))
    )


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
    indicator_vector: tuple[int, ...]
        An indicator_vector (only 0s and/or 1s).

    Returns
    -------
    bool
        True if the pattern is maximally even, False otherwise.

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

    This works with the `indicator_to_interval` function.
    Let's look at those representations for the bembé cycle and a comparison case.

    >>> bembé = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)
    >>> indicator_to_interval(bembé, adjacent_not_all=True)
    (2, 2, 1, 2, 2, 2, 1)

    >>> indicator_to_interval(bembé, adjacent_not_all=True, sequence_not_vector=False)
    (2, 5, 0, 0, 0, 0)

    >>> indicator_to_interval(bembé, adjacent_not_all=False)
    (2, 5, 4, 3, 6, 1)

    >>> is_maximally_even(bembé)
    True

    For our comparison case, we create another cycle that also has:
    a) 7 elements in a 12-unit cycle,

    >>> not_bembé =  (1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1)
    >>> not_bembé.count(1)
    7

    >>> len(not_bembé)
    12

    b) the same first-order interval set of 5 x 2s and 2 x 1s,

    >>> indicator_to_interval(not_bembé, adjacent_not_all=True, sequence_not_vector=False)
    (2, 5, 0, 0, 0, 0)

    ... but for which the those 2 x 1s are together

    >>> indicator_to_interval(not_bembé, adjacent_not_all=True)
    (2, 2, 2, 2, 2, 1, 1)

    ... making it not maximally even.

    >>> is_maximally_even(not_bembé)
    False

    """
    if not is_indicator_vector(indicator_vector):
        raise ValueError(
            f"The `indicator_vector` argument (set as {indicator_vector}) should be an indicator vector."
        )

    k = indicator_vector.count(1)
    n = len(indicator_vector)

    prototype_k_in_n = indices_to_indicator(tuple(max_even_k_in_n(k, n)), n)

    return is_rotation_equivalent(prototype_k_in_n, indicator_vector)


def is_monotonic(
    numbers: Sequence,
    diagnose: bool = True,
) -> bool:
    """
    Assert that a list of numbers is monotonically increasing.
    Returns True if so, raises ValueError at the first failure point.

    Please note that edge case behaviour (e.g., 0, None, raises) may change.

    Parameters
    ----------
    numbers: A sequence (list, tuple, ...) of numeric values (integers, floats, ...).
    diagnose: bool.
        If True, raises a ValueError at the point of failure rather than returning False,
        enabling diagnosis of where the sequence breaks.
        If diagnose is False, simply return a bool in all cases.

    Examples
    --------
    >>> is_monotonic([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    True
    >>> is_monotonic([1, 2, 3, 4, 5, 7, 6, 8, 9, 10])
    Traceback (most recent call last):
    ValueError: Data must be monotonically increasing: value 6 at index 6 is not greater than the previous entry 7.

    >>> is_monotonic([1, 2, 3, 4, 5, 7, 6, 8, 9, 10], diagnose=False)
    False
    """
    if diagnose:
        for i in range(len(numbers) - 1):
            if numbers[i] >= numbers[i + 1]:
                raise ValueError(
                    "Data must be monotonically increasing: value "
                    f"{numbers[i + 1]} at index {i + 1} is not greater than the previous entry {numbers[i]}."
                )
        return True
    else:
        return all(a < b for a, b in zip(numbers, numbers[1:]))


# ------------------------------------------------------------------------

# Generators


def max_even_k_in_n(k: int, n: int) -> set[int]:
    """
    Make a maximally even pattern of k elements in an n-length cycle.
    Normally, we would expect k to be less than n, but this is not strictly required.
    Larger values of k simply produce duplicate entries in n that are ignored in the
    returned set.

    Examples
    --------
    >>> max_even_k_in_n(3, 8)
    {0, 3, 5}

    >>> max_even_k_in_n(7, 12)
    {0, 2, 3, 5, 7, 9, 10}

    >>> max_even_k_in_n(5, 16)
    {0, 3, 6, 10, 13}

    """
    return set([round(n * i / k) for i in range(k)])


def rotation_distinct_patterns(
    vector_patterns: tuple[tuple, ...]
) -> tuple[tuple, ...]:
    """
    Given two or more vectors of the same length,
    test rotation equivalence among them.
    Return the list of rotation distinct pattens:
    the returned patterns are not rotation equivalent to each other,
    but all tested rhythms (in the argument) are rotation equivalent
    to one of those returned patterns.

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
                break
        else:
            return_values.append(vector_patterns[index])

    return tuple(return_values)


# ----------------------------------------------------------------------------

# Candidates for vectors_sets?


def indicator_to_indices(
    vector: Union[list[int], tuple[int, ...]], wrap: bool = False
) -> tuple:
    """
    Simple mapping from an indicator vector for where events fall,
    to a tuple of the corresponding indices.

    Parameters
    ----------
    vector: Union[list[int], tuple[int, ...]]
        an indicator vector

    wrap: bool
        if true, the first element of `vector` is appended to `vector`
        before computing indices, so if the element is non-zero, the
        length of `vector` will appear in the result.

    Returns
    -------
    tuple[int, ...]
        a tuple containing the indices for which `vector` is non-zero.

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
        vector = vector + vector[:1]

    return tuple(i for i, v in enumerate(vector) if v)


def indices_to_indicator(
    indices_vector: Union[list[int], tuple[int, ...]],
    indicator_length: Optional[int] = None,
) -> tuple:
    """
    Simple mapping from indices to indicator vector.

    Parameters
    ----------
    indices_vector: Union[list[int], tuple[int, ...]]
        A vector of indices (0, 2, 4, 5, 7, 9, 11).
        Monotonic increase is expected but not required.
    indicator_length: Optional[int]
        optionally specify the length of the output indicator vector.
        If not specified, we use the highest index in the indices vector.

    Examples
    --------
    Round trip
    >>> bembé = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)
    >>> indices = indicator_to_indices(bembé)
    >>> indices
    (0, 2, 4, 5, 7, 9, 11)

    No `indicator_length` is needed for default

    >>> round_trip = indices_to_indicator(indices)
    >>> round_trip
    (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)

    >>> round_trip == bembé
    True

    The `indicator_length` can, however, be specified:
    >>> indices_to_indicator(indices, indicator_length=12)
    (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)

    And the `indicator_length` can extend the indicator as needed:
    >>> indices_to_indicator(indices, indicator_length=14)
    (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0)

    """
    if indicator_length is None:
        indicator_length = max(indices_vector) + 1
    index_set = set(indices_vector)
    return tuple(1 if i in index_set else 0 for i in range(indicator_length))


def indicator_to_interval(
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
    vector: Union[list[int], tuple[int, ...]]
        an indicator vector representing positions.
    wrap: bool
        wrap the cycle, duplicating the first element at the end to include
        that (possible) interval.
    adjacent_not_all: bool
        If True, form the set of intervals between pairs of adjacent positions.
        If False, form the set of intervals between all pairs.
    sequence_not_vector: bool
        In the case of adjacent intervals, True means express the result as an
        interval sequence, and False means compute an interval vector containing
        the counts of intervals of size 1, 2, 3, etc. If `adjacent_not_all` is
        False (meaning all pairs), the result is always an interval vector.

    Examples
    --------
    Example 1:
    >>> bembé = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)

    Adjacent intervals expressed as a sequence:
    >>> indicator_to_interval(bembé)
    (2, 2, 1, 2, 2, 2, 1)

    Wrap is optional:
    >>> indicator_to_interval(bembé, wrap=False)
    (2, 2, 1, 2, 2, 2)

    Adjacent intervals expressed as an interval vector:
    >>> indicator_to_interval(bembé, sequence_not_vector=False)
    (2, 5, 0, 0, 0, 0)

    All distances (not just the adjacent pairs), which is necessarily
    expressed as an interval vector:
    >>> indicator_to_interval(bembé, adjacent_not_all=False)
    (2, 5, 4, 3, 6, 1)

    Example 2:
    >>> shiko = (1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0)

    Adjacent intervals expressed as a sequence:
    >>> indicator_to_interval(shiko)
    (4, 2, 4, 2, 4)

    Adjacent intervals expressed as an interval vector:
    >>> indicator_to_interval(shiko, sequence_not_vector=False)
    (0, 2, 0, 3, 0, 0, 0, 0)

    All distances (not just the adjacent pairs), which is necessarily
    expressed as an interval vector:
    >>> indicator_to_interval(shiko, adjacent_not_all=False)
    (0, 2, 0, 3, 0, 4, 0, 1)

    """
    if adjacent_not_all and wrap:
        vector = vector + vector[:1]

    indices = indicator_to_indices(vector)

    if adjacent_not_all:
        sequence = tuple(
            [indices[i + 1] - indices[i] for i in range(len(indices) - 1)]
        )
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


def interval_sequence_to_indices(
    interval_sequence_vector: Union[list[int], tuple[int, ...]],
    wrap: bool = False,
) -> tuple[int, ...]:
    """
    Given an interval sequence vector, convert to indices.

    Parameters
    ----------
    interval_sequence_vector: Union[list[int], tuple[int, ...]]
        a vector of distances (intervals) between adjacent positions
        that are used.
    wrap: bool
        If True, include the index after the end of the sequence

    Returns
    -------
    tuple[int, ...]
        A vector containing the positions (indices) that are used.

    Examples
    --------
    >>> interval_sequence_to_indices((3, 3, 2), wrap=False)  # Default
    (0, 3, 6)

    >>> interval_sequence_to_indices((3, 3, 2), wrap=True)
    (0, 3, 6, 8)

    """
    indices = [0]
    count = 0
    if not wrap:
        interval_sequence_vector = interval_sequence_vector[:-1]
    for i in interval_sequence_vector:
        count += i
        indices.append(count)
    return tuple(indices)


def indices_to_interval_sequence(
    indices: Union[list[int], tuple[int, ...]],
    wrap: bool = True,
    mod: int = 12,
) -> tuple[int, ...]:
    """
    Convert a sequence of indices (any increasing integers, n >= 2)
    into a sequence of the differences, mod 12 (including the difference between the last and the first items)

    Parameters
    ----------
    indices: Union[list[int], tuple[int, ...]]
        A vector containing the positions (indices) that are used.
    wrap: bool
        If True, include the index after the end of the sequence
    mod: int
        The modulo value for use when wrapping around

    Returns
    -------
    tuple[int, ...]
        A vector of distances (intervals) between adjacent positions

    Examples
    --------

    >>> indices_to_interval_sequence([1, 2, 3])
    (1, 1, 10)

    >>> indices_to_interval_sequence([1, 2, 3], wrap=False)
    (1, 1)

    >>> indices_to_interval_sequence([1, 2, 6])
    (1, 4, 7)

    >>> start = (3, 3, 2)
    >>> corresponding_indices = interval_sequence_to_indices(start, wrap=False)  # Default
    >>> corresponding_indices
    (0, 3, 6)

    >>> end = indices_to_interval_sequence(corresponding_indices, mod=8)
    >>> end
    (3, 3, 2)

    >>> start == end
    True

    """
    if len(indices) < 2:
        raise ValueError(
            f"Starting indices have 2 or more items, currently {indices} is of length {len(indices)}."
        )

    is_monotonic(indices)

    diffs = []
    for i in range(len(indices) - 1):
        diffs.append(indices[i + 1] - indices[i])

    if wrap:
        diffs += [(indices[0] - indices[-1]) % mod]

    return tuple(diffs)


def interval_sequence_to_indicator(
    interval_sequence_vector: Union[list[int], tuple[int, ...]]
) -> tuple[int, ...]:
    """
    Given an interval sequence vector, convert to indicator.

    Parameters
    ----------
    interval_sequence_vector: Union[list[int], tuple[int, ...]]
        the sequence of distances (intervals) between adjacent positions
        that are used.

    Returns
    -------
    tuple[int, ...]
        An indicator vector representing all positions, where used
        positions contain the value 1.

    Examples
    --------
    >>> interval_sequence_to_indicator((3, 3, 2))
    (1, 0, 0, 1, 0, 0, 1, 0)

    """
    indices = interval_sequence_to_indices(interval_sequence_vector, wrap=False)
    indicator = indices_to_indicator(
        indices, indicator_length=sum(interval_sequence_vector)
    )
    return tuple(indicator)


def saturated_subsequence_repetition(
    sequence: Union[list[int], tuple[int, ...]],
    all_rotations: bool = True,
    subsequence_period: Optional[int] = None,
) -> list[Union[list[int], tuple[int, ...]]]:
    """
    Check if a sequence contains a repeated subsequence such that
    the subsequence saturates the whole (no sequence items "left over").
    This is broadly equivalent to a "periodic sequence", with the additional
    constraint of saturation.

    Parameters
    ----------
    sequence: Union[list[int], tuple[int, ...]]
        A vector for event positions in the cycle time span.
    all_rotations: bool
        If True, check all rotations of the sequence.
    subsequence_period: Optional[int]
        If specified, check only that period length; otherwise,
        check all factors of n.

    Returns
    -------
    Union[List[List[int]]]
        A list of all subsequences that, if repeated, can form the input
        `sequence`. If `all_rotations`, then also include subsequences
        that can repeat to form any rotations of `sequence`. If
        `sequence` is not periodic, return None.

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

    Tuple input return same values, as list of tuples.

    >>> test_tuple = (1, 2, 1, 2, 1, 2, 1, 2)

    All rotations, all subsequence lengths:

    >>> saturated_subsequence_repetition(test_tuple, all_rotations=True)
    [(1, 2), (2, 1), (1, 2, 1, 2), (2, 1, 2, 1)]

    """
    if subsequence_period is not None:
        subsequence_periods = [subsequence_period]
    else:
        subsequence_periods = [
            length
            for length in range(1, len(sequence) // 2 + 1)
            if len(sequence) % length == 0
        ]

    subsequences = []

    for period in subsequence_periods:
        subsequence = sequence[:period]
        if subsequence not in subsequences:
            if all(
                sequence[i : i + period] == subsequence
                for i in range(0, len(sequence), period)
            ):
                subsequences.append(subsequence)

        if all_rotations:
            for j in range(
                1, period
            ):  # sic, from 1 (0 is done) and only up to the length of the subsequence
                this_sequence = rotate(sequence, j)
                subsequence = this_sequence[:period]
                if subsequence not in subsequences:
                    if all(
                        this_sequence[k : k + period] == subsequence
                        for k in range(0, len(this_sequence), period)
                    ):
                        subsequences.append(subsequence)

    return subsequences


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
