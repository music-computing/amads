"""pt_xml_import.py - Partitura XML import and conversion to AMADS"""

__author__ = "Roger B. Dannenberg"

import warnings
from math import isclose
from typing import Optional

import partitura as pt
from partitura import score as ptScore

from amads.core.basics import (
    Chord,
    Clef,
    KeySignature,
    Measure,
    Note,
    Part,
    Rest,
    Score,
    Staff,
    TimeSignature,
)
from amads.core.pitch import Pitch

# plan: multiple passes over iter_all()
# for each part: add the part to a Concurrence
#      1st pass: get staff numbers from notes, extract measures, get div/qtr
#           create a Concurrence of staves if more than one,
#           create measures in each staff
#      2nd pass (A): get notes, rests, insert parameters into lists
#      2nd pass (B): build Note and Rest objects, insert into Measures
#      2nd pass (C): set ties attribute of Notes ?

# Partitura seems to have a rounding error, reporting measure length
# of 1919 instead of 1920 when divs per quarter is 480. This can lead
# to measures with fractional duration (e.g. 3.997916666666667) and
# the insertion of ties across measure boundaries that are in the
# wrong place. When DIV_TO_QUARTER_ROUNDING is not None, measure
# durations are rounded to the nearest 1/DIV_TO_QUARTER_ROUNDING of
# a quarter note. Do not round to whole beats because there might
# be a fractional measure with a pickup note. 24 allows for 32nd
# notes and 64th-note triplets (1/24 beat). Rounding must be enabled
# also by passing rnd=True to div_to_quarter(). The intent is to
# round measure boundaries but not note start/duration (because note
# times can be from a MIDI performance, where time is not quantized,
# at least not to symbolic durations or beats.)
#
DIV_TO_QUARTER_ROUNDING = 96

# algorithm: multiple passes over iter_all()
# for each part: add the part to a Concurrence
#      1st pass: get staff numbers from notes, extract measures, get div/qtr
#           create a Concurrence of staves if more than one,
#           create measures in each staff
#           build a map from every 10 beats to the Staff content index of a
#               measure that starts after that time. (to make it fast to find
#               measures - see description below)
#      2nd pass: get notes, rests, insert parameters into lists
#      3rd pass: re-tie notes that cross measures in case the measure boundary
#           has moved due to rounding
#      4th pass: build Note and Rest objects, insert into Measures
# measure_map: a list of indices into the Staff content list such that for any
#     time t, staff.content[measure_map[int(t/10)]].onset <= t and
#     staff.content[measure_map[int(t/10) + 1]].onset > t. Intuitively,
#     we find index i = int(t/10), and we're guaranteed that measure indexed by
#     measure_map[i] starts at or before time t. We can then search forward to
#     find the measure that contains t.
# Besides the measures map, we have a map pt_note_to_note from partitura note id
#     to both events and Note objects (as a list [event, note]) so we can find
#     the notes to adjust when we process ties.


def find_measure_ending_after(staff: Staff, time: float) -> Optional[Measure]:
    """Find the first measure in the staff that ends after time.
    staff - the Staff object
    time - the time to find the measure after

    Returns
    -------
      Measure - the first measure that ends after time
    """
    i = int(time / 10)
    if i >= len(measure_map):
        return None  # there are no measures to search
    i = measure_map[int(time / 10)]
    assert i < len(staff.content) and staff.content[i].onset <= time
    # now i is a known lower bound on the result we want
    i += 1
    while i < len(staff.content) and staff.content[i].onset <= time:
        i += 1
    # either staff.content[i] does not exist or onset of measure i is too high
    # either way, we want the previous measure:
    return staff.content[i - 1]


def div_to_quarter(durs, div, rnd=False):
    """given an array of (div, divs_per_qtr), map from div to quarter.
    This is not efficient if the array is large, i.e. if divs_per_qtr
    changes many times, which I assume is very unusual. Use this instead
    of quarter_map() because the latter maps partial first measure (pickup
    notes) to negative times, whereas we call the first event (rest or note)
    quarter 0. If rnd is True and DIV_TO_QUARTER_ROUNDING is not None,
    round the result to the nearest multiple of 1/DIV_TO_QUARTER_ROUNDING.
    """
    i = 0
    qtrs = 0
    while i + 1 < len(durs) and div > durs[i + 1][0]:
        # sum intervening quarters to this new time point:
        qtrs += (durs[i + 1][0] - durs[i][0]) / durs[i][1]
        i += 1
    # add quarters from last time point to "now" (div):
    qtrs += (div - durs[i][0]) / durs[i][1]
    if rnd and (DIV_TO_QUARTER_ROUNDING is not None):
        qtrs = round(qtrs * DIV_TO_QUARTER_ROUNDING) / DIV_TO_QUARTER_ROUNDING
    # print("div_to_quarter: div", div, "qtrs", qtrs)
    return qtrs


