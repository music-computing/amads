"""compare two Score objects

"""

from math import isclose
from typing import cast

from amads.core.basics import (
    Chord,
    Clef,
    Event,
    EventGroup,
    KeySignature,
    Measure,
    Note,
    Part,
    Rest,
    Score,
    Staff,
    TimeSignature,
)

__author__ = "Roger B. Dannenberg"


def _time_map_error(msg, x1, x2, tm1, tm2):
    """print time_map error and data"""
    print(msg, x1, x2)
    print("    tm1: ", end="")
    tm1.show()
    print("    tm2: ", end="")
    tm2.show()


def compare_time_maps(tm1, tm2):
    """Compare two TimeMaps for equality."""
    if len(tm1.changes) != len(tm2.changes):
        return _time_map_error(
            "TimeMap lengths do not match:",
            len(tm1.changes),
            len(tm2.changes),
            tm1,
            tm2,
        )
    for mq1, mq2 in zip(tm1.changes, tm2.changes):
        if not isclose(mq1.time, mq2.time, abs_tol=1e-3):
            return _time_map_error(
                "TimeMap times do not match:", mq1.time, mq2.time, tm1, tm2
            )
        if not isclose(mq1.quarter, mq2.quarter, abs_tol=1e-3):
            return _time_map_error(
                "TimeMap quarters do not match:",
                mq1.quarter,
                mq2.quarter,
                tm1,
                tm2,
            )
    return True


