"""
Pitch class distribution analysis.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=80.
"""

from ..core.basics import EventGroup, Note


def pcdist1(noteset: EventGroup, weighted: bool = True) -> list[float]:
    """
    Calculate the pitch-class distribution of a note collection.

    Parameters
    ----------
    noteset
        The collection of notes to analyze
    weighted
        If True, weight the pitch-class distribution by note durations.
        Default is True.

    Returns
    -------
    list[float]
        A 12-element list representing the normalized probabilities of each pitch
        class (C, C#, D, D#, E, F, F#, G, G#, A, A#, B). If the score is empty,
        returns a list with all elements set to zero.
    """
    pcd = [0] * 12

    if weighted:  # no need to merge ties due to weighting
        for note in noteset.find_all(Note):
            pcd[note.pitch_class] += note.duration
    else:  # count tied notes as single notes
        noteset = noteset.merge_tied_notes()
        for note in noteset.find_all(Note):
            pcd[note.pitch_class] += 1
    total = sum(pcd)
    if total > 0:
        pcd = [i / total for i in pcd]
    return pcd
