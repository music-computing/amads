"""
pm_midi_import.py

Import MIDI files into AMADS Score structure using the PrettyMIDI library.

Functions
---------
- pretty_midi_midi_import(filename: str, flatten: bool = False,
                          collapse: bool = False, show: bool = False) -> Score:
    Imports a MIDI file using PrettyMIDI and converts it into a `Score` object.

Usage
-----
Do not use this module directly; see readscore.py.

Notes
-----
PrettyMIDI has a "hidden" representation of the MIDI tempo track in
`_tick_scales`, which has the form [(tick, tick_duration), ...]. We
need to convert this to a TimeMap.
"""

__author__ = "Roger B. Dannenberg"

import warnings
from math import isclose
from typing import cast

from pretty_midi import PrettyMIDI, program_to_instrument_name

# this should not be necessary, but Python confuses AMADS with
#     pretty_midi's TimeSignature class:
from amads.core.basics import Measure, Note, Part, Score, Staff, TimeSignature
from amads.core.pitch import Pitch
from amads.core.timemap import TimeMap


def _time_map_from_tick_scales(tick_scales, resolution: int) -> TimeMap:
    """Convert "hidden" _tick_scales list to AMADS TimeMap, representing the
    midi file tempo map
    """
    ticks_per_second = 1.0 / tick_scales[0][1]
    time_map = TimeMap(qpm=ticks_per_second * 60 / resolution)
    for change in tick_scales[1:]:
        # tick_scales is not documented, but since this works, we
        # can say that tick_scales is a list of breakpoints where
        # tempo changes. time (sec) = change[0] / resolution, and
        # beat (quarters) = 60 / (change[1] * resolution), so
        # each tuple is (score time in units of ticks, seconds/tick)
        time_map.append_change(
            change[0] / resolution, 60.0 / (change[1] * resolution)
        )
    return time_map


def _create_measures(
    staff: Staff,
    time_map: TimeMap,
    notes: list,
    pmscore: PrettyMIDI,
) -> None:
    """Create measures in Staff according to pmscore time_signature_changes

    At each iteration, insert measures up to the signature time, and
    on the last iteration, insert measures up to the end of the score

    To deal with float approximation, we round beat times to 1/32 since
    time signatures are always n/(2^d), e.g. 4/4, 3/16, ....
    """
    # insert measures according to time_signature_changes:
    cur_upper = 4
    cur_lower = 4
    cur_duration = 4  # default is 4/4 starting at beat 0
    cur_beat = 0  # we have created measures up to this time
    # print(pmscore.key_signature_changes)
    sigs = pmscore.time_signature_changes
    i = 0
    score = cast(Score, staff.score)
    while i <= len(sigs):
        if i < len(sigs):
            sig = sigs[i]
            beat = time_map.time_to_quarter(sig.time)
        else:
            sig = None
            beat = score.duration  # should we add 1e-6 here?
        need_time_signature = True
        while cur_beat < beat - 1e-6:  # avoid rounding
            measure = Measure(onset=cur_beat, duration=cur_duration)
            if need_time_signature:  # first measure after time signature change
                ts = TimeSignature(cur_beat, cur_upper, cur_lower)
                score.append_time_signature(ts)
                need_time_signature = False
            staff.insert(measure)
            cur_beat += cur_duration

        # now set up for next iteration
        if sig is not None:
            sig_str = str(sig.numerator) + "/" + str(sig.denominator)
            if not isclose(cur_beat, beat, abs_tol=1e-6):
                warnings.warn(
                    f"MIDI file time signature change at beat {beat}"
                    " is not on the expected measure boundary at"
                    f" {cur_beat}. The time signature {sig_str}"
                    f" will be applied at {cur_beat}."
                )
            cur_upper = sig.numerator
            cur_lower = sig.denominator
            cur_duration = cur_upper * 4 / cur_lower
        # else sig is None means we've reached the end of the score
        i += 1


