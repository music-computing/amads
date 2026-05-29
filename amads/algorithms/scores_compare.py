"""compare two Score objects

"""

from math import isclose
from typing import Tuple, cast

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
        pitch = event.pitch
        return pitch.key_num - pitch.alt * 0.001 if pitch else 0
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


def scores_compare(score1: Event, score2: Event, midi: bool = False) -> bool:
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
            ts2 = cast(TimeSignature, score2)
            if score1.upper != ts2.upper:
                _score_compare_error(
                    "TimeSignature uppers do not match:",
                    score1,
                    score1.upper,
                    ts2,
                    ts2.upper,
                    "upper is",
                )
                return False
            if score1.lower != ts2.lower:
                _score_compare_error(
                    "TimeSignature lowers do not match:",
                    score1,
                    score1.lower,
                    ts2,
                    ts2.lower,
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


def _report_unmatched(
    silent: bool,
    heading: bool,
    name: str,
    unmatched: Note,
    name1: str,
    name2: str,
    early_stop: bool,
):
    if silent:
        return
    if not heading:
        print(f"Score differences found comparing {name1} to {name2}:")
    print(f"    Unmatched note in {name}:", unmatched)
    if early_stop:
        print("    Stopping after first mismatch.")
    return True


def notes_compare(
    score1: Score,
    name1: str,
    score2: Score,
    name2: str,
    check_offsets: bool = True,
    spelling: bool = False,
    tolerance: float = 0.001,
    early_stop: bool = False,
    silent: bool = False,
) -> Tuple[bool, list[Note], list[Note], float, float]:
    """Compare the notes in two Scores for approximate pitch and time match.

    This function ignores score structure and parts. It only compares extracted
    notes. Options allow you to: ignore small time differences, ignore duration,
    and/or ignore pitch spellings.

    By default, two notes are considered a match if their pitches are equal
    and their onset and offset times are within tolerance of each other. If
    check_offsets is False, then only onsets are compared. If spelling is True,
    then pitch spelling (e.g. F# vs Gb) is also compared.

    Normally, tolerance is expected to be small (e.g. 0.001 seconds) to allow
    for small time differences and possible reordering of notes in chords. If
    tolerance is large, run time will suffer due to linear search for matches
    within time span determined by tolerance, and the "greedy" matching
    strategy may not find the "best" match, leading to reports of mismatched
    notes that really had a good match but where "true" matching note was
    paired with some other note further away in time. This would imply that
    some "true" mismatch was not reported because a poor match was found.
    We believe that the algorithm will find the optimal *number* of matches
    but not the optimal (minimum) max_onset_diff or max_offset_diff for that
    number of matches. (Proof or counterexample is welcome!)

    Ties are tricky: if the score has no ties, we can extract all the notes
    and compare them. When we return unmatched notes, they will reference
    the actual Note objects in the score. But if there *are* ties, we have
    to remove the ties, which creates a copy of the score. Then, unmatched
    notes will *not* reference the original Note objects in the score.
    Instead, unmatched notes will be Notes in the copied score without ties.
    This can be confusing, so we search both scores for tied notes and
    only copy a score if a tie is found.

    Parameters
    ----------
    score1 : Score
        First score to compare
    name1 : str
        A name for the first score, used in error messages.
    score2 : Score
        Second score to compare
    name2 : str
        A name for the second score, used in error messages.
    check_offsets : bool, optional
        If True, compare note offsets as well as onsets, by default True.
    spelling : bool, optional
        If True, compare pitch spelling as well as pitch class,
        by default False.
    tolerance : float, optional
        Maximum allowed difference in onsets and offsets for notes to be
        considered a match, by default 0.001 seconds.
    early_stop : bool, optional
        If True, stop at the first mismatch and return.
    silent : bool, optional
        If True, do not print unmatched notes, by default False.

    Returns
    -------
    Tuple[bool, list[Note], list[Note], max_onset_diff, max_offset_diff]
        A tuple containing a boolean indicating whether the notes match,
        a list of unmatched notes from score1, a list of unmatched notes
        from score2, the maximum onset time difference observed between
        matched notes and the maximum offset time difference observed
        between matched notes.

    <small>**Author**: Roger B. Dannenberg</small>
    """
    heading = False  # have we printed a heading for unmatched reports?
    notes1 = score1.get_sorted_notes(has_ties=score1.has_ties())
    notes2 = score2.get_sorted_notes(has_ties=score2.has_ties())
    unmatched1 = []
    unmatched2 = []
    max_onset_diff = 0.0
    max_offset_diff = 0.0
    i_min = 0  # index of first note in notes2 that is within tolerance of
    # current note in notes1
    candidates = []  # list of candidate notes in notes2 that are not matched
    # yet and within tolerance
    # algorithm: for each note in score1, remove from candidates any notes
    # that are too early and move them to unmatched2, then extend candidates
    # with any notes that are now within tolerance, then search candidates
    # for a match, and if found, remove from candidates. If no match is found,
    # append the note from score1 to unmatched1. If early_stop is True, stop
    # at the first mismatch and return.
    for n1 in notes1:
        # remove unmatchable notes from candidates and move to unmatched2
        while (
            len(candidates) > 0 and candidates[0].onset < n1.onset - tolerance
        ):
            unmatched2.append(candidates[0])
            heading = _report_unmatched(
                silent, heading, name2, candidates[0], name1, name2, early_stop
            )
            if early_stop:
                return (
                    False,
                    unmatched1,
                    unmatched2,
                    max_onset_diff,
                    max_offset_diff,
                )
            candidates.pop(0)
        # add new candidates within tolerance
        while (
            i_min < len(notes2) and notes2[i_min].onset <= n1.onset + tolerance
        ):
            candidates.append(notes2[i_min])
            i_min += 1

        for c in candidates:
            if (
                (
                    (not spelling)
                    and (c.key_num == n1.key_num)
                    or (c.pitch == n1.pitch)
                )
                and (abs(c.onset - n1.onset) < tolerance)
                and (
                    (not check_offsets)
                    or (abs(c.offset - n1.offset) < tolerance)
                )
            ):
                candidates.remove(c)
                max_onset_diff = max(max_onset_diff, abs(c.onset - n1.onset))
                max_offset_diff = max(
                    max_offset_diff, abs(c.offset - n1.offset)
                )
                break
        else:
            unmatched1.append(n1)
            heading = _report_unmatched(
                silent, heading, name1, n1, name1, name2, early_stop
            )
            if early_stop:
                return (
                    False,
                    unmatched1,
                    unmatched2,
                    max_onset_diff,
                    max_offset_diff,
                )
    # any remaining candidates are unmatched in score2
    for c in candidates:
        unmatched2.append(c)
        heading = _report_unmatched(
            silent, heading, name2, c, name1, name2, early_stop
        )
        if early_stop:
            return (
                False,
                unmatched1,
                unmatched2,
                max_onset_diff,
                max_offset_diff,
            )
    result = len(unmatched1) == 0 and len(unmatched2) == 0
    return (result, unmatched1, unmatched2, max_onset_diff, max_offset_diff)