def if_tied(note: ptScore.Note) -> bool:
    """Given a partitura note, return the note itself if it is
    either tied-to or tied-from. Otherwise, return None.
    """
    return (note.tie_prev or note.tie_next) is not None


def retie_notes(event, staff, rnd: bool):
    """Adjust tied notes that cross barlines

    This method accounts for rounding in Partitura that can change
    measure timing. It adjusts the onsets and durations of tied notes
    so that ties occur at measure boundaries when they are already
    close, sometimes eliminating tied notes very small durations.

    event - the start of the tied note group
    staff - the staff containing the rest of the measures
    rnd - if True, apply rounding to measure boundaries (default True)

    Algorithm:
    If event is for a note tied to another note but not tied-from
    another note, e.g. it is the first in a tied group, find all tied
    notes using pt_note_to_note. Then for each note in order, if it is
    tied to the next note and the end time rounds to a bar time, then
    replace the end time with the bar time and replace the next note
    onset and duration to move the start time to the bar time. If the
    resulting duration is < 0.001, assume it was created through
    rounding error and set it to zero. (This could slightly truncate
    performance notes, but imperceptibly.) In the next pass, set the
    tied attribute to None if the tied-to note has duration 0 and ignore
    notes with duration of 0, which now indicates they have been deleted
    from a series of tied notes.
    """
    pt_note = event[7]
    if pt_note.tie_prev is not None or pt_note.tie_next is None:
        return

    # gather tied notes into group
    group = [event]
    while pt_note.tie_next is not None:
        pt_note = pt_note.tie_next
        # find the note in events
        ev = pt_note_to_note[pt_note][0]
        group.append(ev)

    for i, ev in enumerate(group[:-1]):  # check all but last event
        # does ev end near a measure boundary? If so assume it's a tie across
        # the bar:
        end = ev[1] + ev[2]

        # find the measure that ends after ev
        measure = find_measure_ending_after(staff, ev[1])
        assert measure is not None

        # see if the end of the note is near the end of the measure
        if rnd and abs(end - measure.offset) < 0.5 / DIV_TO_QUARTER_ROUNDING:
            # end of note rounds to the time of the end of measure
            extend = measure.offset - end  # could be >0 or <0
            ev[2] = measure.offset - ev[1]
            # group[i + 1] exists because we're iterating over group[:-1]
            group[i + 1][1] = measure.offset
            # if we extend ev==group[i], we need to shorten group[i+1]
            group[i + 1][2] -= extend
            # now if group[i+1] duration rounds to zero, we eliminate it
            if group[i + 1][2] < 0.5 / DIV_TO_QUARTER_ROUNDING:
                if group[i + 1][7].tie_next is not None:
                    warnings.warn(
                        "Unexpected very short note event in tied group "
                        + str(group[i + 1])
                    )
                group[i + 1][2] = 0  # indicate that note is removed
                break  # (maybe redundant, we should be done with iteration)


def staff_for_note(part: Part, event: list) -> Staff:
    """Find the staff corresponding to the Partitura staff number.
    part - the Part containing all staffs/staves.
    event - a tuple extracted from Partitura structure (see "Data formats..."
            below).
    Returns
    -------
      Staff - a Staff object from the Part that contains the event.
    """
    if event[3] is None:
        return part.content[0]  # type: ignore  (part has staff)
    else:
        return part.content[event[3] - 1]  # find the staff


