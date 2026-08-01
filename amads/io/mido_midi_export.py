"""
Export a Score as a standard MIDI file using the MIDO library.

Usage
-----
Do not use this module directly; see writescore.py.

Notes
-----
This implementation correctly handles zero-duration notes (grace notes) by
emitting a note_on event followed immediately (delta time = 0) by a note_on
with velocity 0 (which acts as note_off), preserving the original score order.
This avoids the timestamp-collision reordering problem in PrettyMIDI, where
multiple events at the same time can be reordered, making it impossible to
recover original note durations.

The sort order for events within a track at the same tick is:
  - Regular note_off (note_on velocity=0) events come before new note_on
    events (standard SMF convention).
  - For zero-duration (grace) notes, note_on is followed immediately by its
    note_off, in score order.

"""

from pathlib import Path
from typing import cast

import mido

from amads.core.basics import EventGroup, KeySignature, Note, Part, Score, Staff
from amads.core.timemap import TimeMap  # needed for tm.changes in meta track
from amads.io.mido_midi_import import _mido_show
from amads.io.pm_midi_export import _get_midi_time_signatures

__author__ = "Roger B. Dannenberg"

TICKS_PER_BEAT = 600  # 600 ticks/quarter gives ~1 ms resolution at 100 BPM

# Maps sharps/flats count to MIDI key-signature name (major keys assumed).
# Positive = sharps, negative = flats, following circle of fifths.
_SHARPS_TO_KEY = {
    0: "C",
    1: "G",
    2: "D",
    3: "A",
    4: "E",
    5: "B",
    6: "F#",
    7: "C#",
    -1: "F",
    -2: "Bb",
    -3: "Eb",
    -4: "Ab",
    -5: "Db",
    -6: "Gb",
    -7: "Cb",
}

tied_to_notes = (
    None  # global to help skip tied-to notes, mirroring pm_midi_export
)


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
    return dynamic_map.get(dynamic.lower(), 100)


def _collect_notes_from_evgroup(evgroup: EventGroup) -> list[Note]:
    """Recursively collect notes from an EventGroup in score order.

    Skips notes that are targets of ties (already accounted for by the
    first note in the tied chain via ``note.tied_duration``).

    Parameters
    ----------
    evgroup : EventGroup
        The Part, Staff, Measure, Chord, etc. to collect from.

    Returns
    -------
    list[Note]
        Notes in document order, with tied-to notes excluded.
    """
    global tied_to_notes
    notes = []
    for event in evgroup.content:
        if isinstance(event, Note):
            note = cast(Note, event)
            if note in tied_to_notes:  # type: ignore
                continue  # this note is a tied-to target; already handled
            # Mark every note in the tie chain so it is skipped later.
            if note.tie:
                tied = note.tie
                while tied:
                    tied_to_notes[tied] = True  # type: ignore
                    tied = tied.tie  # type: ignore
            notes.append(note)
        elif isinstance(event, EventGroup):
            notes.extend(_collect_notes_from_evgroup(event))
        # Rests, Clefs, KeySignatures, etc. are ignored here.
    return notes