def _score_compare_error(
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


def _pitch_dim(event: Event) -> float:
    """compute a number for sorting events if onsets are equal

    We want Clef < KeySignature < Note, and Notes ordered by key_num
    and then alt.

    This function is not completely correct because if two key_nums
    are very close (on the order of 0.001), and have different alt
    values, they could be returned out of order, but in "normal" music,
    key_num values are separated by 1 or at least some audible difference.
    """
    if isinstance(event, Clef):
        return -10
    elif isinstance(event, KeySignature):
        return -5
    elif isinstance(event, Note):
        pitch = cast(Note, event).pitch
        return pitch.key_num - pitch.alt * 0.001
    return 0


def _all_but_rests_and_chords(measure: Measure, midi: bool) -> list[Event]:
    """
    returns content except rests and chords, but include chord content

    An additional hack is to remove KeySignature(onset=0, 0 flats) because
    this is implied but created anyway (only) by Music21.

    Similarly, if this is midi, Music21 may create Clefs, but Clef is not
    supported by MIDI so we remove them.

    The returned list is sorted in order of increasing time and pitch.
    """
    content = []
    for item in measure.content:
        if isinstance(item, Chord):
            for citem in item.content:  # move chord content to our content
                if not isinstance(citem, Rest):
                    content.append(citem)  # nested chords are NOT expanded
                    # but nested chords should not exist
        elif midi and isinstance(item, Clef):
            pass
        elif (
            isinstance(item, KeySignature)
            and item.onset == 0
            and item.key_sig == 0
        ):
            pass
        elif not isinstance(item, Rest):
            content.append(item)
    content.sort(key=lambda x: (x.onset, _pitch_dim(x)))
    return content


def scores_compare(score1: Score, score2: Score, midi: bool = False) -> bool:
    """Compare two Scores for equality.

    If they are different, print the first difference found.

    Ignores Rests, Chords and fields in non-standard subclasses of Event,
    but compares Score, Part, Staff, Measure, Note, TimeSignature,
    KeySignature, Clef.

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
    if not isclose(score1.onset, score2.onset, abs_tol=0.001):
        _score_compare_error(
            "Event onsets do not match:",
            score1,
            score1.onset,
            score2,
            score2.onset,
            "onset is",
        )
        return False
    dur_match = isclose(score1.duration, score2.duration, abs_tol=0.001)
    if isinstance(score1, EventGroup) and isinstance(score2, EventGroup):
        dur_match = dur_match or midi  # allow non-matching if midi
        content1 = score1.content
        content2 = score2.content
        if isinstance(score1, Measure) and isinstance(score2, Measure):
            # filter Rests and Chords from measures -- they're optional,
            # and MusicXML readers handle things differently
            content1 = _all_but_rests_and_chords(score1, midi)
            content2 = _all_but_rests_and_chords(score2, midi)

        if len(content1) != len(content2):
            _score_compare_error(
                "EventGroup content lengths do not match:",
                score1,
                len(content1),
                score2,
                len(content2),
                "length is",
            )
            print("    from score1:")
            for c in content1:
                print("        ", c)
            print("    from score2:", content2)
            for c in content2:
                print("        ", c)
            return False
        if isinstance(score1, Score) and isinstance(score2, Score):
            if score1._units_are_seconds != score2._units_are_seconds:
                _score_compare_error(
                    "Score units do not match:",
                    score1,
                    score1._units_are_seconds,
                    score2,
                    score2._units_are_seconds,
                    "_units_are_seconds is",
                )
                return False
            if compare_time_maps(score1.time_map, score2.time_map) is False:
                _score_compare_error(
                    "Score time maps do not match:",
                    score1,
                    score1.time_map,
                    score2,
                    score2.time_map,
                    "time_map is",
                )
        elif isinstance(score1, Part) and isinstance(score2, Part):
            # instruments should match, but in PrettyMIDI, if the
            # track name is empty, the instrument name is derived
            # from the General MIDI instrument corresponding to the
            # MIDI program used in the track, defaulting to 0,
            # which is "Acoustic Grand Piano":
            if (score1.instrument != score2.instrument) and (
                (not midi)
                or (
                    (score1.instrument is not None)
                    and (score2.instrument is not None)
                )
            ):
                _score_compare_error(
                    "Part MIDI instruments do not match:",
                    score1,
                    score1.instrument,
                    score2,
                    score2.instrument,
                    "instrument is",
                )
                return False
            if score1.number != score2.number:
                _score_compare_error(
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
                _score_compare_error(
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
                _score_compare_error(
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
            _score_compare_error(
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
            if (midi and (score1.key_num != score2.key_num)) or (
                (not midi) and (score1.pitch != score2.pitch)
            ):
                _score_compare_error(
                    "Note pitches do not match:",
                    score1,
                    score1.pitch,
                    score2,
                    score2.pitch,
                    "pitch is",
                )
                return False
            if score1.dynamic != score2.dynamic:
                _score_compare_error(
                    "Note velocities do not match:",
                    score1,
                    score1.dynamic,
                    score2,
                    score2.dynamic,
                    "dynamic is",
                )
                return False
            if score1.lyric != score2.lyric:
                _score_compare_error(
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
                    _score_compare_error(
                        "score1 has tie but score2 does not:",
                        score1,
                        score1.tie,
                        score2,
                        "skip",
                        "tie is",
                    )
                    return False
                elif not score1.tie:
                    _score_compare_error(
                        "score2 has tie but score1 does not:",
                        score1,
                        "skip",
                        score2,
                        score2.tie,
                        "tie is",
                    )
                    return False
                elif not scores_compare(score1.tie, score2.tie):
                    _score_compare_error(
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
                _score_compare_error(
                    "TimeSignature uppers do not match:",
                    score1,
                    score1.upper,
                    score2,
                    score2.upper,
                    "upper is",
                )
                return False
            if score1.lower != score2.lower:
                _score_compare_error(
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
                _score_compare_error(
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
                _score_compare_error(
                    "Clef types do not match:",
                    score1,
                    score1.clef,
                    score2,
                    score2.clef,
                    "clef is",
                )
                return False
        if not dur_match:
            _score_compare_error(
                "Event durations do not match:",
                score1,
                score1.duration,
                score2,
                score2.duration,
                "duration is",
            )
            return False

    return True
