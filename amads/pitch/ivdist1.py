"""
Provides the `ivdist1` function

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=63
"""

from ..core.basics import Note, Score
from .ismonophonic import ismonophonic


def update_id(id: list[float], notes: list[Note], weighted: bool):
    """Updates the interval distribution list based on the given notes.

    Serves as a helper function for `ivdist1`

    Args:
        id (list[float]): The interval distribution list to be updated.
        notes (list[Note]): The list of notes to process.
        weighted (bool): If True, the interval distribution is weighted
                         by note durations.
    """
    prev = None
    for note in notes:
        if prev:
            num_curr = note.num
            num_prev = prev.num

            diff = round(num_curr - num_prev)

            # Ignore intervals greater than an octave
            if abs(diff) <= 12:
                if weighted:
                    # Since diff ranges from -12 to 12,
                    # diff + 12 prevents negative indicies
                    id[diff + 12] += prev.duration * note.duration
                else:
                    id[diff + 12] += 1

        prev = note


def ivdist1(score: Score, weighted=True) -> list[float]:
    """
    Returns the interval distribution of a musical score.

    Currently, intervals greater than an octave will be ignored.

    Args:
        score (Score): The musical score to analyze
        weighted (bool, optional): If True, the interval distribution is
                                   weighted by note durations (default True)

    Returns:
        list[float]: A 25-element list representing the normalized
                     probabilities of each interval. The components are spaced
                     at semitone distances with the first component
                     representing the downward octave and the last component
                     the upward octave. If the score is empty, the
                     function returns a list with all elements set to zero.

    Raises:
        Exception: If the score is not monophonic (e.g. contains chords)
    """
    if not ismonophonic(score):
        raise Exception("Error: Score must be monophonic")

    id = [0] * 25  # interval distribution list

    for container in score.note_containers():
        notes = container.find_all(Note)
        update_id(id, notes, weighted)

    total = sum(id)
    if total > 0:
        id = [value / total for value in id]

    return id
