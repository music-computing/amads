"""
mido_midi_import.py

Import MIDI files into AMADS Score structure using the MIDO library.
No dependency on PrettyMIDI.

Functions
---------
- mido_midi_import(filename, format, flatten=False, collapse=False,
                   show=False, group_by_instrument=True) -> Score
"""

__author__ = "Roger B. Dannenberg"

import warnings
from collections import defaultdict
from math import isclose
from pathlib import Path
from typing import cast

import mido

from amads.core.basics import (
    KeySignature,
    Measure,
    Note,
    Part,
    Score,
    Staff,
    TimeSignature,
)
from amads.core.timemap import TimeMap

# General MIDI instrument names, indexed by program number 0-127
_GM_INSTRUMENTS = [
    # Piano (0-7)
    "Acoustic Grand Piano",
    "Bright Acoustic Piano",
    "Electric Grand Piano",
    "Honky-tonk Piano",
    "Electric Piano 1",
    "Electric Piano 2",
    "Harpsichord",
    "Clavinet",
    # Chromatic Percussion (8-15)
    "Celesta",
    "Glockenspiel",
    "Music Box",
    "Vibraphone",
    "Marimba",
    "Xylophone",
    "Tubular Bells",
    "Dulcimer",
    # Organ (16-23)
    "Drawbar Organ",
    "Percussive Organ",
    "Rock Organ",
    "Church Organ",
    "Reed Organ",
    "Accordion",
    "Harmonica",
    "Tango Accordion",
    # Guitar (24-31)
    "Nylon String Guitar",
    "Steel String Guitar",
    "Electric Jazz Guitar",
    "Electric Clean Guitar",
    "Electric Muted Guitar",
    "Overdriven Guitar",
    "Distortion Guitar",
    "Guitar Harmonics",
    # Bass (32-39)
    "Acoustic Bass",
    "Electric Bass (finger)",
    "Electric Bass (pick)",
    "Fretless Bass",
    "Slap Bass 1",
    "Slap Bass 2",
    "Synth Bass 1",
    "Synth Bass 2",
    # Strings (40-47)
    "Violin",
    "Viola",
    "Cello",
    "Contrabass",
    "Tremolo Strings",
    "Pizzicato Strings",
    "Orchestral Harp",
    "Timpani",
    # Ensemble (48-55)
    "String Ensemble 1",
    "String Ensemble 2",
    "Synth Strings 1",
    "Synth Strings 2",
    "Choir Aahs",
    "Voice Oohs",
    "Synth Choir",
    "Orchestra Hit",
    # Brass (56-63)
    "Trumpet",
    "Trombone",
    "Tuba",
    "Muted Trumpet",
    "French Horn",
    "Brass Section",
    "Synth Brass 1",
    "Synth Brass 2",
    # Reed (64-71)
    "Soprano Sax",
    "Alto Sax",
    "Tenor Sax",
    "Baritone Sax",
    "Oboe",
    "English Horn",
    "Bassoon",
    "Clarinet",
    # Pipe (72-79)
    "Piccolo",
    "Flute",
    "Recorder",
    "Pan Flute",
    "Blown Bottle",
    "Shakuhachi",
    "Whistle",
    "Ocarina",
    # Synth Lead (80-87)
    "Lead 1 (square)",
    "Lead 2 (sawtooth)",
    "Lead 3 (calliope)",
    "Lead 4 (chiff)",
    "Lead 5 (charang)",
    "Lead 6 (voice)",
    "Lead 7 (fifths)",
    "Lead 8 (bass + lead)",
    # Synth Pad (88-95)
    "Pad 1 (new age)",
    "Pad 2 (warm)",
    "Pad 3 (polysynth)",
    "Pad 4 (choir)",
    "Pad 5 (bowed)",
    "Pad 6 (metallic)",
    "Pad 7 (halo)",
    "Pad 8 (sweep)",
    # Synth Effects (96-103)
    "FX 1 (rain)",
    "FX 2 (soundtrack)",
    "FX 3 (crystal)",
    "FX 4 (atmosphere)",
    "FX 5 (brightness)",
    "FX 6 (goblins)",
    "FX 7 (echoes)",
    "FX 8 (sci-fi)",
    # Ethnic (104-111)
    "Sitar",
    "Banjo",
    "Shamisen",
    "Koto",
    "Kalimba",
    "Bag Pipe",
    "Fiddle",
    "Shanai",
    # Percussive (112-119)
    "Tinkle Bell",
    "Agogo",
    "Steel Drums",
    "Woodblock",
    "Taiko Drum",
    "Melodic Tom",
    "Synth Drum",
    "Reverse Cymbal",
    # Sound Effects (120-127)
    "Guitar Fret Noise",
    "Breath Noise",
    "Seashore",
    "Bird Tweet",
    "Telephone Ring",
    "Helicopter",
    "Applause",
    "Gunshot",
]

