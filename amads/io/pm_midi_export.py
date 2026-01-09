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
PrettyMIDI has a "hidden" representation of the MIDI tempo track in
`_tick_scales`, which has the form [(tick, tick_duration), ...]. We
need to create this from TimeMap.
"""

from typing import cast

import pretty_midi as pm

from amads.core.basics import Note, Part, Score

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
    score = score.flatten()
    score.convert_to_seconds()
    # 600 gives 1 ms resolution at 100 bpm
    pmscore = pm.PrettyMIDI(resolution=600)
    # Create instruments and add notes
    for part in score.find_all(Part):
        part = cast(Part, part)
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
        for note in part.content:  # content is all Notes
            note = cast(Note, note)
            dynamic = note.dynamic if note.dynamic is not None else 100
            if isinstance(dynamic, str):
                dynamic = string_to_velocity(dynamic)
            pm_note = pm.Note(
                velocity=dynamic,
                pitch=round(note.key_num),
                start=note.onset,
                end=note.offset,
            )
            instrument.notes.append(pm_note)
        pmscore.instruments.append(instrument)

    # Create tempo changes from TimeMap
    tm = score.time_map
    if tm is not None:
        tick_scales = []
        for i in range(len(tm.changes)):
            bpm = tm.get_tempo_at(i)
            resolution = pmscore.resolution
            tick_scale = 60.0 / (bpm * resolution)
            tick_scales.append(
                (int(tm.changes[i].time * resolution), tick_scale)
            )
        pmscore._tick_scales = tick_scales

    if show:
        from amads.io.pm_show import pretty_midi_show

        pretty_midi_show(pmscore, filename)
    # Write to MIDI file
    pmscore.write(filename)
