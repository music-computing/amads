"""
The `pitch_list_transformations` module
provides basic functions for transforming pitch lists
(e.g., transposition, inversion, retrograde, rotation).

This small module provides some more niche routines
that are specific to tone rows in serial music.

"""

from typing import List, Tuple, Union

from .transformations import every_nth, transpose_to


def rotate_hexachords(
    row: Union[List, Tuple], transpose_iterations: bool = False
) -> list:
    """
    Implements a set of hexachord rotations of the kind described in krenek 1960, p.212.
    Splits the row into two hexachords and iteratively rotates each.
    This function returns a list of lists with each iteration until
    the cycle is complete and come full circle.


    Parameters
    ----------
    row
        A tone row, or any sequence of 12 integers.
    transpose_iterations
        If True, transpose each iteration to start on the original pitch of the hexachord.
        This alternative is also described by krenek.
        Note this often converts a 12-tone row into one with repeated pitches.

    Returns
    -------
    list
        A list of lists with the full cycle.

    Examples
    --------
    >>> row_krenek = [5, 7, 9, 10, 1, 3, 11, 0, 2, 4, 6, 8]
    >>> for x in rotate_hexachords(row_krenek):
    ...     print(x)
    [5, 7, 9, 10, 1, 3, 11, 0, 2, 4, 6, 8]
    [7, 9, 10, 1, 3, 5, 0, 2, 4, 6, 8, 11]
    [9, 10, 1, 3, 5, 7, 2, 4, 6, 8, 11, 0]
    [10, 1, 3, 5, 7, 9, 4, 6, 8, 11, 0, 2]
    [1, 3, 5, 7, 9, 10, 6, 8, 11, 0, 2, 4]
    [3, 5, 7, 9, 10, 1, 8, 11, 0, 2, 4, 6]
    [5, 7, 9, 10, 1, 3, 11, 0, 2, 4, 6, 8]
    """

    assert len(row) == 12

    rows = [row]  # initialise with starting

    hexachord1note1 = row[0]
    hexachord2note1 = row[6]

    for i in range(1, 6):
        first_hexachord = row[i:6] + row[0:i]
        second_hexachord = row[6 + i :] + row[6 : 6 + i]

        if transpose_iterations:
            first_hexachord = transpose_to(first_hexachord, start=hexachord1note1)
            second_hexachord = transpose_to(second_hexachord, start=hexachord2note1)

        new_row = first_hexachord + second_hexachord
        rows.append(new_row)

    rows.append(row)  # completes the cycle

    return rows


def pair_swap_krenek(row: Union[List, Tuple]) -> list:
    """
    Iteratively swaps pairs of adjacent notes in a row
    with a two-step process as described in Krenek 1960, p.213.

    Returns a list of 13 rows of which the last is the retrograde of the first.
    As such, calling this twice brings you back to the original row.

    Parameters
    ----------
    row
        A tone row, or any sequence of 12 integers.

    Returns
    -------
    list
        A list of lists with the full cycle.

    Examples
    --------
    >>> pair_swap_row = [9, 2, 3, 6, 5, 1, 7, 4, 8, 0, 10, 11]
    >>> for x in pair_swap_krenek(pair_swap_row):
    ...     print(x)
    [9, 2, 3, 6, 5, 1, 7, 4, 8, 0, 10, 11]
    [9, 3, 2, 5, 6, 7, 1, 8, 4, 10, 0, 11]
    [3, 9, 5, 2, 7, 6, 8, 1, 10, 4, 11, 0]
    [3, 5, 9, 7, 2, 8, 6, 10, 1, 11, 4, 0]
    [5, 3, 7, 9, 8, 2, 10, 6, 11, 1, 0, 4]
    [5, 7, 3, 8, 9, 10, 2, 11, 6, 0, 1, 4]
    [7, 5, 8, 3, 10, 9, 11, 2, 0, 6, 4, 1]
    [7, 8, 5, 10, 3, 11, 9, 0, 2, 4, 6, 1]
    [8, 7, 10, 5, 11, 3, 0, 9, 4, 2, 1, 6]
    [8, 10, 7, 11, 5, 0, 3, 4, 9, 1, 2, 6]
    [10, 8, 11, 7, 0, 5, 4, 3, 1, 9, 6, 2]
    [10, 11, 8, 0, 7, 4, 5, 1, 3, 6, 9, 2]
    [11, 10, 0, 8, 4, 7, 1, 5, 6, 3, 2, 9]

    """

    rows = [row]

    for pair in range(6):

        # First swap operation: starting at position 1 (2nd pitch)
        row = [x for x in row]
        for x in range(1, 11, 2):
            row[x], row[x + 1] = row[x + 1], row[x]
        rows.append(row)

        # Second swap operation: starting at position 0 (1st pitch)
        row = [x for x in row]
        for x in range(0, 12, 2):
            row[x], row[x + 1] = row[x + 1], row[x]
        rows.append(row)

    return rows


