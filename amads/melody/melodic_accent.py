"""
Melodic accent salience according to Thomassen's model.

Completely rewrites the original calculate_melodic_accent function that
Yiwen Zhao first wrote.

Ports the `melaccent` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 70.
"""

import math
from collections import deque
from itertools import islice, tee

from amads.core.basics import Note, Score


def melodic_accent(score: Score) -> Score | None:
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

    References
    ----------
        Joseph Thomassen, "Melodic accent: Experiments and a tentative model,"
            Journal of the Acoustical Society of America, Vol. 71, No. 6 (1982)
            pp.1598-1605; see also, Erratum, Journal of the Acoustical Society 
            of America, Vol. 73, No. 1 (1983) p.373.
    """

    notes_iter = score.find_all(Note)
    notes_iter, length_check_iter = tee(notes_iter)
    length_check_list = list(islice(length_check_iter, 3))
    if len(length_check_list) < 3:
        return None
    if not score.ismonophonic():
        return None

    annotation_name = "melodic_accent"

    window = deque(islice(notes_iter, 3 - 1), maxlen=3)

    window[0].set(annotation_name, 1)
    window[1].set(annotation_name, 0)
    # Analyze each three-note window
    for note in notes_iter:
        window.append(note)
        prev_note, current_note, next_note = window
        # Calculate intervals between adjacent notes
        prev_interval = current_note.midi_num - prev_note.midi_num
        next_interval = next_note.midi_num - current_note.midi_num

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
                "how did we end up in a case that is an impossibility?"
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

    return score
