# coding: utf-8
"""
Basic, shared functionality for sets and vectors.
We aim for clear and consistent use of "set" and "vector" in  naming and documentation,
though we tend to use basic classes such as lists in preference over the Python multiset class, for instance.

Argument names are "set" or "vector" where that is the clear expectation and reason for the function.
Where the function could be more widely applied, arguments are named `input_list`.
"""

from __future__ import annotations

__author__ = "Mark Gotham"


def set_to_vector(
    input_set: list[int] | tuple[int],
    min_index: int | None = 0,
    max_index: int | None = 6,
) -> tuple:
    """
    Converts any "set" (list of integers) into a "vector" (count of integers organised by index).
    See the paper for full definitions.
    This is similar to the collections.Counter function, simply returning an ordered list instead of a dict.

    Parameters
    ----------
    input_set: The input integers.
    min_index: The minimum index to use. Defaults to 0. Use 1 for interval vectors, to exlcude 0.
    max_index: The maximum index to use. Defaults to 6 for interval vectors.

    Returns
    -------
    tuple: The corresponding vector.

    Examples
    --------
    >>> test_set = [1, 2, 3]
    >>> set_to_vector(test_set, min_index=0, max_index=6)
    (0, 1, 1, 1, 0, 0, 0)

    >>> set_to_vector(test_set, min_index=1, max_index=6)
    (1, 1, 1, 0, 0, 0)

    >>> set_to_vector(test_set, max_index=None)
    (0, 1, 1, 1)

    """
    if not max_index:
        max_index = max(input_set)
    counts = [0] * (max_index + 1)
    for item in input_set:
        counts[item] += 1

    if min_index > 0:
        counts = counts[min_index:]

    return tuple(counts)


def vector_to_set(vector: list[int] | tuple[int]) -> tuple:
    """
    Converts any "vector" (count of integers organised by index)
    to a corresponding "set" (unordered list of integers).
    See the paper for full definitions.

    Parameters
    ----------
    vector: The input vector.

    Returns
    -------
    tuple: The corresponding set.

    Examples
    --------
    >>> test_vector = (0, 3, 2, 1, 0, 0, 0)
    >>> resulting_set = vector_to_set(test_vector)
    >>> resulting_set
    (1, 1, 1, 2, 2, 3)

    >>> roundtrip = set_to_vector(resulting_set, max_index=6)
    >>> roundtrip
    (0, 3, 2, 1, 0, 0, 0)

    >>> roundtrip == test_vector
    True

    """
    return tuple(i for i in range(len(vector)) for _ in range(vector[i]))


# Arithmetic operations: Addition/subtraction, multiplication,division


def apply_constant(
    set_or_vector: list[int] | tuple[int], constant: float, modulo: int | None = None
) -> list | tuple:
    """
    Apply a constant value to a set or vector.

    Parameters
    ----------
    set_or_vector: Any list or tuple representing a set or vector.
    constant: The constant may be an int or a float and positive or negative.
    modulo: Int or `None`. If int, return the values modulo this value (e.g., 12 for pitch class sets)

    Returns
    -------
    list | tuple: The set or vector with constant applied.

    Examples
    --------

    >>> start = [0, 1, 2, 3, 11]
    >>> more = apply_constant(start, 1)
    >>> more
    [1, 2, 3, 4, 12]

    >>> less = apply_constant(more, -1)
    >>> less
    [0, 1, 2, 3, 11]

    >>> start == less
    True

    >>> more = apply_constant(start, 1, modulo=12)
    >>> more
    [1, 2, 3, 4, 0]
    """
    result = [x + constant for x in set_or_vector]
    if modulo is not None:
        result = [x % modulo for x in result]
    return result


def scalar_multiply(input_list: list, scale_factor: int = 2) -> list:
    """
    Multiply all values of a list.

    Parameters
    ----------
    input_list: Any list.
    scale_factor: The "scale factor" aka "multiplicative operand". Multiply all terms by this amount. Defaults to 2.

    >>> scalar_multiply([0, 1, 2])
    [0, 2, 4]

    """
    return [
        x * scale_factor for x in input_list
    ]  # TODO np would be better in cases like this