# Map MIDO key-string to AMADS sharps/flats count (-7 to +7)
_KEY_TO_SHARPS: dict[str, int] = {
    # Major keys
    "C": 0,
    "G": 1,
    "D": 2,
    "A": 3,
    "E": 4,
    "B": 5,
    "F#": 6,
    "C#": 7,
    "F": -1,
    "Bb": -2,
    "Eb": -3,
    "Ab": -4,
    "Db": -5,
    "Gb": -6,
    "Cb": -7,
    # Minor keys (same signature as their relative major)
    "Am": 0,
    "Em": 1,
    "Bm": 2,
    "F#m": 3,
    "C#m": 4,
    "G#m": 5,
    "D#m": 6,
    "A#m": 7,
    "Dm": -1,
    "Gm": -2,
    "Cm": -3,
    "Fm": -4,
    "Bbm": -5,
    "Ebm": -6,
    "Abm": -7,
}


def _mido_show(mid: mido.MidiFile, filename: str | Path) -> None:
    """Print a text summary of the MIDI file to stdout."""
    print(f"MIDI file: {filename}")
    print(
        f"  type={mid.type}, ticks_per_beat={mid.ticks_per_beat}, "
        f"tracks={len(mid.tracks)}"
    )
    for i, track in enumerate(mid.tracks):
        label = ""
        for msg in track:
            if hasattr(msg, "name") and msg.type == "track_name":
                label = f" ({msg.name})"
                break
        print(f"  Track {i}{label}: {len(track)} messages")
        cummulative = 0
        for msg in track:
            cummulative += msg.time
            cum_qtrs = cummulative / mid.ticks_per_beat
            print(f"    {cum_qtrs:.3f} qtrs: {msg}")


def _parse_meta_track(
    track: mido.MidiTrack,
    tpb: int,
) -> tuple[TimeMap, list, list]:
    """Parse a MIDI meta track and return tempo/time-signature/key-signature.

    Parameters
    ----------
    track : mido.MidiTrack
        The track to scan (typically track 0).
    tpb : int
        Ticks per beat (quarter note) from the MIDI file header.

    Returns
    -------
    tuple(TimeMap, list, list)
        * time_map — piecewise-linear quarter↔seconds map
        * ts_changes — ``[(quarter, numerator, denominator), ...]``
        * ks_changes — ``[(quarter, sharps_flats), ...]``
    """
    abs_tick = 0
    tempo_changes: list[tuple[float, float]] = []  # (quarter, qpm)
    ts_changes: list[tuple[float, int, int]] = []  # (quarter, num, den)
    ks_changes: list[tuple[float, int]] = []  # (quarter, sharps_flats)

    for msg in track:
        abs_tick += msg.time
        quarter = abs_tick / tpb
        if msg.type == "set_tempo":
            tempo_changes.append((quarter, mido.tempo2bpm(msg.tempo)))
        elif msg.type == "time_signature":
            ts_changes.append((quarter, msg.numerator, msg.denominator))
        elif msg.type == "key_signature":
            sharps = _KEY_TO_SHARPS.get(msg.key, 0)
            ks_changes.append((quarter, sharps))

    # Build TimeMap from tempo changes
    default_qpm = 120.0
    if tempo_changes and isclose(tempo_changes[0][0], 0.0):
        time_map = TimeMap(qpm=tempo_changes[0][1])
        remaining = tempo_changes[1:]
    else:
        time_map = TimeMap(qpm=default_qpm)
        remaining = tempo_changes

    for quarter, qpm in remaining:
        time_map.append_change(quarter, qpm)

    return time_map, ts_changes, ks_changes