def _add_notes_to_measures(
    notes: list[Note], measures: list[Measure], div: int
) -> None:
    """Add notes to measures and tie notes across measure boundaries.

    Parameters
    ----------
    notes : list[Note]
        The notes to insert. Parent is set in these notes, but the
        notes are not in the parent's content. Parent will be reset
        to the measure when the note is inserted.
    measures: list[Measures]
        The measures were the notes go.
    div: int
        The original number of divisions per quarter, used to perform
        rounding.
    """
    EPS = 0.5 / div  # time resolution ("epsilon")
    i = 0  # notes index
    for mi, m in enumerate(measures):
        m_insert = m  # where to insert note
        m_insert_i = mi  # index of measure to insert into
        while i < len(notes) and notes[i].onset < m.offset:
            note = notes[i]
            note.parent = None  # fix incorrect parent attribute
            # break note if it spans a measure boundary
            if note.onset > m.offset - EPS:
                # note is at the very end of the measure; just round up
                offset = note.offset
                m_insert_i = mi + 1  # index of measure to insert into
                m_insert = measures[m_insert_i]
                note.onset = m_insert.onset
                note.duration = offset - note.onset  # don't change offset time
            remaining = 0
            if note.offset > m_insert.offset:  # split and tie note
                remaining = note.offset - m_insert.offset
                note.duration = m_insert.offset - note.onset
            m_insert.insert(note)

            next_i = m_insert_i + 1
            prev_note = note
            while remaining > EPS:
                next_measure = measures[next_i]
                duration = min(remaining, next_measure.duration)
                tied_note = Note(
                    parent=next_measure,
                    onset=next_measure.onset,
                    duration=duration,
                    pitch=Pitch(note.pitch),
                    dynamic=note.dynamic,
                )
                prev_note.tie = tied_note
                prev_note = tied_note
                next_i += 1
                remaining -= tied_note.duration
            i += 1


def pretty_midi_midi_import(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
) -> Score:
    """
    Use PrettyMIDI to import a MIDI file and convert it to a Score.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    filename : Union(str, PosixPath)
        The path to the MIDI file to import.
    flatten : bool, optional
        If True, create a flat score where notes are direct children of
        parts. Defaults to collapse, which defaults to False.
    collapse : bool, optional
        If True, merge all parts into a single part. Implies flatten=True.
        Defaults to False.
    show : bool, optional
        If True, print the PrettyMIDI score structure for debugging.
        Defaults to False.

    Returns
    -------
    Score
        The converted Score object containing the imported MIDI data.

    Examples
    --------
    >>> from amads.io.pm_midi_import import pretty_midi_midi_import
    >>> from amads.music import example
    >>> score = pretty_midi_midi_import( \
                    example.fullpath("midi/sarabande.mid"), \
                    flatten=True)  # show=True to see PrettyMIDI data
    """
    flatten = flatten or collapse  # collapse implies flatten

    # Load the MIDI file using PrettyMidi
    filename = str(filename)
    pmscore = PrettyMIDI(filename)
    if show:
        from amads.io.pm_show import pretty_midi_show

        pretty_midi_show(pmscore, filename)

    # Create an empty Score object
    time_map = _time_map_from_tick_scales(
        pmscore._tick_scales, pmscore.resolution
    )
    score = Score(time_map=time_map)
    score.convert_to_seconds()  # convert to seconds for PrettyMIDI

    # Iterate over instruments of the PrettyMIDI score and build parts and notes
    # Then if collapse, merge and sort the notes
    # Then if not flatten, remove each part content, and staff and measures,
    # and move notes into measures, creating ties where they cross

    # Iterate over instruments of the PrettyMIDI score and build parts and notes
    duration = 0
    for ins in pmscore.instruments:
        name = ins.name
        if not ins.name:
            # print("pretty_midi ins.program", ins.program)
            name = program_to_instrument_name(ins.program)
        if name == "Unknown":  # AMADS uses "Unknown" to represent None.
            # Of course, if a user really names an instrument "Unknown",
            # that particular name will not be stored in the Part.
            name = None
        part = Part(parent=score, onset=0.0, instrument=name)
        for note in ins.notes:
            # Create a Note object and associate it with the Part
            Note(
                parent=part,
                onset=note.start,
                duration=note.get_duration(),
                pitch=Pitch(note.pitch),
                dynamic=note.velocity,
            )
            duration = max(duration, note.end)
    # print("pretty_midi_midi_import got max duration", duration)
    score.duration = duration
    for part in score.content:
        part.duration = duration  # all parts get same max duration

    # Then if collapse, merge and sort the notes
    if collapse:
        score = score.flatten(collapse=True)

    score.convert_to_quarters()  # we want to return with quarters as time unit

    # Then if not flatten, remove each part content, and staff and measures,
    # and move notes into measures, creating ties where they cross.
    if not flatten:
        for part in score.content:
            part = cast(Part, part)  # tell type checker that part is a Part
            notes = part.content
            part.content = []  # Remove existing content
            # now notes have part as parent, but parent does not have notes
            staff = Staff(parent=part, onset=0.0, duration=part.duration)
            # in principle we could do this once for the first staff and
            # then copy the created staff with measures for any other
            # staff, but then we would have to save off the notes and
            # write another loop to insert each note list to a corresponding
            # staff. Besides, _create_measures might even be faster than
            # calling deepcopy on a Staff to copy the measures.
            print("    calling _create_measures", score.time_map)
            _create_measures(staff, score.time_map, notes, pmscore)
            notes = cast(
                list[Note], notes
            )  # tell type checker notes is list of Note
            _add_notes_to_measures(
                notes, cast(list[Measure], staff.content), pmscore.resolution
            )

    return score