def process_signatures(
    measure: Measure, staff_num: int, signatures: list[list]
) -> None:
    """
    If one or more signatures belong in measure, create them. This is
    called here because sometimes signatures appear before the Partitura
    measure, so we have to wait for the measure to be created before
    putting signature in the Score.

    Also, this functions sorts events into conventional order: clef < key_sig.

    The intent is to pass the list of signatures to every measure of every
    staff. For efficiency, the signatures are in order and as we process each
    measure, we remove any signature that we use or do not want. Since
    signatures is modified, a copy is made for each staff so that when we
    go to a new staff, we start with the full original list.

    Parameters
    ----------
    measure: Measure
        where to add the signature
    staff_num: int
        what staff does measure belong to?
    signatures: list
        list of tuples, currently either ("key_sig", onset, fifths) or
        ("clef", onset, staff_num, clef). "clef"s are included for all
        staffs, so this function skips

    """
    while len(signatures) > 0:
        sig = signatures[0]
        if sig[0] == "clef" and sig[2] != staff_num:
            del signatures[0]  # skip clefs for other staves
            continue
        if (
            len(signatures) > 1
            and signatures[1][0] == "clef"
            and signatures[1][2] != staff_num
        ):
            del signatures[1]  # skip clefs for other staves even when
            # there is a key signature at the front so that we can swap
            # clef and key signature if needed below
        if sig[1] >= measure.onset:
            # "cheap and dirty" sort since there are only 2 categories:
            if (
                len(signatures) > 1
                and isclose(sig[1], signatures[1][1], abs_tol=0.001)
                and sig[0] == "key_sig"
                and signatures[1][0] == "clef"
                and signatures[1][2] == staff_num
            ):
                signatures[0] = signatures[1]  # swap 0 and 1
                signatures[1] = sig
                sig = signatures[0]
            if sig[0] == "key_sig":
                KeySignature(measure, sig[1], sig[2])
            elif sig[0] == "clef" and sig[2] == staff_num:
                Clef(measure, sig[1], sig[3])
            else:
                assert False, f"Internal error, unexpected sig {sig}"
            del signatures[0]
        else:
            return  # need to wait for measure to be created


