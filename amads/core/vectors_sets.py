# coding: utf-8
"""
Basic, shared functionality for sets and vectors.
We aim for clear and consistent use of "set" and "vector" in naming and documentation.
We also use Python classes to that effect where practical,
though we use some basic classes in preference over non-standard options:
- sets are encoded as `set()`
- multi-sets are tuples or `Counter` objects (NB: not the Python `multiset` class)
- vectors (whether indicator or weighted): are tuples (here as elsewhere we aim for immutability)
- ambiguous cases tend to be tuples, likewise for immutability.

Argument names are "set" or "vector" where that is the clear expectation and reason for the function.
Where the function could be more widely applied, arguments are named accordingly.
"""

__author__ = "Mark Gotham"

from typing import Iterable, Union


def multiset_to_vector(
    multiset: Iterable,
    max_index: Union[int, None] = None,
) -> tuple:
    """
    Converts any "set" or "multiset" (any iterable object containing only integers)
    into a "vector" (count of those integers organized by index).
    This is similar to the collections.Counter function, simply returning an ordered tuple instead of a dict.

    Parameters
    ----------
    multiset : Iterable
        The input integers as an iterable object (list, tuple, set).
        Multisets are accepted but not required (i.e., sets as trivial cases of multisets).
    max_index: Union[int, None]
        Sets the maximum index of the output vector.
        If None, use the maximum value of the input set.

    Returns
    -------
    tuple: The corresponding vector.

    Examples
    --------
    >>> test_multi_set = (1, 1, 1, 2, 2, 3)
    >>> vector = multiset_to_vector(test_multi_set)
    >>> vector
    (0, 3, 2, 1)

    >>> vector_with_padding = multiset_to_vector(test_multi_set, max_index=6)
    >>> vector_with_padding
    (0, 3, 2, 1, 0, 0, 0)

    >>> roundtrip = vector_to_multiset(vector)
    >>> roundtrip
    (1, 1, 1, 2, 2, 3)

    >>> roundtrip == test_multi_set
    True

    >>> test_set = (1, 2, 3)
    >>> vector_2 = multiset_to_vector(test_set)
    >>> vector_2
    (0, 1, 1, 1)

    >>> set_roundtrip = vector_to_multiset(vector_2)
    >>> set_roundtrip
    (1, 2, 3)

    >>> set_roundtrip == test_set
    True

    """
    if max_index is None:
        max_index = max(multiset)
    counts = [0] * (max_index + 1)
    for item in multiset:
        counts[item] += 1

    return tuple(counts)


def vector_to_multiset(vector: tuple[int, ...]) -> tuple:
    """
    Converts any "vector" (count of integers organised by index)
    to a corresponding "multiset" (unordered integers).

    Parameters
    ----------
    vector: The input vector.

    Returns
    -------
    tuple: The corresponding set as a tuple (because it will often be a multiset).

    Examples
    --------
    >>> test_vector = (0, 3, 2, 1, 0, 0, 0)
    >>> resulting_set = vector_to_multiset(test_vector)
    >>> resulting_set
    (1, 1, 1, 2, 2, 3)

    >>> roundtrip = multiset_to_vector(resulting_set, max_index=6)
    >>> roundtrip
    (0, 3, 2, 1, 0, 0, 0)

    >>> roundtrip == test_vector
    True

    """
    return tuple(i for i, count in enumerate(vector) for _ in range(count))


# Arithmetic operations: Addition/subtraction, multiplication, division


def apply_constant(
    set_or_vector: Iterable,
    constant: float,
    modulo: Union[int, None] = None,
) -> Union[tuple, list, set]:
    """
    Apply a constant value to a set or vector.

    Parameters
    ----------
    set_or_vector:
        An iterable representing a set or vector.
    constant:
        The constant may be an int or a float and positive or negative.
    modulo:
        An optional integer.
        If provided, the result will be taken modulo this value.

    Returns
    -------
    tuple, list, or set:
        The set or vector with the constant applied.
        This return type matches the input type.

    Examples
    --------
    >>> start = (0, 1, 2, 3, 11)
    >>> more = apply_constant(start, 1)
    >>> more
    (1, 2, 3, 4, 12)

    >>> less = apply_constant(more, -1)
    >>> less
    (0, 1, 2, 3, 11)

    >>> start == less
    True

    >>> more = apply_constant(start, 1, modulo=12)
    >>> more
    (1, 2, 3, 4, 0)

    >>> as_list = [0, 1, 2, 3, 11]
    >>> more_list = apply_constant(as_list, 1)
    >>> more_list
    [1, 2, 3, 4, 12]

    >>> as_set = {0, 1, 2, 3, 11}
    >>> more_set = apply_constant(as_set, 1)
    >>> more_set
    {1, 2, 3, 4, 12}
    """
    result = [x + constant for x in set_or_vector]
    if modulo is not None:
        result = [x % modulo for x in result]

    if isinstance(set_or_vector, tuple):
        return tuple(result)
    elif isinstance(set_or_vector, list):
        return result
    elif isinstance(set_or_vector, set):
        return set(result)
    else:
        return result


def scalar_multiply(input: tuple, scale_factor: int = 2) -> tuple:
    """
    Multiply all values of a tuple.

    Parameters
    ----------
    input: tuple

    scale_factor: int
        The "scale factor" aka "multiplicative operand".
        Multiply all terms by this amount.
        Defaults to 2.

    >>> scalar_multiply((0, 1, 2))
    (0, 2, 4)

    """
    return tuple(
        x * scale_factor for x in input
    )  # TODO np would be better in cases like this)


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


def is_set(input: Iterable) -> bool:
    """
    Check whether an iterable object is
    a set (specified in the type) or
    a de facto set (not in type, but with no repeated elements).

    >>> clear_set = {1, 2, 3}
    >>> is_set(clear_set)
    True

    >>> de_facto_set = (1, 2, 3)
    >>> is_set(de_facto_set)
    True

    >>> de_facto_multi_set = (1, 1, 2, 3)
    >>> is_set(de_facto_multi_set)
    False
    """
    if isinstance(input, set):
        return True
    elif len(set(input)) == len(input):
        return True
    return False


def is_indicator_vector(vector: tuple) -> bool:
    """
    Check whether an input vector (tuple) is an indicator vector, featuring only 0s and 1s.
    """
    if all(x in (0, 1) for x in vector):
        return True
    return False


def multiset_to_set(multiset: Iterable):
    """
    For completeness, this function provides a simple mapping from multiset (iterable) to set (set).
    No reciprocal function is possible.
    See `weighted_to_indicator` for the corresponding treatment of vectors.
    """
    return set(multiset)


def weighted_to_indicator(weighted_vector: tuple, threshold: float = 0.0) -> tuple:
    """
    Converts a weighted vector to an indicator vector.

    Parameters
    ----------
    weighted_vector: tuple
        Represents the weighted vector.
    threshold: float
        Values below this threshold will be set to 0.
        This handles cases where weights might be very small but not exactly zero.

    Returns
    -------
    tuple
        Representing the indicator vector (0s and 1s).

    Examples
    --------
    >>> weighted_vector1 = (0.0, 0.0, 2.0, 0.0)
    >>> weighted_to_indicator(weighted_vector1)
    (0, 0, 1, 0)

    >>> weighted_vector2 = (0.2, 0.0, 1.5, 0.0, 0.01)
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


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