# Transformations


def rotate(vector: list[int] | tuple[int], steps: int | None = None) -> list:
    """
    Rotate a list by N steps.
    This serves equivalently for
    "phase shifting" of rhythm and
    "transposition" of pitch.

    Parameters
    ----------
    vector: Any list of any elements. We expect to work with a list integers representing a vector.
    steps: how many steps to rotate.
        Or, equivalently, the nth index of the input list becomes the 0th index of the new.
        If unspecified, use the half cycle: int(<cycle lenth>/2).

    Returns
    -------
    list | tuple: The input (list or tuple), rotated. Same length.

    Examples
    --------

    >>> start = [0, 1, 2, 3]
    >>> rotate(start, 1)
    [1, 2, 3, 0]

    >>> rotate(start, -1)
    [3, 0, 1, 2]

    >>> rotate([0, 1, 2, 3])  # note no steps specified
    [2, 3, 0, 1]

    """
    if not steps:
        steps = int(len(vector) / 2)

    return vector[steps:] + vector[:steps]


def mirror(vector: list | tuple, index_of_symmetry: int | None = None) -> list:
    """
    Reverse a list.

    Parameters
    ----------
    vector: Any list of any elements. We expect to work with a list integers representing a vector.
    index_of_symmetry: Defaults to None, in which case, standard refelction [::-1].
        Alternatively, specify an index to rotate about, e.g., for the reverse function in convolution use 0.
        This is equivalent to mirror and rotation.
        See notes at `rotate`.

    Returns
    -------
    list | tuple: The input (list or tuple), mirrored. Same length.

    Examples
    --------
    >>> test_case = [0, 1, 2, 3, 4, 5]
    >>> mirror(test_case)
    [5, 4, 3, 2, 1, 0]

    >>> mirror(test_case, index_of_symmetry=0)
    [0, 5, 4, 3, 2, 1]

    >>> mirror(test_case, index_of_symmetry=1)
    [1, 0, 5, 4, 3, 2]
    """
    if index_of_symmetry is not None:
        return vector[index_of_symmetry::-1] + vector[-1:index_of_symmetry:-1]
    else:
        return vector[::-1]


def is_indicator_vector(indicator_vector: list | tuple) -> bool:
    """
    Check that a list or tuple is an indicator vector, featuring only 0s and 1s.
    """
    if all(x in (0, 1) for x in indicator_vector):
        return True
    return False


def weighted_to_indicator(weighted_vector: list | tuple, threshold=0.0) -> tuple:
    """
    Converts a weighted vector to an indicator vector.

    Parameters
    ----------
    weighted_vector: A NumPy array representing the weighted vector. TODO consider use of numpy
    threshold:  Values below this threshold will be set to 0.  This handles
    cases where weights might be very small but not exactly zero.

    Returns
    -------
    A NumPy array representing the indicator vector (0s and 1s).

    Examples
    --------
    >>> weighted_vector1 = [0.0, 0.0, 2.0, 0.0]
    >>> weighted_to_indicator(weighted_vector1)
    (0, 0, 1, 0)

    >>> weighted_vector2 = [0.2, 0.0, 1.5, 0.0, 0.01]
    >>> weighted_to_indicator(weighted_vector2)
    (1, 0, 1, 0, 1)

    >>> weighted_to_indicator(weighted_vector2, threshold=0.1)
    (1, 0, 1, 0, 0)
    """
    indicator_vector = []
    for weight in weighted_vector:
        if weight > threshold:
            indicator_vector.append(1)
        else:
            indicator_vector.append(0)
    return tuple(indicator_vector)
    # TODO consider np.where(weighted_vector > threshold, 1, 0)


def complement(indicator_vector: list) -> list:
    """
    Provide the complement of an indicator vector.
    >>> complement([1, 0, 1, 0])
    [0, 1, 0, 1]
    """
    if not is_indicator_vector(indicator_vector):
        raise ValueError(
            "This is to be called only on binary lists (indicator vectors)."
        )
    return [1 - x for x in indicator_vector]


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
