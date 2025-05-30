"""
Provides the `ivdist2` function

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=64
"""

from ..core.basics import Note, Score
from .ismonophonic import ismonophonic


def update_id(id: list[list[float]], notes: list[Note], weighted: bool):
    """
    Updates the interval distribution list based on the given notes.

    Serves as a helper function for `ivdist2`

    Args:
        id (list[list[float]]): The interval distribution list to be updated.
        notes (list[Note]): The list of notes to process.
        weighted (bool): If True, the interval distribution is weighted
                         by note durations.
    """

    prev_note = None
    prev_prev_note = None  # used to calculate weight
    for note in notes:
        if prev_note:
            if prev_prev_note:
                key_num_curr = note.key_num
                key_num_prev = prev_note.key_num
                key_num_prev_prev = prev_prev_note.key_num

                diff = round(key_num_curr - key_num_prev)
                prev_diff = round(key_num_prev - key_num_prev_prev)

                # Ignore intervals greater than an octave
                if abs(diff) <= 12 and abs(prev_diff) <= 12:
                    if weighted:
                        # Since diff ranges from -12 to 12,
                        # diff + 12 prevents negative indicies
                        # May need a better algorithm to calculate weight
                        id[prev_diff + 12][diff + 12] += (
                            prev_prev_note.duration * prev_note.duration * note.duration
                        )
                    else:
                        id[prev_diff + 12][diff + 12] += 1
            prev_prev_note = prev_note
        prev_note = note

    # The following implementation looks cleaner but may be costly if the
    # notes generator is large

    # notes = list(notes)  # convert to list since it's a generator

    # for i in range(2, len(notes)):
    #     if i >= 2:
    #         key_num_curr = notes[i].key_num
    #         key_num_prev = notes[i-1].key_num
    #         key_num_prev_prev = notes[i-2].key_num

    #         diff = key_num_curr - key_num_prev
    #         prev_diff = key_num_prev - key_num_prev_prev

    #         # Ignore intervals greater than an octave
    #         if abs(diff) <= 12 and abs(prev_diff) <= 12:
    #             if weighted:
    #                 # Since diff ranges from -12 to 12,
    #                 # diff + 12 prevents negative indicies
    #                 # May need a better algorithm to calculate weight
    #                 id[prev_diff + 12][diff + 12] += (notes[i-2].duration
    #                                                   * notes[i-1].duration
    #                                                   * notes[i].duration)
    #             else:
    #                 id[prev_diff + 12][diff + 12] += 1


def ivdist2(score: Score, weighted=True) -> list[list[float]]:
    """
    Returns the 2nd-order interval distribution of a musical score.

    Currently, intervals greater than an octave will be ignored.

    Args:
        score (Score): The musical score to analyze
        weighted (bool, optional): If True, the interval distribution is
                                   weighted by note durations (default True)

    Returns:
        list[list[float]]: A 25x25 matrix where (i,j) represents the normalized
                           probabilities of transitioning from interval i to
                           interval j. Refer to the documentation for ivdist1
                           for the index of each interval. If the score is
                           empty, the function returns a matrix with all
                           elements set to zero.

    Raises:
        Exception: If the score is not monophonic (e.g. contains chords)
    """
    if not ismonophonic(score):
        raise Exception("Error: Score must be monophonic")

    id = [[0] * 25 for _ in range(25)]  # interval distribution matrix

    score = score.merge_tied_notes()  # merges tied notes
    notes = score.list_all(Note)
    update_id(id, notes, weighted)

    total = sum(sum(row) for row in id)
    if total > 0:
        id = [[value / total for value in row] for row in id]

    return id
