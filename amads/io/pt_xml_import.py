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

# plan: multiple passes over iter_all()
# for each part: add the part to a Concurrence
#      1st pass: get staff numbers from notes, extract measures, get div/qtr
#           create a Concurrence of staves if more than one,
#           create measures in each staff
#      2nd pass: get notes, rests, insert parameters into lists
#      3rd pass: re-tie notes that cross measures in case the measure boundary
#           has moved due to rounding
#      4th pass: build Note and Rest objects, insert into Measures


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
    print("div_to_quarter: div", div, "qtrs", qtrs)
    return qtrs


def tie_status(note):
    """Given a partitura note, compute the ties status as one of: None,
    'start', 'continue', or 'stop'
    """
    if note.tie_prev and note.tie_next:
        return "continue"
    elif note.tie_prev:
        return "stop"
    elif note.tie_next:
        return "start"
    else:
        return None


def retie_notes(event, events, i, measure, staff, mindex, part):
    """Adjust tied notes that cross barlines to account for rounded
    measure timing.
        event - the start of the tied note group
        events - the list of all events
        i - the index of event in events
        measure - the measure of the event
        staff - the staff containing the rest of the measures
        mindex - the index of measure in staff.content
        part - contains the staff

    Algorithm:
    When you find a note where tie='start', find all tied notes.
    Then for each note in order, if tied to the next note and the
    end time rounds to a bar time, then replace the end time with
    the bar time and replace the next not start and duration to
    move the start time to the bar time (delta=0). If the resulting
    duration is < 0.001, assume it was created through rounding error
    and set it to zero, set the current note from tie='continue' to
    tie='stop' or tie='start' to tie=None, and set the tied-to note
    tie='None'. (This could slightly truncate performance notes, but
    imperceptibly.) In the next pass, ignore notes with duration of 0,
    which now indicates they have been deleted from a series of tied
    notes.
    """
    print("BEGIN retie_note", event)
    group = [event]
    pitch = event[4]
    i += 1
    while i < len(events):  # look for notes tied to this one
        ev = events[i]
        print("search for group", ev[0], ev[4], pitch, staff_for_note(part, ev))
        if ev[0] == "Note" and ev[4] == pitch and staff_for_note(part, ev) == staff:
            print("**** found one ****", ev)
            # ev is the next note in events with the same pitch and staff
            group.append(ev)
            if ev[6] == "stop":
                break  # we found the last tied note
        i += 1
    print("GROUP BEFORE: ", group)
    for i, ev in enumerate(group[:-1]):  # check all but 'stop' event
        # does ev end near a measure boundary? If so assume it's a tie across
        # the bar:
        end = ev[1] + ev[2]
        while end > (measure.delta_end + 1 / DIV_TO_QUARTER_ROUNDING) and (
            mindex < len(staff.content) - 1
        ):
            mindex += 1
            measure = staff.content[mindex]
        # now we know end > previous bar end + 1/DIV and
        #     end < this bar end + 1/DIV (unless we ran out of measures), so
        #     this bar end (measure.delta_end) is the time we are looking for
        print(
            "found bar at",
            measure.delta_end,
            "absdiff",
            abs(end - measure.delta_end),
        )
        if abs(end - measure.delta_end) < 0.5 / DIV_TO_QUARTER_ROUNDING:
            # end of note rounds to the time of the end of measure
            extend = measure.delta_end - end  # could be >0 or <0
            ev[2] = measure.delta_end - ev[1]
            group[i + 1][1] = measure.delta_end
            # if we extend ev==group[i], we need to shorten group[i+1]
            group[i + 1][2] -= extend
            # now if group[i+1] duration rounds to zero, we eliminate it
            if group[i + 1][2] < 0.5 / DIV_TO_QUARTER_ROUNDING:
                if group[i + 1][6] != "stop":
                    print(
                        "Unexpected very short note event in tied group", group[i + 1]
                    )
                group[i + 1][2] = 0  # indicate that note is removed
                ev[6] = None if ev[6] == "start" else "stop"
                break  # (maybe redundant, we should be done with iteration)
    print("GROUP AFTER: ", group)


def staff_for_note(part, event):
    """Find the staff corresponding to the Partitura staff number.
    part - the Part containing all staffs/staves.
    event - a tuple extracted from Partitura structure (see "Data formats..."
            below).
    returns a Staff object
    """
    if event[3] is None:
        return part.content[0]
    else:
        return part.content[event[3] - 1]  # find the staff


