"""
Prepare a grid
based on the tatum (smallest value needed to fully express all event positions).
This will be a monotonically increasing sequence of integers
where each integer expresses the event position relative in multiples of the tatum.

This is needed for algorithms including the
Inner Metrical Analysis (IMA) which takes this list of integers indices
and deduced local and spectral meters.

"""

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------

from partitura import musicxml_to_notearray

from amads.time.meter.grid import get_tatum


def score_to_offsets(path_to_score: str, to_indices: bool = True) -> list:
    """
    Import a score and convert it to the set of
    starting timepoints as measured in quarters since the start of the score
    and (optionally) convert those starts to indices on a tatum grid.

    Parameters
    ----------
    path_to_score
        A string for the file path. Yes, a string. Partitura doesn't seem to accept a `Path` object ...
    to_indices
        If True, convert the starts to indices on a tatum grid.

    """
    note_array = musicxml_to_notearray(
        path_to_score,
        flatten_parts=True,
    )
    offsets = [note[0] for note in note_array]
    offsets = list(set(offsets))
    offsets.sort()

    if to_indices:
        return starts_to_indices(offsets)
    else:
        return offsets


def starts_to_indices(list_of_starts: list):
    """
    Given a list of start times,
    deduce the tatum and convert the initial list to a list of indices on the tatum grid.

    This is the input format for the IMA algorithm, among others.

    Examples
    --------
    >>> combine_half_and_third = [0, 1/2, 2/3, 2.5]
    >>> get_tatum(combine_half_and_third)
    Fraction(1, 6)

    >>> starts_to_indices(combine_half_and_third)
    [0, 3, 4, 15]

    >>> badly_rounded = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.5, 6.6640625, 6.83203125, 7.0]
    >>> get_tatum(badly_rounded, distance_threshold=0.1)
    Fraction(1, 6)

    >>> starts_to_indices(badly_rounded)
    [0, 6, 12, 18, 24, 30, 36, 39, 40, 41, 42]

    """
    tatum = get_tatum(list_of_starts)
    return [round(x / tatum) for x in list_of_starts]


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