def _build_meta_track(score: Score, tm: TimeMap) -> mido.MidiTrack:
    """Build the Type-1 MIDI tempo track (track 0).

    Contains set_tempo, time_signature, and key_signature meta messages.

    Parameters
    ----------
    score : Score
        The score being exported.
    tm : TimeMap
        The score's time map.

    Returns
    -------
    mido.MidiTrack
        The completed meta track.
    """
    # Collect meta events as (abs_tick, type_order, index, MetaMessage).
    # type_order: 0=tempo, 1=time_sig, 2=key_sig  — determines ordering at
    # the same tick, matching standard SMF conventions.
    meta_events: list[tuple] = []

    # --- Tempo changes ---
    for i, change in enumerate(tm.changes):
        bpm = tm.get_tempo_at(i)
        abs_tick = round(change.quarter * TICKS_PER_BEAT)
        meta_events.append(
            (
                abs_tick,
                0,
                i,
                mido.MetaMessage(
                    "set_tempo", tempo=mido.bpm2tempo(bpm), time=0
                ),
            )
        )

    # --- Time signatures ---
    # ts.quarters is always in quarter-note units (invariant under
    # convert_to_seconds), so ticks = quarters * TICKS_PER_BEAT directly.
    tss = _get_midi_time_signatures(score)
    for i, ts in enumerate(tss):  # ts is (quarters, upper, lower)
        abs_tick = round(ts[0] * TICKS_PER_BEAT)
        meta_events.append(
            (
                abs_tick,
                1,
                i,
                mido.MetaMessage(
                    "time_signature",
                    numerator=int(ts[1]),
                    denominator=int(ts[2]),
                    time=0,
                ),
            )
        )

    # --- Key signatures ---
    # KeySignature events have onset in quarters (invariant under
    # convert_to_quarters), so ticks = onset * TICKS_PER_BEAT directly.
    seen_key_sigs: dict[int, str] = {}  # abs_tick → key name (deduplicate)
    for ks_event in score.find_all(KeySignature):
        ks = cast(KeySignature, ks_event)
        key_name = _SHARPS_TO_KEY.get(ks.key_sig, "C")
        abs_tick = round(ks.onset * TICKS_PER_BEAT)
        if seen_key_sigs.get(abs_tick) != key_name:
            seen_key_sigs[abs_tick] = key_name
            meta_events.append(
                (
                    abs_tick,
                    2,
                    abs_tick,
                    mido.MetaMessage("key_signature", key=key_name, time=0),
                )
            )

    # Sort: primarily by tick, then by type_order, then by index.
    meta_events.sort(key=lambda e: (e[0], e[1], e[2]))

    track = mido.MidiTrack()
    prev_tick = 0
    for abs_tick, _type, _idx, msg in meta_events:
        delta = abs_tick - prev_tick
        track.append(msg.copy(time=delta))
        prev_tick = abs_tick

    track.append(mido.MetaMessage("end_of_track", time=0))
    return track


def _build_instrument_track(
    evgroup: EventGroup, channel: int, program: int, name: str
) -> mido.MidiTrack:
    """Build a MIDI track for one instrument part (Part or Staff).

    Zero-duration notes (grace notes) are written as a note_on immediately
    followed by a note_on with velocity 0 (delta = 0), preserving their
    original order from the Score.

    Parameters
    ----------
    evgroup : EventGroup
        The Part or Staff whose notes are written to the track.
    channel : int
        MIDI channel (0–15) to use for all events in this track.
    program : int
        MIDI program number (0–127) for the instrument.
    name : str
        Instrument name written as the track name meta message.

    Returns
    -------
    mido.MidiTrack
        The completed instrument track.
    """
    track = mido.MidiTrack()

    # Track name and program change at tick 0.
    track.append(mido.MetaMessage("track_name", name=name, time=0))
    if program is not None:
        track.append(
            mido.Message(
                "program_change", channel=channel, program=program, time=0
            )
        )

    # Collect notes in document order (tied-to notes already excluded by
    # _collect_notes_from_evgroup via the global tied_to_notes dict).
    notes = _collect_notes_from_evgroup(evgroup)

    # Build a flat event list: (abs_tick, sort_key, mido.Message)
    #
    # Sort key ensures correct SMF ordering at the same tick:
    #   (0, seq)       — regular note_off (velocity=0); note_offs before
    #                    new note_ons at the same tick (standard convention)
    #   (1, seq*2)     — note_on (regular or grace)
    #   (1, seq*2+1)   — grace note_off (immediately after its note_on)
    events: list[tuple] = []
    minimum_onset: dict[int, int] = {}  # pitch → earliest allowed onset tick

    for seq, note in enumerate(notes):
        dynamic = note.dynamic if note.dynamic is not None else 100
        if isinstance(dynamic, str):
            dynamic = string_to_velocity(dynamic)
        velocity = min(127, max(1, int(dynamic)))
        note_num = min(127, max(0, round(note.key_num)))

        onset_tick = round(note.onset * TICKS_PER_BEAT)
        # tied_duration spans the full duration including any tied notes.
        dur = max(note.tied_duration, 0.001)  # force non-zero duration
        offset_tick = round((note.onset + dur) * TICKS_PER_BEAT)

        # check for minimum onset for this pitch
        onset_tick = max(onset_tick, minimum_onset.get(note_num, 0))

        # update minimum onset for this pitch to the new offset
        minimum_onset[note_num] = offset_tick

        note_on = mido.Message(
            "note_on", channel=channel, note=note_num, velocity=velocity, time=0
        )
        note_off = mido.Message(
            "note_on", channel=channel, note=note_num, velocity=0, time=0
        )  # note_on vel=0 = note_off

        if onset_tick == offset_tick:
            # Zero-duration (grace) note: note_on then note_off at same tick,
            # kept together and in score order.
            events.append((onset_tick, (1, seq * 2), note_on))
            events.append((onset_tick, (1, seq * 2 + 1), note_off))
        else:
            events.append((onset_tick, (1, seq * 2), note_on))
            events.append((offset_tick, (0, seq * 2), note_off))

    # Sort by (abs_tick, sort_key).  Python tuple comparison is
    # lexicographic, so this enforces note_offs before note_ons at equal
    # ticks, and grace note pairs stay together.
    events.sort(key=lambda e: (e[0], e[1]))

    # Convert absolute ticks to delta times and append to track.
    prev_tick = 0
    for abs_tick, _key, msg in events:
        delta = abs_tick - prev_tick
        track.append(msg.copy(time=delta))
        prev_tick = abs_tick

    track.append(mido.MetaMessage("end_of_track", time=0))
    return track


