"""
Export a Score as a standard MIDI file using PrettyMIDI library.

Usage
-----
Do not use this module directly; see writescore.py.

Notes
-----
See `export_midi` notes for translation-to-MIDI-file details.

"""

from math import isclose
from pathlib import Path
from typing import cast

import pretty_midi as pm

from amads.core.basics import (
    EventGroup,
    KeySignature,
    Measure,
    Note,
    Part,
    Score,
    Staff,
)

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


def add_note_to_instrument(
    note: Note,
    instrument: pm.Instrument,
    minimum_duration: float,
    minimum_onset: dict[int, float],
) -> None:
    """Add a Note to a PrettyMIDI Instrument."""
    global tied_to_notes

    if note in tied_to_notes:  # type: ignore
        return  # Note is tied from another, already handled
    dynamic = note.dynamic if note.dynamic is not None else 100
    if isinstance(dynamic, str):
        dynamic = string_to_velocity(dynamic)
    pitch = round(note.key_num)
    start = note.onset
    end = start + note.tied_duration
    start = max(start, minimum_onset.get(pitch, 0.0))
    end = max(end, start + minimum_duration)
    minimum_onset[pitch] = end  # update for next note of same pitch

    pm_note = pm.Note(
        velocity=dynamic,
        pitch=pitch,
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
    # Our key_sig uses key number from -7 (7 flats) to +7 (7 sharps)
    # PrettyMIDI's KeySignature uses a key number 0-12 for Major, 12-23 for
    # minor. We will assume that all key signatures are Major. Convert from
    # flats/sharps to key number using circle of fifths:
    key_number = (1200 + (key_sig * 7)) % 12
    location = len(key_signatures)  # default to appending at end
    for index, ks in enumerate(key_signatures):
        if (
            isclose(ks.time, onset, abs_tol=1e-3)
            and ks.key_number == key_number
        ):
            return  # Key signature already exists at this time
        elif ks.time > onset + 1e-3:
            location = index
            break
    # now location is where to insert a new key signature
    # our KeySignature class encodes only the number of flats/sharps, while
    pm_key_sig = pm.KeySignature(key_number=key_number, time=onset)
    key_signatures.insert(location, pm_key_sig)


def add_eventgroup_to_instrument(
    evgroup: EventGroup,
    instrument: pm.Instrument,
    key_signatures: list[pm.KeySignature],
    minimum_duration: float,
    minimum_onset: dict[int, float],
) -> None:
    """Add events from a Part or Staff to a PrettyMIDI Instrument.

    This function is recursive to process Notes in Measures, Chords, etc.
    """
    for event in evgroup.content:
        if isinstance(event, KeySignature):
            add_key_signature(event.onset, event.key_sig, key_signatures)
        elif isinstance(event, Note):
            note = cast(Note, event)
            add_note_to_instrument(
                note, instrument, minimum_duration, minimum_onset
            )
        elif isinstance(event, EventGroup):
            add_eventgroup_to_instrument(
                event,
                instrument,
                key_signatures,
                minimum_duration,
                minimum_onset,
            )
        # else event is unhandled, hopefully a Rest, or Clef


def _get_midi_time_signatures(
    score: Score,
) -> list[tuple[float, int, int, float]]:
    """Create time signature changes found in AMADS Score."""
    time_signatures = []
    if score.is_well_formed_full_score():
        # check for short measures in first staff
        staff = next(score.find_all(Staff), None)
        ts = score.time_signatures
        tsi = 0
        need_ts = True  # always insert default 4/4 if nothing else is there
        upper = 4
        lower = 4
        if staff is not None:
            staff = cast(Staff, staff)
            for measure in staff.find_all(Measure):
                # if there is a time signature at the start of the measure,
                # it will provide the lower number for a time signature.
                if tsi < len(ts) and isclose(
                    measure.onset, ts[tsi].quarters, abs_tol=1e-3
                ):
                    need_ts = True
                    upper = ts[tsi].upper
                    lower = ts[tsi].lower
                if not isclose(
                    measure.duration, upper * 4 / lower, abs_tol=1e-3
                ):
                    need_ts = True
                    upper = measure.duration * lower / 4
                    # if measure is fractional, e.g., 0.5/4, then increase lower
                    # to get, e.g., 1/8 (which could be for a 1/8 pickup note).
                    while lower < 128 and not isclose(
                        upper, round(upper), abs_tol=1e-3
                    ):
                        lower *= 2
                        upper *= 2
                    # maximum lower is 128, and at this point we just assume
                    # upper is an integer (or close to one).
                    upper = round(upper)
                if need_ts:
                    time_signatures.append(
                        (measure.onset, upper, lower, upper * 4 / lower)
                    )
                    need_ts = False
    return time_signatures


def pretty_midi_export(
    score: Score,
    filename: str | Path,
    format: str,
    show: bool,
    is_temp: bool,
    minimum_duration: float = 0.0,
) -> None:
    """
    Export a Score as a standard MIDI file using PrettyMIDI library.

    Parameters
    ----------
    score : Score
        The Score object to export.
    filename : str | Path
        The path to the output MIDI file.
    format : str
        The export format, should be "midi" for this function.
    show : bool
        Print a text representation of the data.
    is_temp : bool
        This is ignored since we do not create temp files here.
    minimum_duration : float
        If greater than 0, then notes in MIDI file output will be extended
        to at least this duration. This is useful when grace notes are
        encoded with zero duration, but you want them to be visible and
        audible as MIDI.
    """
    global tied_to_notes  # helps to merge tied notes
    tied_to_notes = {}

    score = cast(Score, score.merge_tied_notes())
    score.convert_to_quarters()
    # Create time signature changes
    midi_tss = _get_midi_time_signatures(score)

    score.convert_to_seconds()

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

        add_eventgroup_to_instrument(
            evgroup, instrument, key_signatures, minimum_duration, {}
        )
        pmscore.instruments.append(instrument)

    for ts in midi_tss:  # tuples: (time, upper, lower, duration)
        tsec = score.time_map.quarter_to_time(ts[0])
        # PrettyMIDI uses a 128th note as the denominator, so we
        # convert from AMADS quarter note units to 128th notes.
        pm_ts = pm.TimeSignature(numerator=ts[1], denominator=ts[2], time=tsec)
        pmscore.time_signature_changes.append(pm_ts)

    # Add key signatures to pmscore
    pmscore.key_signature_changes = key_signatures

    # Force pretty_midi to use custom _tick_scales before writing:
    _ = pmscore.get_end_time()

    if show:
        from amads.io.pm_show import pretty_midi_show

        pretty_midi_show(pmscore, str(filename))

    # Write to MIDI file
    pmscore.write(str(filename))
    tied_to_notes = None  # clear global variable after use
