"""
Melodic accent salience according to Thomassen's model.

Ports the `melaccent` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 70.
"""

import math
from typing import Optional

from amads.core.basics import Note, Score


def melodic_accent(score: Score) -> Optional[Score]:
    """
    Calculate melodic accent salience according to Thomassen's model.

    In this function, each window consists of 3 consecutive notes in a
    monophonic score.

    Melodic accent is determined by analyzing patterns of the following:
    (1) the pitch-change pattern for the current window.
    (2) the pitch-change pattern for the previous window

    Parameters
    ----------
    score : Score
        A Score object containing the monophonic melody to analyze.

    Returns
    -------
    Optional[Score]
        A list of accent values between 0 and 1 for each note. First note
        has accent value of 1.

    Examples
    --------
    >>> score = Score.from_melody([60, 64, 62])
    >>> annotated_score = melodic_accent(score)
    """

    # Handle empty score
    if not score.ismonophonic():
        return None

    length_req_iter = score.find_all(Note)
    # Need at least 3 notes to form a 3-note window
    for _ in range(3):
        note = next(length_req_iter, None)
        if note is None:
            return None

    notes_iter = score.find_all(Note)
    comparing_notes = (next(notes_iter, None), next(notes_iter, None))
    assert all(note is not None for note in comparing_notes)

    annotation_name = "melodic_accent"

    prev_note, current_note = comparing_notes
    prev_note.set(annotation_name, 1)
    current_note.set(annotation_name, 0)
    # Analyze each three-note window
    for next_note in notes_iter:
        # obtain first 2 notes for the 3-note window
        prev_note, current_note = comparing_notes
        # Calculate intervals between adjacent notes
        prev_interval = current_note.key_num - prev_note.key_num
        next_interval = next_note.key_num - current_note.key_num

        # Assign accent values based on Thomassen's model:
        if prev_interval == 0 and next_interval == 0:
            # 3 repeated notes in the pitch window
            current_coef, next_coef = 0.00001, 0.0
        elif prev_interval != 0 and next_interval == 0:
            # 2 trailing notes are the same in the window
            current_coef, next_coef = 1, 0.0
        elif prev_interval == 0 and next_interval != 0:
            # 2 leading notes are the same in the window
            current_coef, next_coef = 0.00001, 1
        elif prev_interval > 0 and next_interval < 0:
            # Peak accent (up-down pattern)
            current_coef, next_coef = 0.83, 0.17
        elif prev_interval < 0 and next_interval > 0:
            # Valley accent (down-up pattern)
            current_coef, next_coef = 0.71, 0.29
        elif prev_interval > 0 and next_interval > 0:
            # Continuous ascending pattern
            current_coef, next_coef = 0.33, 0.67
        elif prev_interval < 0 and next_interval < 0:
            # Continuous descending pattern
            current_coef, next_coef = 0.5, 0.5
        else:
            raise RuntimeError(
                "how did we end up in a case that " "is an impossibility?"
            )

        current_val = current_note.get(annotation_name, None)
        # simple sanity check if current note value has been annotated from a
        # previous iteration
        assert current_val is not None
        # filter the non-zero components and multiply them for the current
        # middle note in the pitch window
        current_coefs = [current_coef, current_val]
        combined_coef = math.prod(coef for coef in current_coefs if coef != 0)
        current_note.set(annotation_name, combined_coef)
        # set initial coefficient for next note value
        next_note.set(annotation_name, next_coef)
        # update 3-note window for next iteration
        comparing_notes = (current_note, next_note)

    return score