def _extract_track_notes(
    track: mido.MidiTrack,
    tpb: int,
) -> tuple[str | None, dict[int, int], dict[int, list]]:
    """Extract note events from a MIDO track, grouped by MIDI channel.

    Parameters
    ----------
    track : mido.MidiTrack
    tpb : int
        Ticks per beat.

    Returns
    -------
    tuple(str | None, dict, dict)
        * track_name — value of the first ``track_name`` MetaMessage, or None
        * channel_programs — ``{channel: program_number}``
        * channel_notes — ``{channel: [(onset_q, duration_q, pitch, velocity), ...]}``
          Notes are in onset order (MIDI event order).
    """
    track_name: str | None = None
    channel_programs: dict[int, int] = {}
    # active_notes: (channel, pitch) -> FIFO list of (onset_tick, velocity)
    active_notes: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(
        list
    )
    channel_notes: dict[int, list] = defaultdict(list)

    abs_tick = 0
    for msg in track:
        abs_tick += msg.time
        if getattr(msg, "is_meta", False):
            if msg.type == "track_name":
                if track_name is None:
                    track_name = msg.name
            continue

        if msg.type == "program_change":
            channel_programs[msg.channel] = msg.program

        elif msg.type == "note_on" and msg.velocity > 0:
            active_notes[(msg.channel, msg.note)].append(
                (abs_tick, msg.velocity)
            )

        elif msg.type == "note_off" or (
            msg.type == "note_on" and msg.velocity == 0
        ):
            key = (msg.channel, msg.note)
            if active_notes[key]:
                onset_tick, velocity = active_notes[key].pop(0)  # FIFO
                onset_q = onset_tick / tpb
                duration_q = (abs_tick - onset_tick) / tpb
                channel_notes[msg.channel].append(
                    (onset_q, duration_q, msg.note, velocity)
                )

    # Warn about and drop any unclosed notes
    for (channel, pitch), onsets in active_notes.items():
        if onsets:
            warnings.warn(
                f"MIDI note (channel {channel}, pitch {pitch}) has no "
                f"note_off event; {len(onsets)} note(s) ignored.",
                stacklevel=4,
            )

    return track_name, channel_programs, dict(channel_notes)


