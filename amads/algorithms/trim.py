"""
Implementation of the trim() function, which removes leading silence, from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 93

"""

from amads.core.basics import Score


def trim(score: Score) -> Score:
    """
    Removes all leading silence from a given score such that the first note starts at time 0.0.

    trim() returns a new, flattened score to ensure that the original score is not altered.

    Parameters
    ----------
    score: Score
        The score that is to be trimmed.

    Returns
    -------
    Score
        A new, trimmed, and flattened score.

    """
    # 1. Get a flattened version of the score
    flat_score = score.flatten()

    # 2. Get all the notes in the score in sorted order (to get the first note)
    notes = flat_score.get_sorted_notes()

    # 2a. If it's empty, return it
    if not notes:
        return flat_score

    # 3. Calculate how much we need to shift the score.
    # If the first note starts at time n, we want to shift everything by -n to make it start at time 0.0
    first_note = notes[0]
    shift_amount = -first_note.onset

    # 4. Use the time_shift method to move all notes in the score
    flat_score.time_shift(shift_amount)
    return flat_score
