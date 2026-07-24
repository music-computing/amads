"""
Prepare a grid
based on the tatum (smallest value needed to fully express all event positions).
This will be a monotonically increasing sequence of integers
where each integer expresses the event position relative in multiples of the tatum.

This is needed for algorithms including the
Inner Metrical Analysis (IMA) which takes this list of integers indices
to deduce "local" and "spectral" meters.

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"

from fractions import Fraction
from typing import Union

from amads.io.readscore import read_score, set_reader_warning_level
from amads.time.meter.grid import get_tatum_from_priorities


def score_to_offsets(path_to_score: str, to_indices: bool = True) -> list:
    """
    Import a score and convert it to the sorted list of unique
    starting timepoints as measured in quarters since the start of the score,
    and (optionally) convert those starts to indices on a tatum grid.

    Note: score parsing warnings are supressed.
    If you need to test the validity of scores, handle that separately.

    Parameters
    ----------
    path_to_score
        A string for the file path or URL.
    to_indices
        If True, convert the starts to indices on a tatum grid.

    Examples
    --------
    >>> from amads.music import example
    >>> test_xml_file = str(example.fullpath("musicxml/ex1.xml"))
    >>> score_to_offsets(test_xml_file, to_indices=False)
    [0.0, 0.5, 1.25, 1.5, 2.0, 2.25]

    >>> score_to_offsets(test_xml_file)
    [0, 2, 5, 6, 8, 9]

    """
    set_reader_warning_level("none")
    score = read_score(path_to_score, show=False)
    notes = score.get_sorted_notes()
    timepoints = sorted(set(n.onset for n in notes))
    if to_indices:
        return starts_to_indices(timepoints)
    else:
        return timepoints


def starts_to_indices(
    starts: list, tatum: Union[Fraction, int, None] = None
) -> list:
    """
    Given a list of start times,
    convert to a list of indices on the tatum grid.

    If a tatum value is provided, use that;
    otherwise, deduce the tatum using GCD methods.

    This is the input format for the IMA algorithm, among others.

    Note that this function is generally applicable to any contiainer.
    While taking time since the start of the whole piece may be the most typical use case,
    other reference points include the start of the measure.

    Parameters
    ----------
    starts
        A list of numeric start times.
    tatum
        The tatum duration to use as the grid unit and values are rounded to it.
        If None, it is
        deduced automatically via `get_tatum_from_priorities`.

    Examples
    --------
    >>> starts_to_indices([0, 1/2, 2/3, 2.5])
    [0, 3, 4, 15]

    >>> starts_to_indices([0, 1/2, 2/3, 2.5], tatum=Fraction(1, 6))
    [0, 3, 4, 15]

    >>> starts_to_indices([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.5, 6.6640625, 6.83203125, 7.0])
    [0, 6, 12, 18, 24, 30, 36, 39, 40, 41, 42]

    >>> starts_to_indices([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.5, 6.6640625, 6.83203125, 7.0], tatum=Fraction(1, 6))
    [0, 6, 12, 18, 24, 30, 36, 39, 40, 41, 42]

    Also accepts tatum values greater than 1:

    >>> starts_to_indices([3, 6, 9], tatum=3)
    [1, 2, 3]

    >>> starts_to_indices([3, 6, 9])
    [1, 2, 3]

    >>> starts_to_indices([0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40])
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    >>> starts_to_indices([28.0, 29.0, 29.5, 30.0, 32.0, 33.0, 34.0, 36.0, 38.0, 40.0])
    [56, 58, 59, 60, 64, 66, 68, 72, 76, 80]

    """
    if not starts:
        raise ValueError("starts must not be empty")

    if tatum is None:
        tatum = get_tatum_from_priorities(starts)

    return [round(x / tatum) for x in starts]


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