def partitura_convert_part(ppart, score):
    # note ppart.quarter_map(x) maps divs to quarters
    part = Part(instrument=ppart.part_name)
    durs = ppart.quarter_durations()
    staff_numbers = set()
    measures = []
    # pass 1: staves and measures
    for item in ppart.iter_all():
        if isinstance(item, pt.score.Note) or isinstance(item, pt.score.Rest):
            staff_numbers.add(item.staff)
        elif isinstance(item, pt.score.Measure):
            measures.append((item.number, item.start.t, item.end.t))
        elif isinstance(item, pt.score.TimeSignature):
            measures.append(("timesig", item.beats, item.beat_type))
        elif isinstance(item, pt.score.KeySignature):
            measures.append(("keysig", item.fifths))
    print("staff_numbers", staff_numbers)
    print("measures", measures)
    for _ in range(0, len(staff_numbers)):
        staff = Staff()
        for m in measures:
            if m[0] == "timesig":
                # assume timesig is inside a measure, which would be the last
                # measure (so far) in this staff, and assume we are at the
                # beginning of the measure; delta=0 overrides putting this
                # at the end of the measure which already has a duration
                staff.last.append(TimeSignature(m[1], m[2]), delta=0)
            elif m[0] == "keysig":
                staff.last.append(KeySignature(m[1], delta=0))
            else:
                # convert divs duration to quarters
                duration = div_to_quarter(durs, m[2], rnd=True) - div_to_quarter(
                    durs, m[1], rnd=True
                )
                if duration > 0:  # do not append zero-length measures that arise
                    # from rounding errors in Partitura:
                    staff.append(Measure(duration=duration))
        print("added measures to staff:")
        staff.show()
        part.append(staff)

    # pass 2: gather notes and rests
    events = []
    print("div=0 -> qtr", ppart.quarter_map(0))
    print("measure_map(0)", ppart.measure_map(0))
    print("measure_number_map(0)", ppart.measure_number_map(0))
    for item in ppart.iter_all():
        if isinstance(item, pt.score.Note) or isinstance(item, pt.score.Rest):
            start = div_to_quarter(durs, item.start.t)
            print("Note or Rest start", start, "item.start.t", item.start.t)
            duration = (item.end.t - item.start.t) / item.start.quarter
            if isinstance(item, pt.score.Note):
                events.append(
                    [
                        "Note",
                        start,
                        duration,
                        item.staff,
                        item.midi_pitch,
                        item.id,
                        tie_status(item),
                    ]
                )
            elif isinstance(item, Rest):
                events.append(["Rest", start, duration, item.staff])
        elif isinstance(item, pt.score.Tempo):
            start = div_to_quarter(durs, item.start.t)
            print("Tempo start", start, "tempo", item.bpm / 60.0)
            score.time_map.append_beat_tempo(start, item.bpm / 60.0)
        else:
            print("ignoring", item)
    print("events", events)

    # Data formats (note that staff number is always event[3])
    #    (Note, start, duration, staff, midi_pitch, id, tie) -- on events list
    #    (Rest, start, duration, staff) -- on events list
    # id_to_event = {}

    # pass 3: re-tie notes that cross measures in case measure times
    #         have changed due to rounding.
    mindex = 0
    for i, event in enumerate(events):
        staff = staff_for_note(part, event)
        measure = staff.content[mindex]
        while event[1] >= measure.delta_end and mindex < len(staff.content) - 1:
            mindex += 1
            measure = staff.content[mindex]
        if event[6] == "start":
            retie_notes(event, events, i, measure, staff, mindex, part)
    print("after re-tie notes, events:")
    print(events)

    # pass 4: insert notes and rests into score
    mindex = 0
    for event in events:
        staff = staff_for_note(part, event)
        measure = staff.content[mindex]
        while event[1] >= measure.delta_end:
            mindex += 1
            if mindex == len(staff.content):
                print("Something is wrong; could not find measure for", event)
                break  # use previous measure, but probably there is a bug here
            measure = staff.content[mindex]
        delta = event[1] - measure.onset
        if event[0] == "Note":
            if event[2] > 0:  # zero duration means skip note
                note = Note(duration=event[2], pitch=event[4], delta=delta)
                note.tie = event[6]
                print("Before inserting note:")
                note.show()
                # id_to_event[event[5]] = note  # build temporary map in dictionary
                measure.insert(note)
        elif event[0] == "Rest":
            measure.insert(Rest(event[2]), delta=measure.delta)
        else:
            assert False
    return part


def partitura_xml_import(filename, ptprint=False):
    """Use Partitura to import a MusicXML file."""
    if filename is None:
        filename = pt.EXAMPLE_MUSICXML
    ptscore = pt.load_score(filename)
    if ptprint:
        for ptpart in ptscore:
            print(ptpart.pretty())
    score = Score()
    for ptpart in ptscore.parts:
        score.append(partitura_convert_part(ptpart, score))
    return score