def partitura_convert_part(
    ppart: ptScore.Part, score: Score, rnd: bool = True
) -> Part:
    """Convert a Partitura part to an AMADS Part and add it to the Score.
    ppart - the Partitura part
    score - the AMADS Score to which the Part will be added
    rnd - if True, does some select rounding for symbolic scores.
          if False (default), no rounding is done (used for MIDI import)
    Returns
    -------
      Part - the newly created AMADS Part
    """
    # these are globals so we don't have to pass to every
    # helper function that needs to do lookups:
    global measure_map, pt_note_to_note
    # note ppart.quarter_map(x) maps divs to quarters
    part: Part = Part(parent=score, instrument=ppart.part_name)
    durs = ppart.quarter_durations()
    staff_numbers = set()
    # data is stored in ppart in a different order than we want, so
    # we first extract it into various lists, each of which will be
    # accessed in order. (This also means only one iteration of ppart
    # because iter_all() is currently extremely slow, so we only want
    # to do it once.) We traverse measures and signatures for each
    # staff in a subsequent pass.
    measures = []  # list of (measure number, start time, end time) tuples
    signatures = []  # list of ("key_sig", onset, fifths) and
    # ("clef", onset, staff_num, clef) info
    notes = []  # list of ("note", ...), ("rest", ...) or ("tempo", ...)
    # information
    measure_map = []
    pt_note_to_note = {}

    # pass 1: count staves and collect measure, signature, notes lists
    tied_count = 0  # debug to count notes in part
    for item in ppart.iter_all():
        if isinstance(item, ptScore.Note) or isinstance(item, ptScore.Rest):
            staff_numbers.add(item.staff)

        onset = div_to_quarter(durs, item.start.t)  # type: ignore
        if isinstance(item, ptScore.Measure):
            # convert divs duration to quarters
            duration = div_to_quarter(
                durs, item.end.t, rnd=rnd  # type: ignore
            ) - div_to_quarter(
                durs, item.start.t, rnd=rnd  # type: ignore
            )  # type: ignore
            if duration > 0:  # all staves have the same
                # measure count and timing, so we only build the map for
                # staff 0; do not append zero-length measures that arise
                # from rounding errors in Partitura:
                #
                # When a measure onset will land on or exceed a 10-beat
                # boundary, add a map entry. Use while in case measures are
                # longer than 10 beats, which means we'll have multiple entries
                # denoting to the same measure.
                #
                # we want staff.content[measure_map[int(t/10)]].onset <= t,
                # i.e. measure_map[0].onset == 0, measure_map[1].onset <= 10,
                # measure_map[2].onset <= 20, etc.
                offset = onset + duration
                while offset >= len(measure_map) * 10:
                    measure_map.append(len(measures))
                measures.append((onset, duration))
        elif isinstance(item, ptScore.TimeSignature):
            upper = item.beats
            lower = item.beat_type
            # find the time signature in effect at onset, add small offset
            # to avoid floating point rounding errors:
            ts = score._find_time_signature(onset + 1e-6)
            if ts.upper != upper or ts.lower != lower:
                last_ts = score.time_signatures[-1]
                if last_ts.time > onset:
                    warnings.warn(
                        "Encountered a new Partitura time signature"
                        " placed BEFORE an earlier time signature:"
                        " {element}. Something is probably wrong"
                        " with this score. Ignoring the time"
                        " signature in conversion to AMADS."
                    )
                else:
                    ts = TimeSignature(onset, upper, lower)
                    score.append_time_signature(ts)
        elif isinstance(item, ptScore.KeySignature):
            signatures.append(("key_sig", onset, item.fifths))
        elif isinstance(item, ptScore.Clef):
            clef = None
            if not item.octave_change or item.octave_change == 0:
                if item.sign == "G":
                    if item.line == 2:
                        clef = "treble"
                elif item.sign == "F":
                    if item.line == 4:
                        clef = "bass"
                elif item.sign == "C":
                    if item.line == 3:
                        clef = "alto"
                    elif item.line == 4:
                        clef = "tenor"
            elif (
                item.octave_change == -1 and item.sign == "G" and item.line == 2
            ):
                clef = "treble8vb"
            elif item.sign == "percussion":
                clef = "percussion"
            if clef is None:
                warnings.warn(
                    f'Unrecognized Partitura clef "{item}"'
                    f" octave_change {item.octave_change} ignored."
                )
            else:
                signatures.append(("clef", onset, item.staff, clef))
        elif isinstance(item, ptScore.Note):
            qtr = item.start.quarter  # type: ignore
            duration = (item.end.t - item.start.t) / qtr  # type: ignore
            is_tied = if_tied(item)
            notes.append(
                [
                    "note",
                    onset,
                    duration,
                    item.staff,
                    item.midi_pitch,
                    item.id,
                    is_tied,  # event[6]
                    item,
                ]
            )  # event[7]
            if is_tied:
                pt_note_to_note[item] = [notes[-1]]
                tied_count += 1  # debug
        elif isinstance(item, ptScore.Rest):
            qtr = item.start.quarter  # type: ignore
            duration = (item.end.t - item.start.t) / qtr  # type: ignore
            notes.append(["rest", onset, duration, item.staff])
        elif isinstance(item, ptScore.Tempo):
            # Note: partitura "bpm" is really beats per second!
            factor = 1.0  # conversion factor from partitura bpm to AMADS qps
            if item.unit is not None:  # unit string provided
                if item.unit == "h":
                    factor = 2.0  # half notes per second
                elif item.unit == "q":
                    factor = 1.0  # quarter notes per second
                elif item.unit == "q.":
                    factor = 1.5  # dotted quarter notes per second
                elif item.unit == "e":
                    factor = 0.5  # eighth notes per second
                elif item.unit == "e.":
                    factor = 0.75  # dotted eighth notes per second
                elif item.unit == "s":
                    factor = 4.0  # sixteenth notes per second
                elif item.unit == "s.":
                    factor = 0.375  # dotted sixteenth notes per second
                else:
                    ValueError(f"Unknown tempo unit in partitura: {item.unit}")
            score.time_map.append_change(onset, item.bpm * factor)

    # for each staff, create measures
    for staff_num in staff_numbers:
        # not sure what staff_num can be, so trying to be robust here:
        if staff_num is not None and not isinstance(staff_num, int):
            staff_num = str(staff_num)
            assert str(staff_num).isdigit(), (
                "Unexpected staff value" " from Partitura note"
            )
            staff_num = int(staff_num)
        staff = Staff(parent=part, number=staff_num)
        # staff_signatures will be "consumed" by new measures, so make a copy:
        staff_signatures = signatures.copy()
        for m_info in measures:
            m = Measure(parent=staff, onset=m_info[0], duration=m_info[1])
            process_signatures(m, staff_num, staff_signatures)
        staff.inherit_duration()

    # Data formats (note that staff number is always event[3])
    #    (Note, onset, duration, staff, midi_pitch, id, tied, ptnote)
    #    (Rest, onset, duration, staff)
    # id_to_event = {}

    # pass 3: re-tie notes that cross measures in case measure times
    #         have changed due to rounding.
    if rnd:
        for i, event in enumerate(notes):
            staff = staff_for_note(part, event)
            if event[0] == "note" and event[6]:  # tied
                retie_notes(event, staff, rnd)

    # pass 4: insert notes and rests into score
    mindex = 0
    for i, event in enumerate(notes):
        staff = staff_for_note(part, event)
        measure: Measure = staff.content[mindex]  # type: ignore
        # find the measure containing event[1] (onset)
        while event[1] >= measure.offset:
            mindex += 1
            if mindex == len(staff.content):
                warnings.warn(
                    f"Something is wrong; could not find measure"
                    f" for {event}"
                )
                break  # use previous measure, but probably there is a bug here
            measure = staff.content[mindex]  # type: ignore
        if event[0] == "note":
            if event[2] > 0:  # zero duration means skip note
                note = Note(
                    parent=measure,
                    onset=event[1],
                    duration=event[2],
                    pitch=Pitch(event[4]),
                )
                if event[6]:  # is tied to another note
                    # Multiple cases: 1) note is tied to next note with
                    # non-zero duration, so we put the note in pt_note_to_note
                    # so it can be patched later. 2) note is tied to a previous
                    # note, so we patch the previous note.
                    pt_note = event[7]
                    # map pt_note to [event, note], so [0] gives the event,
                    # and event[2] is duration
                    if pt_note.tie_next and pt_note_to_note[pt_note][0][2] != 0:
                        # associate this new Note with the partitura note:
                        pt_note_to_note[pt_note].append(note)
                    if pt_note.tie_prev:
                        # patch the previous note
                        pt_note = pt_note.tie_prev
                        pt_note_to_note[pt_note][1].tie = note
        elif event[0] == "rest":
            Rest(parent=measure, onset=event[1], duration=event[2])
        else:
            assert False, f"Unknown event type {event[0]}"

    # expand first measures to a full measure if necessary
    # what is the maximum offset of the first measure?
    for staff in part.content:
        if len(staff.content) > 0:  # type: ignore
            m1 = staff.content[0]  # type: ignore
            max_offset = 0
            for elem in m1.content:
                max_offset = max(max_offset, elem.offset)
            m1_ts_dur = m1.time_signature().quarters
            if max_offset < m1_ts_dur - 0.001:  # need to insert rest
                gap = m1_ts_dur - max_offset
                for elem in m1.content:
                    if (
                        isinstance(elem, Note)
                        or isinstance(elem, Rest)
                        or isinstance(elem, Chord)
                    ):
                        elem.time_shift(gap)
                # insert Rest, Since m1 is first, m1.onset == 0
                _ = Rest(m1, m1.onset, duration=gap)

                # if m1 duration increases, shift all other measures
                gap = m1_ts_dur - m1.offset
                if gap > 0.001:
                    m1.duration = m1_ts_dur  # fix m1 duration
                    staff.pack()  # type: ignore

                # also need to update time map and time_signatures
                for ts in score.time_signatures[1:]:
                    ts.time += gap
                # we're adding gap beats at the initial tempo,
                # so convert that to a time shift in seconds,
                # then add (time_gap, gap) to (time, quarter) pairs
                time_gap = gap * score.time_map.get_tempo_at(0)
                for mq in score.time_map.changes[1:]:
                    mq.time += time_gap
                    mq.quarter += gap

    part.duration = part.content[0].duration  # set to equal staff duration
    return part


