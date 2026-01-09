"""compare two Score objects

"""

import math
from typing import cast

from amads.core.basics import (
    Clef,
    Event,
    EventGroup,
    KeySignature,
    Measure,
    Note,
    Part,
    Score,
    Staff,
    TimeSignature,
)

__author__ = "Roger B. Dannenberg"


def compare_time_maps(tm1, tm2):
    """Compare two TimeMaps for equality."""
    if len(tm1.changes) != len(tm2.changes):
        print(
            "TimeMap lengths do not match:", len(tm1.changes), len(tm2.changes)
        )
        return False
    for mq1, mq2 in zip(tm1.changes, tm2.changes):
        if mq1.time != mq2.time:
            print("TimeMap times do not match:", mq1.time, mq2.time)
            return False
        if mq1.quarter != mq2.quarter:
            print("TimeMap quarters do not match:", mq1.quarter, mq2.quarter)
            return False
    return True


def score_compare_error(
    msg, score1, data1, score2, data2, data_phrase: str
) -> None:
    print(msg)
    print(f"  Score 1: {score1}", end="")
    if data1 == "skip":
        data1 = ""
    else:
        data1 = f" {data_phrase} {data1}"
    print(data1)
    print(f"  Score 2: {score2}", end="")
    if data2 == "skip":
        data2 = ""
    else:
        data2 = f" {data_phrase} {data2}"
    print(data2)


