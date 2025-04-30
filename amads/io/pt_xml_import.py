"""pt_xml_import.py - Partitura XML import and conversion to AMADS"""

__author__ = "Roger B. Dannenberg"

import partitura as pt

from ..core.basics import (
    KeySignature,
    Measure,
    Note,
    Part,
    Rest,
    Score,
    Staff,
    TimeSignature,
)

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


def find_measure_ending_after(staff: Staff, time: float) -> Measure:
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


def if_tied(note: pt.score.Note) -> bool:
    """Given a partitura note, return the note itself if it is
    either tied-to or tied-from. Otherwise, return None.
    """
    return (note.tie_prev or note.tie_next) is not None


def retie_notes(event, staff):
    """Adjust tied notes that cross barlines to account for rounded

    measure timing.
    event - the start of the tied note group
    events - the list of all events
    i - the index of event in events
    staff - the staff containing the rest of the measures
    part - contains the staff

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
    print("BEGIN retie_note", event)
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

    print("GROUP BEFORE: ", group)
    for i, ev in enumerate(group[:-1]):  # check all but last event
        # does ev end near a measure boundary? If so assume it's a tie across
        # the bar:
        end = ev[1] + ev[2]

        # find the measure that ends after ev
        measure = find_measure_ending_after(staff, ev[1])
        assert measure is not None

        # see if the end of the note is near the end of the measure
        if abs(end - measure.offset) < 0.5 / DIV_TO_QUARTER_ROUNDING:
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
                    print(
                        "Unexpected very short note event in tied group", group[i + 1]
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
        return part.content[0]
    else:
        return part.content[event[3] - 1]  # find the staff


def process_signatures(measure: Measure, signatures: list[list]):
    """
    If one or more signatures belong in measure, create them. This is
    called here because sometimes signatures appear before the Partitura
    measure, so we have to wait for the measure to be created before
    putting signature in the Score.
    """
    while len(signatures) > 0:
        sig = signatures[0]
        if sig[1] >= measure.onset:
            if sig[0] == "key_sig":
                KeySignature(measure, sig[1], sig[2])
                del signatures[0]
            if sig[0] == "time_sig":
                TimeSignature(measure, sig[1], sig[2], sig[3])
                del signatures[0]
        else:
            return  # need to wait for measure to be created


def partitura_convert_part(ppart, score):
    # these are globals so we don't have to pass to every
    # helper function that needs to do lookups:
    global measure_map, pt_note_to_note
    # note ppart.quarter_map(x) maps divs to quarters
    part = Part(parent=score, instrument=ppart.part_name)
    durs = ppart.quarter_durations()
    staff_numbers = set()
    # data is stored in ppart in a different order than we want, so
    # we first extract it into various lists, each of which will be
    # accessed in order. (This also means only one iteration of ppart
    # because iter_all() is currently extremely slow, so we only want
    # to do it once.) We traverse measures and signatures for each
    # staff in a subsequent pass.
    measures = []  # list of (measure number, start time, end time) tuples
    signatures = []  # list of ("time_sig", beats, beat_type) or
    # ("key_sig", fifths) information
    notes = []  # list of ("note", ...), ("rest", ...) or ("tempo", ...)
    # information
    measure_map = []
    pt_note_to_note = {}

    # T print("Starting iter_all")
    # T for item in ppart.iter_all():
    # T     pass
    # T print("Done iter_all")

    # T print("In partitura_convert_part")
    # T timer = Timer("convert_part pass 1-begin")
    # T timer2 = Timer("convert_part pass 1-next")
    # T timer.start()
    # T first_time = True
    # pass 1: count staves and collect measure, signature, notes lists
    for item in ppart.iter_all():
        # T if first_time:
        # T     timer.stop(report=True) # DEBUG
        # T     first_time = False
        # T else:
        # T     timer2.stop() # DEBUG

        if isinstance(item, pt.score.Note) or isinstance(item, pt.score.Rest):
            staff_numbers.add(item.staff)

        onset = div_to_quarter(durs, item.start.t)
        if isinstance(item, pt.score.Measure):
            # convert divs duration to quarters
            duration = div_to_quarter(durs, item.end.t, rnd=True) - div_to_quarter(
                durs, item.start.t, rnd=True
            )
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
        elif isinstance(item, pt.score.TimeSignature):
            signatures.append(("time_sig", onset, item.beats, item.beat_type))
        elif isinstance(item, pt.score.KeySignature):
            signatures.append(("key_sig", onset, item.fifths))
        elif isinstance(item, pt.score.Note):
            duration = (item.end.t - item.start.t) / item.start.quarter
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
        elif isinstance(item, pt.score.Rest):
            duration = (item.end.t - item.start.t) / item.start.quarter
            notes.append(["rest", onset, duration, item.staff])
        elif isinstance(item, pt.score.Tempo):
            # print("Tempo start", start, "tempo", item.bpm / 60.0)
            score.time_map.append_beat_tempo(onset, item.bpm / 60.0)
        # T timer2.start()
    # T timer2.report() # DEBUG
    # print("partitura_convert_part: after pass 1, measures are")
    # print(measures)

    # T timer.init("convert_part pass 2")
    # T timer.start()

    # for each staff, create measures
    for staff_num in range(0, len(staff_numbers)):
        staff = Staff(parent=part, number=staff_num + 1)
        # staff_signatures will be "consumed" by new measures, so make a copy:
        staff_signatures = signatures.copy()
        for m_info in measures:
            m = Measure(parent=staff, onset=m_info[0], duration=m_info[1])
            process_signatures(m, staff_signatures)
        staff.inherit_duration()
    # T timer.stop(report=True) # DEBUG

    # T timer.init("convert_part pass 3")
    # T timer.start()

    # Data formats (note that staff number is always event[3])
    #    (Note, onset, duration, staff, midi_pitch, id, tied, ptnote)
    #    (Rest, onset, duration, staff)
    # id_to_event = {}

    # pass 3: re-tie notes that cross measures in case measure times
    #         have changed due to rounding.
    for i, event in enumerate(notes):
        staff = staff_for_note(part, event)
        if event[6]:  # tied
            retie_notes(event, staff)
    # T timer.stop(report=True) # DEBUG

    # T timer.init("convert_part pass 4")
    # T timer.start()

    # pass 4: insert notes and rests into score
    mindex = 0
    for event in notes:
        staff = staff_for_note(part, event)
        measure = staff.content[mindex]
        while event[1] >= measure.offset:
            mindex += 1
            if mindex == len(staff.content):
                print("Something is wrong; could not find measure for", event)
                break  # use previous measure, but probably there is a bug here
            measure = staff.content[mindex]
        if event[0] == "note":
            if event[2] > 0:  # zero duration means skip note
                note = Note(
                    parent=measure, onset=event[1], duration=event[2], pitch=event[4]
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
                        # associate thie new Note with the partitura note:
                        pt_note_to_note[pt_note].append(note)
                    if pt_note.tie_prev:
                        # patch the previous note
                        pt_note = pt_note.tie_prev
                        pt_note_to_note[pt_note][1].tie = note
        elif event[0] == "rest":
            Rest(parent=measure, onset=measure.onset, duration=event[2])
        else:
            assert False
    # T timer.stop(report=True) # DEBUG
    return part


def partitura_xml_import(filename, show=False):
    """Use Partitura to import a MusicXML file."""
    if filename is None:
        filename = pt.EXAMPLE_MUSICXML

    # Partitura.load_score claims to accept a file-like object, but
    # it has been problematic for us in the past, so we use a string filename.
    filename = str(filename)

    ptscore = pt.load_score(filename)
    if show:
        for ptpart in ptscore:
            print(ptpart.pretty())
    score = Score()
    for ptpart in ptscore.parts:
        partitura_convert_part(ptpart, score)
    score.inherit_duration()
    return score