def mido_midi_export(
    score: Score,
    filename: str | Path,
    format: str,
    show: bool,
    is_temp: bool = False,
) -> None:  # type: ignore  (unused parameter)
    """
    Export a Score as a standard MIDI file using the MIDO library.

    Unlike PrettyMIDI, MIDO writes note_on and note_off events in the order
    they are appended to a track, so zero-duration notes (grace notes) *could*
    be correctly encoded as a note_on immediately followed (delta=0) by a
    note_on with velocity 0, preserving the original note sequence from
    the Score. However, these files cannot be read by pretty_midi, so we
    change the duration to 0.001 quarters.

    This causes another problem if there is a zero-length note followed by
    another note at the same pitch: moving the note-off of the first note
    after the note-on of the first creates overlapping notes, which is not
    well-defined in MIDI. We solve this problem by tracking the minimum_onset
    allowed for each pitch (key_number) and moving the onset later if it
    comes before the offset of a note already sounding.

    Parameters
    ----------
    score : Score
        The Score object to export.
    filename : str | Path
        The path to the output MIDI file.
    format : str
        The export format, should be "midi" for this function.
    show : bool
        Print a text representation of the MIDI data before writing.
    is_temp : bool
        Ignored; no temporary files are created.
    """
    global tied_to_notes
    tied_to_notes = {}

    score.convert_to_quarters()  # ticks = quarters * TICKS_PER_BEAT exactly
    score.merge_tied_notes()  # updates tied_duration; result not reassigned

    mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)
    tm = score.time_map

    # Track 0: tempo / time-signature / key-signature meta track.
    mid.tracks.append(_build_meta_track(score, tm))

    # Determine which EventGroups become separate MIDI tracks.
    # A Part that contains Notes directly is written as its own track.
    # Every Staff within a Part is also written as its own track.
    evgroups: list[Part | Staff] = []
    for part in score.find_all(Part):  # type: ignore
        part = cast(Part, part)
        if any(isinstance(ev, Note) for ev in part.content):
            evgroups.append(part)
        for staff in part.find_all(Staff):
            evgroups.append(cast(Staff, staff))

    # Assign MIDI channels sequentially, skipping channel 9 (GM percussion).
    channel = -1

    for evgroup in evgroups:
        # Advance to the next available channel, skipping 9.
        channel = (channel + 1) % 16
        if channel == 9:
            channel = 10

        # Determine the Part that owns this evgroup (for instrument info).
        if isinstance(evgroup, Part):
            part = evgroup
        else:
            part = cast(Part, evgroup.part)  # type: ignore

        name = part.instrument
        program = part.get("midi_program")

        track = _build_instrument_track(
            evgroup, channel, program, name if name is not None else "Unknown"
        )
        mid.tracks.append(track)

    if show:
        _mido_show(mid, filename)

    mid.save(str(filename))
    tied_to_notes = None  # clear global after use