def scores_compare(score1: Score, score2: Score, midi: bool = False) -> bool:
    """Compare two Scores for equality.

    If they are different, print the first difference found.

    Ignores Rests and fields in non-standard subclasses of Event, but compares
    Score, Part, Staff, Measure, Note, TimeSignature, KeySignature, Clef.

    If midi, EventGroups are allowed to have non-matching durations because
    some MIDI readers fill out duration to even number of measures and others
    do not.  And Staff numbers do not have to match.

    Parameters
    ----------
    score1 : Event
        First score or event to compare
    score2 : Event
        Second score or event to compare

    Returns
    -------
    bool
        True if the scores/events are equal, False otherwise.

    <small>**Author**: Roger B. Dannenberg</small>
    """
    if not isinstance(score1, Event):
        print("Event or EventGroup from score1 is not an Event", score1)
        return False
    if not isinstance(score2, Event):
        print("Event or EventGroup from score2 is not an Event", score2)
        return False
    if not math.isclose(score1.onset, score2.onset, abs_tol=0.001):
        score_compare_error(
            "Event onsets do not match:",
            score1,
            score1.onset,
            score2,
            score2.onset,
            "onset is",
        )
        return False
    dur_match = math.isclose(score1.duration, score2.duration, abs_tol=0.001)
    if isinstance(score1, EventGroup) and isinstance(score2, EventGroup):
        dur_match = dur_match or midi  # allow non-matching if midi
        content1 = score1.content
        content2 = score2.content
        if midi and isinstance(score1, Measure) and isinstance(score2, Measure):
            # filter non-notes from midi measures -- they're optional
            # measures can also have chords, but they will not appear in midi
            content1 = score1.list_all(Note)
            content2 = score2.list_all(Note)
        if len(content1) != len(content2):
            score_compare_error(
                "EventGroup content lengths do not match:",
                score1,
                len(content1),
                score2,
                len(content2),
                "length is",
            )
            return False
        if isinstance(score1, Score) and isinstance(score2, Score):
            if score1._units_are_seconds != score2._units_are_seconds:
                score_compare_error(
                    "Score units do not match:",
                    score1,
                    score1._units_are_seconds,
                    score2,
                    score2._units_are_seconds,
                    "_units_are_seconds is",
                )
                return False
            if compare_time_maps(score1.time_map, score2.time_map) is False:
                score_compare_error(
                    "Score time maps do not match:",
                    score1,
                    score1.time_map,
                    score2,
                    score2.time_map,
                    "time_map is",
                )
        elif isinstance(score1, Part) and isinstance(score2, Part):
            if score1.instrument != score2.instrument:
                score_compare_error(
                    "Part MIDI programs do not match:",
                    score1,
                    score1.instrument,
                    score2,
                    score2.instrument,
                    "instrument is",
                )
                return False
            if score1.number != score2.number:
                score_compare_error(
                    "Part numbers do not match:",
                    score1,
                    score1.number,
                    score2,
                    score2.number,
                    "number is",
                )
                return False
        elif isinstance(score1, Staff) and isinstance(score2, Staff):
            # staff numbers do not need to match. Only Partitura numbers staffs
            # in MIDI files and numbering is 1, 2, ... within each Part, even
            # though we would expect
            if midi and score1.number != score2.number:
                score_compare_error(
                    "Staff numbers do not match:",
                    score1,
                    score1.number,
                    score2,
                    score2.number,
                    "number is",
                )
                return False
        elif isinstance(score1, Measure) and isinstance(score2, Measure):
            if score1.number != score2.number:
                score_compare_error(
                    "Measure numbers do not match:",
                    score1,
                    score1.number,
                    score2,
                    score2.number,
                    "number is",
                )
                return False
        for elem1, elem2 in zip(content1, content2):
            if not scores_compare(elem1, elem2, midi):
                return False
    else:  # both are Events
        # compare to makes sure they have the same class
        if score1.__class__ != score2.__class__:
            score_compare_error(
                "Event classes do not match:",
                score1,
                score1.__class__,
                score2,
                score2.__class__,
                "class is",
            )
            return False
        if isinstance(score1, Note):
            score2 = cast(Note, score2)
            if score1.pitch != score2.pitch:
                score_compare_error(
                    "Note pitches do not match:",
                    score1,
                    score1.pitch,
                    score2,
                    score2.pitch,
                    "pitch is",
                )
                return False
            if score1.dynamic != score2.dynamic:
                score_compare_error(
                    "Note velocities do not match:",
                    score1,
                    score1.dynamic,
                    score2,
                    score2.dynamic,
                    "dynamic is",
                )
                return False
            if score1.lyric != score2.lyric:
                score_compare_error(
                    "Note lyrics do not match:",
                    score1,
                    score1.lyric,
                    score2,
                    score2.lyric,
                    "lyric is",
                )
                return False
            if score1.tie or score2.tie:
                if not score2.tie:
                    score_compare_error(
                        "score1 has tie but score2 does not:",
                        score1,
                        score1.tie,
                        score2,
                        "skip",
                        "tie is",
                    )
                    return False
                elif not score1.tie:
                    score_compare_error(
                        "score2 has tie but score1 does not:",
                        score1,
                        "skip",
                        score2,
                        score2.tie,
                        "tie is",
                    )
                    return False
                elif not scores_compare(score1.tie, score2.tie):
                    score_compare_error(
                        "Tied notes do not match:",
                        score1,
                        score1.tie,
                        score2,
                        score2.tie,
                        "tied note is",
                    )
                    return False
                return True
        elif isinstance(score1, TimeSignature):
            score2 = cast(TimeSignature, score2)
            if score1.upper != score2.upper:
                score_compare_error(
                    "TimeSignature uppers do not match:",
                    score1,
                    score1.upper,
                    score2,
                    score2.upper,
                    "upper is",
                )
                return False
            if score1.lower != score2.lower:
                score_compare_error(
                    "TimeSignature lowers do not match:",
                    score1,
                    score1.lower,
                    score2,
                    score2.lower,
                    "lower is",
                )
                return False
        elif isinstance(score1, KeySignature):
            score2 = cast(KeySignature, score2)
            if score1.key_sig != score2.key_sig:
                score_compare_error(
                    "KeySignature key_sigs do not match:",
                    score1,
                    score1.key_sig,
                    score2,
                    score2.key_sig,
                    "key_sig is",
                )
                return False
        elif isinstance(score1, Clef):
            score2 = cast(Clef, score2)
            if score1.clef != score2.clef:
                score_compare_error(
                    "Clef types do not match:",
                    score1,
                    score1.clef,
                    score2,
                    score2.clef,
                    "clef is",
                )
                return False
        if not dur_match:
            score_compare_error(
                "Event durations do not match:",
                score1,
                score1.duration,
                score2,
                score2.duration,
                "duration is",
            )
            return False

    return True
