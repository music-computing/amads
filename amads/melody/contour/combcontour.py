"""
Pairwise pitch comparison melodic "contour" representation of a monophonic Score

Ports the 'combcontour' function from miditoolbox.

https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 55
"""

import numpy as np

from amads.core.basics import Score
from amads.pitch.ismonophonic import ismonophonic


def get_pitch_comparison_contour_matrix(
    score: Score,
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

    References
    ----------
        Marvin, E. W. & Laprade, P. A. (1987). Relating music contours:
            Extensions of a theory for contour. Journal of Music Theory,
            31(2), 225-267.

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/combcontour.m
    """
    # melodic analysis must be done on a monophonic score
    if not ismonophonic(score):
        raise ValueError("Score must be monophonic")

    # extracting note references
    notes = score.get_sorted_notes()

    # no comparisons to be had if the score contains no notes
    if not notes:
        return None

    pitch_array = np.array([note.midi_num for note in notes])

    contour_mtx = np.full((len(notes), len(notes)), False, dtype=bool)

    # perform the comparison with slicing notation for numpy array
    for i in range(len(notes)):
        contour_mtx[i:, i] = pitch_array[i] > pitch_array[i:]

    return contour_mtx
