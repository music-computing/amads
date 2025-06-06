"""
Number of notes per beat or second in a Score.

Author:
    Tai Nakamura (2025)

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=77
"""

from typing import Optional

from ..core.basics import Score

__author__ = "Tai Nakamura"


def notedensity(score: Score, timetype: Optional[str] = "beat") -> float:
    """
    Returns the number of notes per beat or second in a Score as a float.

    Specifically, it computes note density as (number of notes - 1) divided by
    the time span from the first note onset to the last note onset.
    The subtraction of 1 ensures that density is measured in terms
    of intervals between notes.
    If there are no notes, it returns 0.0.

    Parameters
    ----------
    score (Score): The musical score to analyze.
    timetype (str, optional, default='beat'):
        Time unit for calculation:
        - 'beat': notes per beat (default)
        - 'sec' : notes per second

    Returns
    -------
    float
        Computed note density. Returns 0.0 if the score
        is empty or if all notes have the same onset time
        (i.e., time span equals zero).

    Raises
    ------
    ValueError
        If 'timetype' is not 'beat' or 'sec'.

    """
    notes = score.get_sorted_notes()
    if not notes:
        return 0.0

    if timetype == "sec":
        if score.units_are_seconds:
            start_onset = notes[0].onset
            end_onset = notes[-1].onset
        else:
            start_onset = score.time_map.beat_to_time(notes[0].onset)
            end_onset = score.time_map.beat_to_time(notes[-1].onset)
    elif timetype == "beat":
        if score.units_are_seconds:
            start_onset = score.time_map.time_to_beat(notes[0].onset)
            end_onset = score.time_map.time_to_beat(notes[-1].onset)
        else:
            start_onset = notes[0].onset
            end_onset = notes[-1].onset
    else:
        raise ValueError(f"Invalid timetype: {timetype}. Use 'beat' or 'sec'.")
    duration = end_onset - start_onset
    if duration <= 0:
        return 0.0
    return (len(notes) - 1) / duration