def lumsdaine_cycle(
    row: Union[list, None] = None,
) -> list[list]:
    """
    A multipart
    rotation and re-combination
    method as reported in
    Hopper's "The Music of David Lumsdaine", p.21.

    Parameters
    ----------
    row
        A tone row, or any sequence of 12 integers.

    Returns
    -------
    list
        A list of lists with the full cycle.

    Examples
    --------
    >>> for x in lumsdaine_cycle():
    ...     print(x)
    [11, 6, 5, 0, 3, 2, 9, 8, 10, 4, 1, 7]
    [11, 9, 6, 8, 5, 10, 0, 4, 3, 1, 2, 7]
    [11, 10, 2, 8, 3, 9, 0, 7, 5, 1, 6, 4]
    [11, 0, 10, 7, 2, 5, 8, 1, 3, 6, 9, 4]
    [2, 6, 10, 1, 11, 5, 9, 7, 3, 0, 8, 4]
    [2, 9, 6, 7, 10, 3, 1, 0, 11, 8, 5, 4]
    [2, 3, 5, 7, 11, 9, 1, 4, 10, 8, 6, 0]
    [2, 1, 3, 4, 5, 10, 7, 8, 11, 6, 9, 0]
    [5, 6, 3, 8, 2, 10, 9, 4, 11, 1, 7, 0]
    [5, 9, 6, 4, 3, 11, 8, 1, 2, 7, 10, 0]
    [5, 11, 10, 4, 2, 9, 8, 0, 3, 7, 6, 1]
    [5, 8, 11, 0, 10, 3, 4, 7, 2, 6, 9, 1]
    [10, 6, 11, 7, 5, 3, 9, 0, 2, 8, 4, 1]
    [10, 9, 6, 0, 11, 2, 7, 8, 5, 4, 3, 1]
    [10, 2, 3, 0, 5, 9, 7, 1, 11, 4, 6, 8]
    [10, 7, 2, 1, 3, 11, 0, 4, 5, 6, 9, 8]
    [3, 6, 2, 4, 10, 11, 9, 1, 5, 7, 0, 8]
    [3, 9, 6, 1, 2, 5, 4, 7, 10, 0, 11, 8]
    [3, 5, 11, 1, 10, 9, 4, 8, 2, 0, 6, 7]
    [3, 4, 5, 8, 11, 2, 1, 0, 10, 6, 9, 7]

    """
    if row is None:
        row = [11, 6, 5, 0, 3, 2, 9, 8, 10, 4, 1, 7]
    out = []
    for i in range(5):  # run 4, update to new starting row, and run again
        out += lumsdaine_4(row)
        row = every_nth(out[-1], start_index=4)
    return out


def lumsdaine_4(
    row: Union[List, None] = None,
) -> list[list]:
    """
    One phase of `lumsdaine_cycle()`
    producing a set of 4 rows.

    Parameters
    ----------
    row
        A tone row, or any sequence of 12 integers.

    Returns
    -------
    list
        A list of lists with the full cycle.

    Examples
    --------
    >>> for x in lumsdaine_4([11, 6, 5, 0, 3, 2, 9, 8, 10, 4, 1, 7]):
    ...     print(x)
    [11, 6, 5, 0, 3, 2, 9, 8, 10, 4, 1, 7]
    [11, 9, 6, 8, 5, 10, 0, 4, 3, 1, 2, 7]
    [11, 10, 2, 8, 3, 9, 0, 7, 5, 1, 6, 4]
    [11, 0, 10, 7, 2, 5, 8, 1, 3, 6, 9, 4]

    >>> for x in lumsdaine_4([5, 9, 7, 3, 0, 8, 4, 2, 6, 10, 1, 11]):
    ...     print(x)
    [5, 9, 7, 3, 0, 8, 4, 2, 6, 10, 1, 11]
    [5, 4, 9, 2, 7, 6, 3, 10, 0, 1, 8, 11]
    [5, 6, 8, 2, 0, 4, 3, 11, 7, 1, 9, 10]
    [5, 3, 6, 11, 8, 7, 2, 1, 0, 9, 4, 10]

    """
    if row is None:
        row = [11, 6, 5, 0, 3, 2, 9, 8, 10, 4, 1, 7]
    row2 = lumsdaine_hexachord_pairs(row)
    row3 = every_nth(row2)
    row4 = lumsdaine_hexachord_pairs(row3)
    return [row, row2, row3, row4]


def lumsdaine_hexachord_pairs(row: list):
    """
    Constituent step in the Lumsdaine method
    that re-arrange row elements indices into the order 0, 6, 1, 7 ...

    Parameters
    ----------
    row
        A tone row, or any sequence of 12 integers.

    Returns
    -------
    list
        A list of lists with the full cycle.

    Examples
    --------
    >>> lumsdaine_hexachord_pairs([11, 6, 5, 0, 3, 2, 9, 8, 10, 4, 1, 7])
    [11, 9, 6, 8, 5, 10, 0, 4, 3, 1, 2, 7]
    """
    out_row = []
    for i in range(6):
        out_row += [row[i], row[i + 6]]
    return out_row


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