def _create_measures(
    staff: Staff,
    score_duration: float,
    ts_changes: list,
    ks_changes: list,
) -> None:
    """Create Measure objects in *staff* according to time/key signature changes.

    Does **not** modify ``score.time_signatures``; call sites are responsible
    for building that list separately.

    Parameters
    ----------
    staff : Staff
    score_duration : float
        Total duration in quarters; used as the end sentinel.
    ts_changes : list[(quarter, numerator, denominator)]
        Sorted list of time-signature changes in quarters.
    ks_changes : list[(quarter, key_sig)]
        Sorted list of key-signature changes in quarters.
    """
    cur_upper: int = 4
    cur_lower: int = 4
    cur_duration: float = 4.0
    cur_beat: float = 0.0

    k = 0  # index into ks_changes
    i = 0
    while i <= len(ts_changes):
        tbeat = ts_changes[i][0] if i < len(ts_changes) else score_duration

        while cur_beat < tbeat - 1e-6:
            measure = Measure(onset=cur_beat, duration=cur_duration)
            staff.insert(measure)

            # Insert key signature into this measure if one is due. If there
            # are multiple key signatures due, insert only the last one.
            while (
                k + 1 < len(ks_changes)
                and cur_beat > ks_changes[k + 1][0] - 1e-6
            ):
                k = k + 1  # skip to the next key signature change at this time
            if k < len(ks_changes) and cur_beat > ks_changes[k][0] - 1e-6:
                _ = KeySignature(measure, cur_beat, ks_changes[k][1])
                k += 1
            cur_beat += cur_duration

        # Advance to the next time signature
        if i < len(ts_changes):
            upper, lower = ts_changes[i][1], ts_changes[i][2]
            if not isclose(cur_beat, tbeat, abs_tol=1e-6):
                warnings.warn(
                    f"MIDI file time signature change at beat {tbeat}"
                    " is not on the expected measure boundary at"
                    f" {cur_beat}. The time signature {upper}/{lower}"
                    f" will be applied at {cur_beat}.",
                    stacklevel=4,
                )
            cur_upper = upper
            cur_lower = lower
            cur_duration = cur_upper * 4 / cur_lower
        i += 1


def _add_notes_to_measures(
    notes: list[Note], measures: list[Measure], tpb: int
) -> None:
    """Add notes to measures and tie notes that cross measure boundaries.

    All times must be in the same unit (quarters).

    Parameters
    ----------
    notes : list[Note]
        Notes in onset order.  Each note's ``parent`` will be reset to its
        containing measure.
    measures : list[Measure]
    tpb : int
        Ticks per beat; used to derive the floating-point epsilon for rounding.
    """
    EPS = 0.5 / tpb  # one half-tick in quarters
    i = 0
    for mi, m in enumerate(measures):
        m_insert = m
        m_insert_i = mi
        while i < len(notes) and notes[i].onset < m.offset:
            note = notes[i]
            note.parent = None  # detach from old parent (Part)
            # If the note onset is right at the measure boundary, push it
            # forward into the next measure to avoid a zero-duration fragment
            if note.onset > m.offset - EPS:
                offset = note.offset
                m_insert_i = mi + 1
                m_insert = measures[m_insert_i]
                note.onset = m_insert.onset
                note.duration = offset - note.onset
            remaining = 0.0
            if note.offset > m_insert.offset:  # note crosses measure boundary
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
                    pitch=note.pitch,
                    dynamic=note.dynamic,
                )
                prev_note.tie = tied_note
                prev_note = tied_note
                next_i += 1
                remaining -= tied_note.duration
            i += 1


