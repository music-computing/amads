"""
Handle figuration of the kind seen in middle-voice keyboard arpeggiation for instance.

Note 1:
    This module assumes clean separation of textural elements.
    In the wild, keyboard music often combines >2 voices into 2 staves, for instance.
    See the paired notebook (notebooks/figuration) for an example.

Note:
    This functionality has been implemented for work on figuration,
    but none of ir is specific to that use case.
    Any or all of this may move to a more central part of AMADS or otherwise be refactored
    if deemed useful to share in wider settings.

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


from itertools import groupby


def encode(items):
    """
    Compresses a sequence of items into (item, count) tuples.

    Complements `decode`.

    Examples
    --------

    >>> moonlight_encoded = [
    ... ([56, 61, 64], 8),
    ... ([57, 61, 64], 2),
    ... ([57, 62, 66], 2),
    ... ([56, 60, 66], 1),
    ... ([56, 61, 64], 1),
    ... ([56, 61, 63], 1),
    ... ([54, 60, 63], 1),
    ... ([52, 56, 61], 1),
    ... ([56, 61, 64], 3),
    ... ]

    >>> moonlight_decoded = decode(moonlight_encoded)
    >>> moonlight_decoded[7]
    [56, 61, 64]

    >>> moonlight_decoded[16]
    [52, 56, 61]

    >>> moonlight_decoded[17]
    [56, 61, 64]

    Roundtrip
    >>> re_encoded = encode(moonlight_decoded)
    >>> re_encoded == moonlight_encoded
    True

    """
    return [(k, len(list(g))) for k, g in groupby(items)]


def decode(data):
    """
    Expands (item, count) tuples back into a sequence of items.

    Complements `encode`; see notes and examples there.
    """
    return [item for item, count in data for _ in range(count)]


def get_size_order(numbers):
    """
    Given an ordered list of numbers (here intended for the elements of a figuration pattern)
    return the size order (rank).
    Assign 1 to the smallest, 2 to the middle, and so on.

    Process:
    - Create a list of tuples from the input values (value, original_index)
    - Sort by value to determine rank
    - Initialize result array with zeros
    - Assign ranks (1-indexed) to the original indices

    The ranking based on distinct sorted values ("dense" ranking), to accommodate repeated values (they share a rank).

    As a fail-safe, if there is any `None` in numbers return None.
    If there are any non-numeric values, there will be errors.

    Examples
    --------
    >>> get_size_order([4, 8, 5])
    [1, 3, 2]

    >>> get_size_order([5, 4, 8])
    [2, 1, 3]

    Repeated numbers are accepted
    >>> get_size_order([5, 4, 8, 5])
    [2, 1, 3, 2]

    >>> get_size_order([None, 4, 8]) is None
    True

    """
    if None in numbers:
        return None

    unique_sorted = sorted(set(numbers))
    value_to_rank = {
        value: rank for rank, value in enumerate(unique_sorted, start=1)
    }

    result = [value_to_rank[num] for num in numbers]

    return result


if __name__ == "__main__":
    import doctest

    doctest.testmod()