def partitura_xml_import(
    filename,
    flatten=False,
    collapse=False,
    show=False,
    group_by_instrument: bool = True,
) -> Score:
    """Use Partitura to import a MusicXML file.

    Parameters
    ----------
    filename : str
        The path (relative or absolute) to the music file.
    flatten : bool = False
        Returns a flat score (see `amads.core.basics.Part.flatten`)
    collapse : bool = False
        If `flatten` is True, all Notes are merged (collapsed) into
        a single Part in the resulting Score.
    show : bool = False
        Print a text representation of the data.
    group_by_instrument : bool = True
        This parameter is ignored by Partitura, which automatically
        produces parts with multiple staffs. The Partitura grouping
        is respected, and `group_by_instrument` is ignored.

    Returns
    -------
    Score
        The imported Score

    <small>**Author**: Roger B. Dannenberg</small>
    """
    if filename is None:
        filename = pt.EXAMPLE_MUSICXML

    # Partitura.load_score claims to accept a file-like object, but
    # it has been problematic for us in the past, so we use a string filename.
    filename = str(filename)

    ptscore = pt.load_score(filename)
    if show:
        print(f"Partitura score structure from {filename}:")
        for ptpart in ptscore:
            print(ptpart.pretty())
    score = Score()
    for ptpart in ptscore.parts:
        partitura_convert_part(ptpart, score)
    score.inherit_duration()
    if flatten or collapse:
        score = score.flatten(collapse=collapse)
    return score