def mido_midi_import(
    filename: str | Path,
    format: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
    ignore_hidden=False,
) -> Score:
    """Import a MIDI file and return an AMADS ``Score`` using the MIDO library.

    No PrettyMIDI dependency.  The returned score uses *quarters* as its
    time unit (the default for the Score constructor).

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    filename : str | Path
        Path to the MIDI file.
    format : str
        File format string; must be ``"midi"``.
    flatten : bool, optional
        If True, notes become direct children of Parts (no Staff/Measure
        structure).  Defaults to *collapse*, which defaults to False.
    collapse : bool, optional
        If True, merge all parts into a single Part.  Implies *flatten*.
    show : bool, optional
        If True, print the raw MIDO file contents to stdout.
    group_by_instrument : bool, optional
        If True (default), tracks with the same instrument name are merged
        as multiple Staffs under one Part.
    ignore_hidden: bool
        Unused in MIDI import. See read_score() for details.


    Returns
    -------
    Score
        Score in quarters.

    Examples
    --------
    >>> from amads.io.readscore import read_score, set_preferred_midi_reader
    >>> from amads.io.readscore import set_reader_warning_level
    >>> from amads.music import example
    >>> # 'mido' is already the default, but make sure it is set as expected
    >>> _ = set_preferred_midi_reader("mido")
    >>> _ = set_reader_warning_level("default")
    >>> score = read_score(example.fullpath("midi/sarabande.mid"),
    ...                    flatten=True)  # doctest: +ELLIPSIS
    Reading ... using midi reader file=mido_midi_import.
    """
    flatten = flatten or collapse

    mid = mido.MidiFile(str(filename))
    if show:
        _mido_show(mid, filename)

    tpb: int = mid.ticks_per_beat

    # --- Parse track 0 for tempo map, time signatures, key signatures ---
    time_map, ts_changes, ks_changes = _parse_meta_track(mid.tracks[0], tpb)

    # Create Score (works in quarters by default)
    score = Score(time_map=time_map)

    # --- Determine which tracks carry note events ---
    if mid.type == 0:
        # Single-track file: everything (meta + notes) is in track 0
        note_track_list = [(0, mid.tracks[0])]
    else:
        # Type 1/2: track 0 is the global tempo/meta track;
        # subsequent tracks carry notes (and possibly track-level meta).
        note_track_list = [
            (i, t) for i, t in enumerate(mid.tracks[1:], start=1)
        ]
        # Collect notes from track 0 too if it happens to contain any
        if any(
            not getattr(msg, "is_meta", True)
            and msg.type in ("note_on", "note_off")
            for msg in mid.tracks[0]
        ):
            note_track_list = [(0, mid.tracks[0])] + note_track_list

    # --- Extract notes and build flat Parts ---
    instrument_groups: dict[str, list[Part]] = {}
    max_duration_q: float = 0.0
    no_name_id = 1

    for _track_idx, track in note_track_list:
        track_name, channel_programs, channel_notes = _extract_track_notes(
            track, tpb
        )

        for channel, notes_list in channel_notes.items():
            if not notes_list:
                continue

            # Determine instrument name for this channel
            if channel == 9:
                name: str | None = "Drums"  # GM percussion channel
            else:
                program = channel_programs.get(channel, 0)
                name = track_name if track_name else None
                if name is None:
                    name = (
                        _GM_INSTRUMENTS[program] if 0 <= program < 128 else None
                    )

            if name == "Unknown":
                name = None

            part = Part(parent=score, onset=0.0, instrument=name)

            for onset_q, duration_q, pitch, velocity in notes_list:
                Note(
                    parent=part,
                    onset=onset_q,
                    duration=duration_q,
                    pitch=pitch,
                    dynamic=velocity,
                )
                max_duration_q = max(max_duration_q, onset_q + duration_q)

            # Group key for instrument grouping
            group_key = (
                name
                if (name and group_by_instrument)
                else f"_None~@_{no_name_id}"
            )
            if not name or not group_by_instrument:
                no_name_id += 1

            group = instrument_groups.get(group_key, [])
            group.append(part)
            instrument_groups[group_key] = group

    score.duration = max_duration_q
    for part in score.content:
        part.duration = max_duration_q

    # --- Optionally collapse all parts into one ---
    if collapse:
        score = score.flatten(collapse=True)

    # --- Optionally build Staff/Measure structure ---
    if not flatten:
        # Build score.time_signatures from ts_changes (once, not per staff)
        score.time_signatures = [TimeSignature(0.0, 4, 4)]
        for q, u, l in ts_changes:
            score.append_time_signature(TimeSignature(q, u, l))

        score.content.clear()  # remove flat Parts; we'll rebuild with Staffs
        for group in instrument_groups.values():
            new_part = group[0].insert_emptycopy_into(score)
            new_part = cast(Part, new_part)
            new_part.duration = score.duration
            for old_part in group:
                old_part = cast(Part, old_part)
                notes = old_part.content
                staff = Staff(
                    parent=new_part, onset=0.0, duration=new_part.duration
                )
                _create_measures(staff, score.duration, ts_changes, ks_changes)
                _add_notes_to_measures(
                    cast(list[Note], notes),
                    cast(list[Measure], staff.content),
                    tpb,
                )
                old_part.content.clear()

    return score
