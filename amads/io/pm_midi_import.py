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
PrettyMIDI has a "hidden" representation of teh MIDI tempo track in
`_tick_scales`, which has the form [(tick, tick_duration), ...]. We
need to convert this to a TimeMap.
"""

__author__ = "Roger B. Dannenberg <rbd@cs.cmu.edu>"

import warnings

from pretty_midi import PrettyMIDI

from ..core.basics import Measure, Note, Part, Score, Staff
from ..core.timemap import TimeMap

_pitch_names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def _show_pretty_midi(pmscore: PrettyMIDI, filename: str) -> None:
    # Print the PrettyMIDI score structure for debugging
    print(f"PrettyMIDI score structure from {filename}:")
    print(f"end_time: {pmscore.get_end_time()}")
    if pmscore.key_signature_changes and len(pmscore.key_signature_changes) > 0:
        for sig in pmscore.key_signature_changes:
            key = _pitch_names[sig.key_number % 12]
            key += " major" if sig.key_number < 12 else " minor"
            print(
                f"    KeySignature(time={sig.time},"
                f" key_number={sig.key_number}) {key}"
            )
    if pmscore.time_signature_changes and len(pmscore.time_signature_changes) > 0:
        for sig in pmscore.time_signature_changes:
            print(
                f"    TimeSignature(time={sig.time},"
                f" numerator={sig.numerator},"
                f" denominator={sig.denominator})"
            )
    for ins in pmscore.instruments:
        drum_str = ", is_drum" if ins.is_drum else ""
        print(f"    Instrument(name={ins.name}," f" program={ins.program}{drum_str})")
        if ins.pitch_bends and len(ins.pitch_bends) > 0:
            print(f"        ignoring {len(ins.pitch_bends)} pitch bends")
        if ins.control_changes and len(ins.control_changes) > 0:
            print(f"        ignoring {len(ins.control_changes)}" " control changes")
        for note in ins.notes:
            print(
                f"        Note(start={note.start},"
                f" duration={note.get_duration()},"
                f" pitch={note.pitch},"
                f" velocity={note.velocity})"
            )
    if pmscore.lyrics and len(pmscore.lyrics) > 0:
        for lyric in pmscore.lyrics:
            print(f"    Lyric(time={lyric.time}, text={lyric.text})")
    if (
        hasattr(pmscore, "text_events")
        and pmscore.text_events
        and pmscore(pmscore.text_events) > 0
    ):
        print("    Text events (not imported by AMADS):")
        for text in pmscore.text_events:
            print(f"        Text(time={text.time}, text={text.text})")


def _time_map_from_tick_scales(tick_scales, resolution: int) -> TimeMap:
    """Convert "hidden" _tick_scales list to AMADS TimeMap, representing the
    midi file tempo map
    """
    ticks_per_second = 1.0 / tick_scales[0][1]
    time_map = TimeMap(bpm=ticks_per_second * 60 / resolution)
    for change in tick_scales[1:]:
        time_map.append_beat_tempo(
            change[0] / resolution, 60.0 / (change[1] * resolution)
        )
    return time_map


def _create_measures(
    staff: Staff, time_map: TimeMap, end_beat: float, notes: list, pmscore: PrettyMIDI
) -> None:
    """Create measures in Staff according to pmscore data

    To deal with float approximation, we round beat times to 1/32 since
    time signatures are always n/(2^d), e.g. 4/4, 3/16, ....
    """
    # insert measures according to time_signature_changes:
    current_duration = 4  # default is 4/4
    current_beat = 0  # we have created measures up to this time
    for sig in pmscore.time_signature_changes:
        beat = time_map.time_to_beat(sig.time)
        beat = round(beat * 32) / 32  # quantize measure boundaries
        while current_beat < beat:  # fill in measures using current_duration
            staff.insert(Measure(onset=current_beat, duration=current_duration))
            current_beat += current_duration
        if current_beat != beat:
            sig_str = str(sig.numerator) + "/" + str(sig.denominator)
            warnings.warn(
                f"MIDI file time signature change at beat {beat}"
                " is not on the expected measure boundary at"
                f" {current_beat}. The time signature {sig_str}"
                f" will be applied at {current_beat}."
            )
        current_duration = sig.numerator * 4 / sig.denominator

    # fill out measures to end_beat
    while current_beat < end_beat:
        staff.insert(Measure(onset=current_beat, duration=current_duration))
        current_beat += current_duration


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
                    pitch=note.pitch,
                    dynamic=note.dynamic,
                )
                prev_note.tie = tied_note
                prev_note = tied_note
                next_i += 1
                remaining -= tied_note.duration
            i += 1


def pretty_midi_midi_import(
    filename: str, flatten: bool = False, collapse: bool = False, show: bool = False
) -> Score:
    """
    Use PrettyMIDI to import a MIDI file and convert it to a Score.

    Parameters
    ----------
    filename : Union(str, PosixPath)
        The path to the MIDI file to import.
    flatten : bool, optional
        If True, create a flattened score where notes are direct children of
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
        _show_pretty_midi(pmscore, filename)

    # Create an empty Score object
    time_map = _time_map_from_tick_scales(pmscore._tick_scales, pmscore.resolution)
    score = Score(time_map=time_map)
    score.convert_to_seconds()  # convert to seconds for PrettyMIDI

    # Iterate over instruments of the PrettyMIDI score and build parts and notes
    # Then if collapse, merge and sort the notes
    # Then if not flatten, remove each part content, and staff and measures,
    # and move notes into measures, creating ties where they cross
    # Iterate over instruments of the PrettyMIDI score and build parts and notes
    for ins in pmscore.instruments:
        part = Part(parent=score, onset=0.0, instrument=ins.name)
        for note in ins.notes:
            # Create a Note object and associate it with the Part
            Note(
                parent=part,
                onset=note.start,
                duration=note.get_duration(),
                pitch=note.pitch,
                dynamic=note.velocity,
            )
            part.duration = max(part.duration, note.end)

    # Then if collapse, merge and sort the notes
    if collapse:
        score = score.flatten(collapse=True)

    score.convert_to_quarters()  # we want to return with quarters as time unit

    # Then if not flatten, remove each part content, and staff and measures,
    # and move notes into measures, creating ties where they cross.
    if not flatten:
        for part in score.content:
            notes = part.content
            part.content = []  # Remove existing content
            # now notes have part as parent, but parent does not have notes
            staff = Staff(parent=part, onset=0.0, duration=part.duration, number=1)
            end_time = pmscore.get_end_time()  # total duration of score
            end_beat = score.time_map.time_to_beat(end_time)
            # in principle we could do this once for the first staff and
            # then copy the created staff with measures for any other
            # staff, but then we would have to save off the notes and
            # write another loop to insert each note list to a corresponding
            # staff. Besides, _create_measures might even be faster than
            # calling deepcopy on a Staff to copy the measures.
            _create_measures(staff, score.time_map, end_beat, notes, pmscore)
            _add_notes_to_measures(notes, staff.content, pmscore.resolution)

    return score
