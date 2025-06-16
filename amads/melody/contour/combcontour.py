"""
Pairwise pitch comparison melodic "contour" representation of a monophonic Score

Date: [2025-01-26]

Description:
    Computes a combination contour matrix given a monophonic Score.
    (See combcontour docstring for more details)

Usage:
    [Add basic usage examples or import statements]

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=54

Reference(s):
    Marvin, E. W. & Laprade, P. A. (1987). Relating music contours:
        Extensions of a theory for contour. Journal of Music Theory,
        31(2), 225-267.
"""

import numpy as np

from ...core.basics import Note, Score
from ...pitch.ismonophonic import ismonophonic


def pairwiseCombinationContour(score: Score):
    """
    Define the corresponding index of a note in a monophonic Score
    as the order statistic of a note based off of note onset.
    Define a combination contour matrix of a monophonic score as a boolean
    square matrix whose row and column indices are the corresponding indices
    of notes, and for all i,j-th element in the matrix such that (i > j and
    note[j].keynum > note[i].keynum)
    Computes a combination contour matrix and a list of notes for corresponding
    indices given a monophonic Score.

    For instance, given a monophonic score of 4 notes where the notes are sorted by
    onset:
    [note1, note2, note3, note4]
    with corresponding pitch values:
    [55, 40, 60, 50]
    We will get the following combination contour matrix:
    [[0, 0, 0, 0],
     [1, 0, 0, 0],
     [0, 0, 0, 0],
     [1, 0, 1, 0]]
    and the following list of notes for corresponding indices:
    [note1, note2, note3, note4]

    Parameters
    ----------
    score
        Monophonic input score (class from core.basics for storing music scores)

    Returns
    -------
    Tuple of the following:
    (1) 2-d numpy array containing the combination contour matrix
    (2) list of notes (as a reference for corresponding index of each note
    in the 2-d array)

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/combcontour.m

    Examples
    --------
    [Unfortunately, still having problem resolving score construction]
    """
    # melodic analysis must be done on a monophonic score
    if not ismonophonic(score):
        raise ValueError("Score must be monophonic")
    # make a flattened and collapsed copy of the original score
    flattened_score = score.flatten(collapse=True)

    # extracting note references here from our flattened score
    notes = list(flattened_score.find_all(Note))

    # sort the notes
    notes.sort(key=lambda note: (note.start, -note.pitch.keynum))
    # no comparisons to be had if the score contains no notes
    if not notes:
        raise ValueError("Score is empty")

    pitch_array = np.array([note.keynum for note in notes])

    contour_mtx = np.full((len(notes), len(notes)), False, dtype=bool)

    # perform the comparison with slicing notation for numpy array
    for i in range(len(notes)):
        contour_mtx[i:, i] = pitch_array[i] > pitch_array[i:]

    return notes, contour_mtx
