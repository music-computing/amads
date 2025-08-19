"""
Number of notes per quarter or second in a Score.

Author:
    Tai Nakamura (2025)

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=77
"""

from typing import Optional

from ..core.basics import Score

__author__ = "Tai Nakamura"


def notedensity(score: Score, timetype: Optional[str] = "quarters") -> float:
    """
    Returns the number of notes per quarter or second in a Score as a float.

    Specifically, it computes note density as (number of notes - 1) divided by
    the time span from the first note onset to the last note onset.
    The subtraction of 1 ensures that density is measured in terms
    of intervals between notes.
    If there are no notes, it returns 0.0.

    Parameters
    ----------
    score (Score): The musical score to analyze.
    timetype (str, optional, default='quarters'):
        Time unit for calculation:
        - 'quarters': notes per quarter (default)
        - 'seconds' : notes per second

    Returns
    -------
    float
        Computed note density. Returns 0.0 if the score
        is empty or if all notes have the same onset time
        (i.e., time span equals zero).

    Raises
    ------
    ValueError
        If 'timetype' is not 'quarters' or 'seconds'.

    Examples
    --------
    >>> score = Score.from_melody([60, 62, 64, 65])  # all quarter notes
    >>> notedensity(score, timetype='quarters')
    1.0
    >>> from amads.core.timemap import TimeMap
    >>> score = Score.from_melody([60, 62, 64, 65])  # all quarter notes
    >>> score.time_map = TimeMap(bpm = 120)  # set BPM to 120
    >>> notedensity(score, timetype='seconds')
    2.0
    >>> score = Score.from_melody([60, 62, 64, 65], durations = [1.0, 2.0, 3.0, 4.0])  # mixed durations
    >>> notedensity(score, timetype='quarters')
    0.5
    """
    notes = score.get_sorted_notes()
    if not notes:
        return 0.0

    if timetype == "seconds":
        if score.units_are_seconds:
            start_onset = notes[0].onset
            end_onset = notes[-1].onset
        else:
            start_onset = score.time_map.beat_to_time(notes[0].onset)
            end_onset = score.time_map.beat_to_time(notes[-1].onset)
    elif timetype == "quarters":
        if score.units_are_seconds:
            start_onset = score.time_map.time_to_beat(notes[0].onset)
            end_onset = score.time_map.time_to_beat(notes[-1].onset)
        else:
            start_onset = notes[0].onset
            end_onset = notes[-1].onset
    else:
        raise ValueError(f"Invalid timetype: {timetype}. Use 'quarters' or 'seconds'.")
    duration = end_onset - start_onset
    if duration <= 0:
        return 0.0
    return (len(notes) - 1) / duration
