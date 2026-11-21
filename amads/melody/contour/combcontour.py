"""
Pairwise pitch comparison melodic "contour" representation of a monophonic Score

Ports the 'combcontour' function from miditoolbox.

https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 55
"""

from collections.abc import Iterator
from itertools import tee

import numpy as np

from amads.core.basics import Note, Score


def get_pitch_comparison_contour_matrix(
    note_iterator: Iterator[Note],
) -> np.ndarray[bool] | None:
    """
    Computes a pairwise melodic contour matrix.

    This function first sorts the notes of a monophonic score chronologically by
    their onset time. The sorted position of each note acts as its index.
    It then constructs a boolean matrix comparing the pitch (keynum) of every
    note against every other note to map the pitch "contour" (up/down trend)
    of the melody.

    Parameters
    ----------
    note_iterator
        Note iterator from a monophonic note input (class from core.basics for
        storing music scores)
        For arbitrary matrix cell at (i, j):
        True if the pitch from the pitch note in the row index is smaller.
        False otherwise.

    Returns
    -------
    Optional[np.array[bool]]
        the boolean pitch comparison contour matrix
        None if the score is empty

    References
    ----------
        Marvin, E. W. & Laprade, P. A. (1987). Relating music contours:
            Extensions of a theory for contour. Journal of Music Theory,
            31(2), 225-267.
    """
    note_iterator, next_iterator = tee(note_iterator)
    # no comparisons to be had if the score contains no notes
    if not next(next_iterator, None):
        return None

    pitch_array = np.fromiter((note.midi_num for note in note_iterator), int)
    pitch_len = pitch_array.size

    contour_mtx = np.full((pitch_len, pitch_len), False, dtype=bool)

    # perform the comparison with slicing notation for numpy array
    for i in range(pitch_len):
        contour_mtx[i:, i] = pitch_array[i] > pitch_array[i:]

    return contour_mtx


def combination_contour(
    score: Score,
) -> np.ndarray[bool] | None:
    """
    This function is a port of combcontour from miditoolbox and replicates
    its functionality.

    Parameters
    ----------
    score
        Monophonic input score (class from core.basics for storing music scores)
        For arbitrary matrix cell at (i, j):
        True if the pitch from the pitch note in the row index is smaller.
        False otherwise.

    Returns
    -------
    Optional[np.array[bool]]
        the boolean pitch comparison contour matrix
        None if the score is empty

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/combcontour.m
    """
    # melodic analysis must be done on a monophonic score
    if not score.ismonophonic():
        raise ValueError("Score must be monophonic")

    # no comparisons to be had if the score contains no notes
    if not next(score.find_all(Note), None):
        return None

    return get_pitch_comparison_contour_matrix(score.find_all(Note))
