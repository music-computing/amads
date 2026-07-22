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


def chunk(
    user_values: list,
    sublist_length: int,
    require_even_div: bool = True,
) -> list[list]:
    """
    Split `user_values` into consecutive sublists of length `sublist_length`.

    If `len(user_values)` isn't evenly divisible by `sublist_length`,
    the outcome depends on `require_even_div`.
    If `require_even_div` is True a ValueError is raised.
    If `require_even_div` is False (default),
    the final sublist will be shorter than the rest.

    Parameters
    ----------
    user_values : list
        The list to split.
    sublist_length : int
        Desired length of each sublist. Must be a positive integer.
    require_even_div : bool, default True
        If True, raise ValueError when `len(user_values) % sublist_length != 0`.
        If False, allow a shorter final sublist.

    Returns
    -------
    list[list]
        The list of sublists.

    Raises
    ------
    ValueError
        If `sublist_length` is not a positive integer, or if
        `require_even_div` is True and `len(user_values)` is not evenly
        divisible by `sublist_length`.

    Examples
    --------
    Segment a list of 8 elements into sublists of 4:

    >>> user_values = [1, 2, 3, 4, 5, 6, 7, 8]
    >>> chunk(user_values, 4)
    [[1, 2, 3, 4], [5, 6, 7, 8]]

    Segment the same list into sublists of 3. Since 8 % 3 != 0,
    `require_even_div=True` (the default) raises:

    >>> chunk(user_values, 3)
    Traceback (most recent call last):
        ...
    ValueError: list length 8 not divisible by 3

    With `require_even_div=False`, no error is raised, the last sublist is simply short:

    >>> chunk(user_values, 3, require_even_div=False)
    [[1, 2, 3], [4, 5, 6], [7, 8]]

    An empty list (user_values = []) returns []

    >>> chunk([], 3)
    []
    """
    if sublist_length <= 0:
        raise ValueError(
            f"sublist_length must be positive, got {sublist_length}"
        )

    if require_even_div and len(user_values) % sublist_length != 0:
        raise ValueError(
            f"list length {len(user_values)} not divisible by {sublist_length}"
        )

    return [
        user_values[i : i + sublist_length]
        for i in range(0, len(user_values), sublist_length)
    ]


def find_period(user_values: list) -> int:
    """
    Find the smallest period `p` such that `user_values` is composed of the
    subsequence `user_values[:p]` repeated (with the final repeat possibly
    truncated).

    Formally,
    the smallest `p` in `1..len(user_values)`
    such that `user_values[i] == user_values[i % p]` for every index `i`.
    If no smaller period exists,
    `p == len(user_values)` (the list is its own period).

    Parameters
    ----------
    user_values : list
        The list to inspect. Elements must support `==` comparison.

    Returns
    -------
    int
        The smallest period length.
        Returns len(user_values) if there's no internal period,
        and returns 0 if `user_values` is empty.

    Examples
    --------
    >>> find_period([1, 2, 1, 2, 1, 2])
    2
    >>> find_period([7, 3, 5, 7, 3, 5, 7, 3, 5])
    3
    >>> find_period([1, 2, 3, 4, 5])
    5
    >>> find_period([])
    0
    """
    m = len(user_values)
    if m == 0:
        return 0

    for p in range(1, m + 1):
        if all(user_values[i] == user_values[i % p] for i in range(m)):
            return p

    return m  # unreachable, but keeps type-checkers happy


def chunk_by_pattern(user_values: list) -> list[list]:
    """
    Split `user_values` into sublists using its smallest repeating period,
    detected with `find_period` (no user-specified length).

    Internally `find_period` determines the chunk size,
    then delegates to `chunk`.

    Because the period is derived from `user_values`
    itself, `len(user_values)` is always evenly divisible by it except when
    no repetition exists, in which case the whole list is returned
    as a single chunk.

    Parameters
    ----------
    user_values : list
        The list to split. Elements must support `==` comparison.

    Returns
    -------
    list[list]
        The list of sublists, each equal to `user_values[:period]`,
        except possibly the last if the period doesn't evenly divide
        `len(user_values)`.

    Examples
    --------
    >>> chunk_by_pattern([1, 2, 1, 2, 1, 2])
    [[1, 2], [1, 2], [1, 2]]

    >>> chunk_by_pattern([7, 3, 5, 7, 3, 5, 7, 3, 5])
    [[7, 3, 5], [7, 3, 5], [7, 3, 5]]

    No repeating pattern exists, so the whole list is one chunk:

    >>> chunk_by_pattern([1, 2, 3, 4, 5])
    [[1, 2, 3, 4, 5]]
    """
    period = find_period(user_values)

    if period == 0:
        return []

    return chunk(user_values, period, require_even_div=False)


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


def get_size_order(numbers: list[int | None] | tuple[int | None, ...]) -> None:
    """
     Given an ordered list of numbers
     (here intended for the MIDI numbers of pitches in a figuration pattern)
     return the size order (rank).
     Assign 1 to the smallest, 2 to the next higher, and so on.

     The ranking based on distinct sorted values ("dense" ranking), to accommodate repeated values (they share a rank).

     As a fail-safe, if there is any `None` in numbers return None.
     If there are any non-numeric values, there will be errors.

     Examples
     --------
     >>> get_size_order([4, 8, 5])
     (1, 3, 2)

     >>> get_size_order([5, 4, 8])
     (2, 1, 3)

     Repeated numbers are accepted
     >>> get_size_order([5, 4, 8, 5])
     (2, 1, 3, 2)

     One or more None values are accepted and any None returns None.
     >>> get_size_order([None, 4, 8]) == (None,)
     True

    >>> get_size_order([None, None, None]) == (None,)
    True

    """
    if None in numbers:
        return (None,)

    unique_sorted = sorted(set(numbers))
    value_to_rank = {
        value: rank for rank, value in enumerate(unique_sorted, start=1)
    }

    result = tuple([value_to_rank[num] for num in numbers])

    return result


if __name__ == "__main__":
    import doctest

    doctest.testmod()
