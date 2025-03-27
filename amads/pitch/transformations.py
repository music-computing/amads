"""
Basic functionality for transforming pitch lists
expressed as integers (MIDI numbers or pitch classes)
through transposition, inversion, retrograde, rotation, and more.

Most apply equally to any pitch class sequence
and can therefore be use in melody and harmony settings.
"""

from typing import Iterable

# ------------------------------------------------------------------------------


def transpose_by(pitches: Iterable, semitones: int, mod_12: bool = True) -> list:
    """
    Transposes a list of pitches by an interval of size
    set by the value of `semitones`.

    Parameters
    ----------
    pitches
        Any list or tuple of integers representing pitches as MIDI numbers or pitch classes.
    semitones
        How far to transpose, expressed in semitones (1 per MIDI note).
    mod_12
        If True, return values modulo 12 (necessary for pitch class sets, not for MIDI numbers)

    Returns
    -------
    list
        A new list of the same length as the input.

    Examples
    --------

    >>> transpose_by([0, 1, 2, 3,], 16, mod_12=True)
    [4, 5, 6, 7]

    >>> transpose_by([0, 1, 2, 3,], 16, mod_12=False)
    [16, 17, 18, 19]

    """
    result = []
    for pitch in pitches:
        transposed = pitch + semitones
        if mod_12:
            transposed %= 12
        result.append(transposed)
    return result


def transpose_to(pitches: Iterable, start: int = 0, mod_12: bool = True) -> list:
    """
    Transpose a list of pitch classes to start on 0 (by default), or
    any another number set by the value of `start`.

    Parameters
    ----------
    pitches
        Any list or tuple of integers representing pitches as MIDI numbers or pitch classes.
    start
        The first number of the new list.
    mod_12
        If True, return values modulo 12 (necessary for pitch class sets, not for MIDI numbers)

    Returns
    -------
    list
        A new list of the same length as the input.

    Examples
    --------

    >>> transpose_to([0, 1, 2, 3,], 16, mod_12=True)
    [4, 5, 6, 7]

    >>> transpose_to([0, 1, 2, 3,], 16, mod_12=False)
    [16, 17, 18, 19]

    """
    difference = start - pitches[0]
    result = []
    for pitch in pitches:
        transposed = pitch + difference
        if mod_12:
            transposed %= 12
        result.append(transposed)
    return result


def retrograde(pitches: Iterable) -> list:
    """
    Retrograde (reverse) a list of pitches.

    Parameters
    ----------
    pitches
        Any list or tuple of integers representing pitches as MIDI numbers or pitch classes.

    Returns
    -------
    list
        A new list of the same length as the input.

    Examples
    --------

    >>> retrograde([2, 6, 9])
    [9, 6, 2]

    """
    result = pitches[::-1]  # to create a copy
    return result


def invert(
    pitches: Iterable, use_first_not_0: bool = True, mod_12: bool = True
) -> list:
    """
    Invert a list of pitch classes around a specified pitch: the starting pitch or 0.

    Parameters
    ----------
    pitches
        Any list or tuple of integers representing pitches as MIDI numbers or pitch classes.
    use_first_not_0
        If true, use the first number of the list as the centre of the inversion.
    mod_12
        If True, return values modulo 12 (necessary for pitch class sets, not for MIDI numbers)

    Returns
    -------
    list
        A new list of the same length as the input.

    Examples
    --------
    >>> invert([5, 6, 7])
    [5, 4, 3]

    >>> invert([5, 6, 7], use_first_not_0=False)
    [7, 6, 5]

    """
    origin = pitches[0] if use_first_not_0 else 0
    result = []
    for pitch in pitches:
        inverted = 2 * origin - pitch
        if mod_12:
            inverted %= 12
        result.append(inverted)

    return result


def pitches_to_intervals(
    pitches: Iterable, wrap: bool = False, mod_12: bool = True
) -> list:
    """
    Get the interval succession of a list of pitches.

    Parameters
    ----------
    pitches
        Any list or tuple of integers representing pitches as MIDI numbers or pitch classes.
    wrap
        If true, include the interval from the last element to the first in addition.
    mod_12
        If True, return values modulo 12 (necessary for pitch class sets, not for MIDI numbers)

    Returns
    -------
    list
        A new list of the same length as the input (if wrap), otherwise, one less.

    Examples
    --------
    >>> pitches_to_intervals([0, 2, 5])
    [2, 3]

    >>> pitches_to_intervals([0, 2, 5], wrap=True)
    [2, 3, 7]

    """
    intervals = []
    if wrap:
        pitches += [pitches[0]]
    for i in range(1, len(pitches)):
        i = pitches[i] - pitches[i - 1]
        if mod_12:
            i %= 12
        intervals.append(i)

    return intervals


def rotate(pitches: Iterable, steps: int = 1) -> list:
    """
    Rotates a list of pitch classes through N steps (i.e. starts on the Nth element).

    Should be called on an integer less than the length of the pitch list.
    If called on a larger integer, the value modulo the length of the pitch list.
    (e.g. 15 becomes 3 for a pitch list of length 12).

    Parameters
    ----------
    pitches
        Any list or tuple of integers representing pitches as MIDI numbers or pitch classes.
    steps
        If true, include the interval from the last element to the first in addition.

    Returns
    -------
    list
        A new list of the same length as the input.

    Examples
    --------
    >>> rotate([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 4)
    [4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3]


    """
    list_len = len(pitches)
    if steps > list_len:
        steps = steps % list_len
    result = pitches[steps:] + pitches[:steps]
    return result


def every_nth(pitches: list, start_index: int = 0, step_size: int = 5) -> list:
    """
    Cycle through a list of pitches
    with a step size of n mod the length of the list

    By default,
    start at index 0 and iterate 12 times (0-12),
    though both the start index and the range() are settable arguments,
    hence this equivlance:

    Parameters
    ----------
    pitches
        Any list or tuple of integers representing pitches as MIDI numbers or pitch classes.
    start_index
        The index position in the list to start at.
    step_size
        The gap between successive elements.

    Returns
    -------
    list
        A new list of the same length as the input.

    Examples
    --------

    >>> test_pitches = [11, 9, 6, 8, 5, 10, 0, 4, 3, 1, 2, 7]
    >>> every_nth(test_pitches, step_size=5)
    [11, 10, 2, 8, 3, 9, 0, 7, 5, 1, 6, 4]

    >>> every_nth(test_pitches, step_size=5, start_index=5)
    [10, 2, 8, 3, 9, 0, 7, 5, 1, 6, 4, 11]

    """
    list_len = len(pitches)
    out_pitches = []
    for i in range(list_len):
        out_pitches.append(pitches[(start_index + i * step_size) % list_len])
    return out_pitches


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
