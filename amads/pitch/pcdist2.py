"""
This module provides the `pcdist2` function.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=81.
"""

from ..core.basics import Note, Score


def update_pcd(pcd: list[list[float]], notes: list[Note], weighted: bool):
    """Updates the pitch-class distribution matrix based on the given notes.

    Serves as a helper function for `pcdist2`

    Args:
        pcd (list[list[float]]): The pitch-class distribution matrix to be
                                 updated.
        notes (list[Note]): The list of notes to process.
        weighted (bool, optional): If True, the pitch-class distribution is
                                   weighted by note durations.
    """
    prev = None
    for note in notes:
        if prev:
            pc_curr = note.pitch.pitch_class
            pc_prev = prev.pitch.pitch_class

            if weighted:
                pcd[pc_prev][pc_curr] += prev.duration * note.duration
            else:
                pcd[pc_prev][pc_curr] += 1

        prev = note


def pcdist2(score: Score, weighted=True) -> list[list[float]]:
    """Returns the 2nd order pitch-class distribution of a musical score.

    Args:
        score (Score): The musical score to analyze.
        weighted (bool, optional): If True, the pitch-class distribution is
                                   weighted by note durations.

    Returns:
        list[list[float]]: A 12x12 matrix where PCD[i][j] represents the
                           probability of transitioning from pitch class
                           i to j. The pitch classes are (C, C#, D, D#,
                           E, F, F#, G, G#, A, A#, B). If the score is empty,
                           the function returns a list with all elements
                           set to zero.
    """
    pcd = [[0] * 12 for _ in range(12)]

    for container in score.note_containers():
        notes = container.find_all(Note)
        update_pcd(pcd, notes, weighted)

    total = sum(sum(row) for row in pcd)
    if total > 0:
        pcd = [[value / total for value in row] for row in pcd]

    return pcd
