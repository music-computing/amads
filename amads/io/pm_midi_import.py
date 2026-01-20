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
from amads.core.basics import (
    KeySignature,
    Measure,
    Note,
    Part,
    Score,
    Staff,
    TimeSignature,
)
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
    pmscore: PrettyMIDI,
) -> None:
    """Create measures in Staff according to pmscore time_signature_changes

    At each iteration, insert measures up to the signature time, and
    on the last iteration, insert measures up to the end of the score

    To deal with float approximation, we round beat times to 1/32 since
    time signatures are always n/(2^d), e.g. 4/4, 3/16, ....
    """
    # insert measures according to time_signature_changes:
    # also add key signatures to measures
    cur_upper = 4
    cur_lower = 4
    cur_duration = 4  # default is 4/4 starting at beat 0
    cur_beat = 0  # we have created measures up to this time

    ksigs = pmscore.key_signature_changes
    k = 0  # index to key signatures in ksigs
    if k < len(ksigs):
        ksig = ksigs[k]
        kbeat = time_map.time_to_quarter(ksig.time)
    else:
        kbeat = staff.duration + 999  # no key signatures

    tsigs = pmscore.time_signature_changes
    i = 0
    score = cast(Score, staff.score)
    while i <= len(tsigs):
        if i < len(tsigs):
            tsig = tsigs[i]
            tbeat = time_map.time_to_quarter(tsig.time)
        else:  # trick to fill measures to the end of score
            tsig = None
            tbeat = score.duration  # should we add 1e-6 here?
        need_time_signature = True
        while cur_beat < tbeat - 1e-6:  # avoid rounding
            measure = Measure(onset=cur_beat, duration=cur_duration)
            if need_time_signature:  # first measure after time signature change
                ts = TimeSignature(cur_beat, cur_upper, cur_lower)
                score.append_time_signature(ts)
                need_time_signature = False
            staff.insert(measure)
            # if needed now, insert key signature into measure
            if cur_beat > kbeat - 1e-6:  # avoid rounding error
                _ = KeySignature(
                    measure, cur_beat, ksig.key_number
                )  # type: ignore
                # get next key signature
                k += 1
                if k < len(ksigs):
                    ksig = ksigs[k]
                    kbeat = time_map.time_to_quarter(ksig.time)
                else:
                    kbeat = score.duration + 999  # no more key signatures
            cur_beat += cur_duration

        # now set up for next iteration
        if tsig is not None:
            tsig_str = str(tsig.numerator) + "/" + str(tsig.denominator)
            if not isclose(cur_beat, tbeat, abs_tol=1e-6):
                warnings.warn(
                    f"MIDI file time signature change at beat {tbeat}"
                    " is not on the expected measure boundary at"
                    f" {cur_beat}. The time signature {tsig_str}"
                    f" will be applied at {cur_beat}."
                )
            cur_upper = tsig.numerator
            cur_lower = tsig.denominator
            cur_duration = cur_upper * 4 / cur_lower
        # else tsig is None means we've reached the end of the score
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


# debug
def has_staff(part):
    for item in part.content:
        if isinstance(item, Staff):
            return True
    return False


def pretty_midi_midi_import(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
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
    group_by_instrument : bool, optional
        If True, group parts by instrument name into staffs. Defaults to True.
        See read_midi() for more details.

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

    # This helps orgainize parts by instrument name. Parts with the same
    # instrument name are grouped together as staffs in a single Part.
    instrument_groups: dict[str, list[Part]] = {}

    # Iterate over instruments of the PrettyMIDI score and build parts and notes
    duration = 0
    no_name_id = 1
    for ins in pmscore.instruments:
        name = ins.name
        if not ins.name:
            name = program_to_instrument_name(ins.program)
        if name == "Unknown":  # AMADS uses "Unknown" to represent None.
            # Of course, if a user really names an instrument "Unknown",
            # that particular name will not be stored in the Part.
            name = None

        part = Part(parent=score, onset=0.0, instrument=name)

        # now that we've put the name in the Part, change None to a unique name
        # so that we can make the part a named instrument group. If we are not
        # grouping by instrument, we want each part in its own group, so we
        # give each part a unique name in that case too.
        if name is None or not group_by_instrument:
            name = f"_None~@_{no_name_id}"  # something unlikely to be a name
            no_name_id += 1
        group = instrument_groups.get(name, [])
        group.append(part)
        instrument_groups[name] = group

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
        assert not has_staff(
            part
        ), "Part should not have Staffs before flattening"

    score.duration = duration
    for part in score.content:
        part.duration = duration  # all parts get same max duration
        assert not has_staff(part), "Part should not have Staffs"

    # Then if collapse, merge and sort the notes
    if collapse:
        score = score.flatten(collapse=True)

    score.convert_to_quarters()  # we want to return with quarters as time unit

    # TODO: remove this block
    for groups in instrument_groups.values():
        for part in groups:
            assert not has_staff(part), "Part should not have Staffs 2"

    # Then if not flatten, remove each part content, and staff and measures,
    # and move notes into measures, creating ties where they cross. This maybe
    # does some extra work if not grouping by instrument, because we already
    # have the right set of parts, but the real work here is creating the staffs
    # and measures, and moving notes into measures with ties, so we have
    # eliminated the small extra work of copying parts when not grouping.
    if not flatten:
        score.content.clear()  # remove parts from score
        for group in instrument_groups.values():
            new_part = group[0].insert_emptycopy_into(score)
            new_part = cast(Part, new_part)
            new_part.duration = score.duration
            for old_part in group:
                assert not has_staff(
                    old_part
                ), "Part should not have Staffs before creating staffs"
                old_part = cast(Part, old_part)
                notes = old_part.content
                # now notes have part as parent, but parent does not have notes
                staff = Staff(
                    parent=new_part, onset=0.0, duration=new_part.duration
                )
                # in principle we could do this once for the first staff and
                # then copy the created staff with measures for any other
                # staff, but then we would have to save off the notes and
                # write another loop to insert each note list to a corresponding
                # staff. Besides, _create_measures might even be faster than
                # calling deepcopy on a Staff to copy the measures.
                _create_measures(staff, score.time_map, pmscore)
                notes = cast(
                    list[Note], notes
                )  # tell type checker notes is list of Note
                _add_notes_to_measures(
                    notes,
                    cast(list[Measure], staff.content),
                    pmscore.resolution,
                )
                old_part.content.clear()  # clean up

    return score
