"""
Export a Score as a standard MIDI file using PrettyMIDI library.

Functions
---------
- pretty_midi_midi_export(score: Score, filename: str) -> None:
    Exports a `Score` object as a MIDI file using PrettyMIDI.

Usage
-----
Do not use this module directly; see writescore.py.

Notes
-----
See `export_midi` notes for translation-to-MIDI-file details.

"""

from math import isclose
from typing import cast

import pretty_midi as pm

from amads.core.basics import EventGroup, KeySignature, Note, Part, Score, Staff

__author__ = "Roger B. Dannenberg"


def string_to_velocity(dynamic: str) -> int:
    """Convert a dynamic string (e.g., 'p', 'mf', 'f') to a MIDI velocity value."""
    dynamic_map = {
        "pppp": 10,
        "ppp": 23,
        "pp": 36,
        "p": 49,
        "mp": 62,
        "mf": 75,
        "f": 99,
        "ff": 102,
        "fff": 114,
        "ffff": 127,
    }
    return dynamic_map.get(dynamic.lower(), 100)  # Default to 100 if unknown


tied_to_notes = None  # global to help merge tied notes


def add_note_to_instrument(note: Note, instrument: pm.Instrument) -> None:
    """Add a Note to a PrettyMIDI Instrument."""
    global tied_to_notes

    if note in tied_to_notes:  # type: ignore
        return  # Note is tied from another, already handled
    dynamic = note.dynamic if note.dynamic is not None else 100
    if isinstance(dynamic, str):
        dynamic = string_to_velocity(dynamic)
    pm_note = pm.Note(
        velocity=dynamic,
        pitch=round(note.key_num),
        start=note.onset,
        end=note.onset + note.tied_duration,
    )
    if note.tie:
        note = note.tie
        while note:
            tied_to_notes[note] = True  # type: ignore
            note = note.tie  # type: ignore - follow chain of ties

    instrument.notes.append(pm_note)


def add_key_signature(
    onset: float, key_sig: int, key_signatures: list[pm.KeySignature]
) -> None:
    """Add a Key Signature change to the PrettyMIDI time signatures list."""
    # PrettyMIDI uses key number from -7 (7 flats) to +7 (7 sharps)
    location = len(key_signatures)  # default to appending at end
    for index, ts in enumerate(key_signatures):
        if isclose(ts.time, onset, abs_tol=1e-3) and ts.key_number == key_sig:
            return  # Key signature already exists at this time
        elif ts.time > onset + 1e-3:
            location = index
            break
    # now location is where to insert a new key signature
    pm_key_sig = pm.KeySignature(key_number=key_sig, time=onset)
    key_signatures.insert(location, pm_key_sig)


def add_eventgroup_to_instrument(
    evgroup: EventGroup,
    instrument: pm.Instrument,
    key_signatures: list[pm.KeySignature],
) -> None:
    """Add events from a Part or Staff to a PrettyMIDI Instrument.

    This function is recursive to process Notes in Measures, Chords, etc.
    """
    for event in evgroup.content:
        if isinstance(event, KeySignature):
            add_key_signature(event.onset, event.key_sig, key_signatures)
        elif isinstance(event, Note):
            note = cast(Note, event)
            add_note_to_instrument(note, instrument)
        elif isinstance(event, EventGroup):
            add_eventgroup_to_instrument(event, instrument, key_signatures)
        # else event is unhandled, hopefully a Rest, or Clef


def pretty_midi_midi_export(
    score: Score, filename: str, show: bool = False
) -> None:
    """
    Export a Score as a standard MIDI file using PrettyMIDI library.

    Parameters
    ----------
    score : Score
        The Score object to export.
    filename : str
        The path to the output MIDI file.
    """
    global tied_to_notes  # helps to merge tied notes
    tied_to_notes = {}

    score.convert_to_seconds()
    score.merge_tied_notes()

    # 600 gives 1 ms resolution at 100 bpm
    pmscore = pm.PrettyMIDI(resolution=600)

    # Create tempo changes from TimeMap
    tm = score.time_map
    if tm is not None:
        tick_scales = []
        for i in range(len(tm.changes)):
            bpm = tm.get_tempo_at(i)
            resolution = pmscore.resolution
            # form breakpoints with units of (ticks, seconds/tick)
            tick_scale = 60.0 / (bpm * resolution)
            tick_scales.append(
                (int(tm.changes[i].quarter * resolution), tick_scale)
            )
        pmscore._tick_scales = tick_scales

    # We want to write every Part or Staff as a separate PrettyMIDI Instrument
    # Gather the EventGroups to write. Note that the reader may reconstruct
    # The Part/Staff hierarchy if all Parts have different instruments and
    # read_score is invoked with the default group_by_instrument=True.
    evgroups: list[Part | Staff] = []
    for part in score.find_all(Part):  # type: ignore
        # search Part for any Notes at the top level
        part = cast(Part, part)
        if any(isinstance(ev, Note) for ev in part.content):
            evgroups.append(part)
        # search for Staffs within Part
        for staff in part.find_all(Staff):
            staff = cast(Staff, staff)
            evgroups.append(staff)
    key_signatures = []  # Collect key signatures for pmscore

    # Create instruments and add notes
    for evgroup in evgroups:
        # determine a name for the pm.Instrument
        if isinstance(evgroup, Part):
            part: Part = evgroup
        else:
            part = evgroup.part  # type: ignore
        name = part.instrument
        program = part.get("midi_program")
        if name is not None and program is None:
            try:
                program = pm.instrument_name_to_program(name)
            except Exception:
                program = None
        if program is None:
            program = 0  # Acoustic Grand Piano as default
        instrument = pm.Instrument(
            program, name=name if name is not None else "Unknown"
        )

        add_eventgroup_to_instrument(evgroup, instrument, key_signatures)
        pmscore.instruments.append(instrument)

    # Create time signature changes
    for ts in score.time_signatures:
        # Convert onset (in quarters) to seconds using time_map
        time_in_seconds = score.time_map.quarter_to_time(ts.time)
        pm_ts = pm.TimeSignature(
            numerator=int(ts.upper),
            denominator=int(ts.lower),
            time=time_in_seconds,
        )
        pmscore.time_signature_changes.append(pm_ts)

    # Add key signatures to pmscore
    pmscore.key_signature_changes = key_signatures

    # Force pretty_midi to use custom _tick_scales before writing:
    _ = pmscore.get_end_time()

    if show:
        from amads.io.pm_show import pretty_midi_show

        pretty_midi_show(pmscore, filename)

    # Write to MIDI file
    pmscore.write(filename)
    tied_to_notes = None  # clear global variable after use
