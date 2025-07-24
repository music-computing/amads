"""
Shifts all values in a score by a specified amount and specified type.

TODO: comments!

WTF with not allowing import <module> as <name> statements if they are
not in python... flake8...

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=91
"""

from typing import Optional, Union

from ..core.basics import (
    Chord,
    Clef,
    KeySignature,
    Measure,
    Note,
    Part,
    Pitch,
    Rest,
    Score,
    Staff,
    TimeSignature,
)


def rectify_time_to_score(score: Score, timeval: int, timetype: str) -> int:
    """
    returns rectified time value based on the time type in the score
    and the time type for timeval
    """
    if timetype is None:
        return timeval
    elif timetype == "seconds":
        if score.units_are_seconds:
            return timeval
        else:
            return score.time_map.time_to_beat(timeval)
    elif timetype == "quarters":
        if score.units_are_seconds:
            return score.time_map.beat_to_time(timeval)
        else:
            return timeval
    else:
        raise ValueError(f"Invalid timetype: {timetype}. Use 'quarters' or 'seconds'.")


def add_onset(score: Score, rectified_amount: int):
    # while it is possible for me to write a custom recursion
    # and make this more efficient computationally,
    # I still think it is better for us to use methods that are
    # already available to us in py
    # It is invalid for the time to be written in a float.
    score.onset += rectified_amount
    for elem in score.find_all(Part):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(Staff):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(Measure):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(Chord):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(Note):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(Rest):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(KeySignature):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(TimeSignature):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)
    for elem in score.find_all(Clef):
        assert elem.onset is not None
        elem.onset += rectified_amount
        elem.onset = max(elem.onset, 0)

    return


def add_duration(score: Score, rectified_amount: int):
    score.duration += rectified_amount
    for elem in score.find_all(Part):
        assert elem.duration is not None
        elem.duration += rectified_amount
        elem.duration = max(elem.duration, 0)
    for elem in score.find_all(Staff):
        assert elem.duration is not None
        elem.duration += rectified_amount
        elem.duration = max(elem.duration, 0)
    for elem in score.find_all(Measure):
        assert elem.duration is not None
        elem.duration += rectified_amount
        elem.duration = max(elem.duration, 0)
    for elem in score.find_all(Chord):
        assert elem.duration is not None
        elem.duration += rectified_amount
        elem.duration = max(elem.duration, 0)
    for elem in score.find_all(Note):
        assert elem.duration is not None
        elem.duration += rectified_amount
        elem.duration = max(elem.duration, 0)
    for elem in score.find_all(Rest):
        assert elem.duration is not None
        elem.duration += rectified_amount
        elem.duration = max(elem.duration, 0)

    return


def shift(
    score: Score, type: str, amount: Union[int, float], timetype: Optional[str] = None
) -> Optional[Score]:
    """
    For a given score, shifts a given value type by the specified amount.
    """
    if timetype is None:
        timetype = "quarters"

    score_copy = score.deep_copy()

    if type == "dynamic":
        for note in score_copy.find_all(Note):
            if isinstance(note.dynamic, str):
                return None
            elif isinstance(note.dynamic, int):
                note.dynamic += amount
    elif type == "onset":
        # we need to adjust offset for every time-signatured instance in
        # the score...
        corrected_amount = rectify_time_to_score(score_copy, amount, timetype)
        # the problem is, all the events have
        add_onset(score_copy, corrected_amount)
    elif type == "dur":
        # be careful of things like TimeSignature which has 0 duration
        # always...
        corrected_amount = rectify_time_to_score(score_copy, amount, timetype)
        add_duration(score_copy, corrected_amount)
    elif type == "pitch":
        amount = int(amount)
        for note in score_copy.find_all(Note):
            keynum, alt = note.pitch.as_tuple()
            note.pitch = Pitch(keynum + amount, alt)
    else:
        # Note that, in the original implementation midi channel was also
        # a shiftable attribute
        raise ValueError(
            'type must be one of "dynamic", "onset", "dur", \
            or "pitch"'
        )
    return score_copy
