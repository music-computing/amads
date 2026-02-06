import warnings
from math import isclose
from typing import Dict, Optional, Tuple, Union, cast

from music21 import (
    bar,
    chord,
    clef,
    converter,
    instrument,
    key,
    note,
    stream,
    tempo,
)
from music21.meter.base import TimeSignature as m21TimeSignature

from amads.core.basics import (
    Chord,
    Clef,
    KeySignature,
    Measure,
    Note,
    Part,
    Pitch,
    Rest,
    Score,
    Staff,
    TimeSignature,
)
from amads.io.m21_show import music21_show

tied_notes = {}  # temporary data to track tied notes, this is a mapping
# from key number to Note object for notes that originate a tie. When we
# see a note that ends or continues a tie, we look up the origin of the
# tie in this dictionary and link it to the note that ends or continues
# the tie. Note that we do not encode 'let-ring' or 'continue-let-ring'
# in the AMADS data model, so we ignore those cases.
#     It is possible for notes to overlap in time and be tied. What ties
# to what in Music21 (as well as MIDI files) is ambiguous in this case,
# but ignoring overlapping ties would create multiple notes when there
# was only one in the MIDI file, so when there is overlap, we map from
# pitch to a list of notes that originate unterminated ties for this
# pitch. When a tie is terminated, we tie from the first note in the
# list. (First-in-first-out).


def music21_xml_import(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
) -> Score:
    """
    Use music21 to import a MusicXML file and convert it to a Score.

    Parameters
    ----------
    filename : str
        The path to the MusicXML file.
    flatten : bool, optional
        If True, flatten the score structure.
    collapse : bool, optional
        If True and flatten is true, also collapse parts.
    show : bool, optional
        If True, print the music21 score structure for debugging.
    group_by_instrument : bool, optional
        If True, group parts by instrument name into staffs. Defaults to True.
        See music21_to_score() for more details.

    Returns
    -------
    Score
        The converted AMADS Score object.
    """
    # Load the MusicXML file using music21
    m21score = converter.parse(filename, format="xml")

    # m21score can be an Opus, but this is checked in music21_to_score, so we
    # can ignore the type error here:
    score = music21_to_score(
        m21score,
        flatten,
        collapse,
        show,  # type: ignore
        group_by_instrument=group_by_instrument,
    )
    return score


# mapping from PartStaff id to list of AMADS Part, where each Part contains
# a Staff. After everything is read, Parts with the same id should be
# combined.
_staff_id_to_part: Dict[str, Tuple[stream.PartStaff, Part]]  # declare global


def music21_to_score(
    m21score: Union[stream.Score, stream.Part],
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    filename: Optional[str] = None,
    group_by_instrument: bool = True,
) -> Score:
    global _staff_id_to_part
    _staff_id_to_part = {}

    if show:
        music21_show(m21score, filename)  # type: ignore

    # Create an empty Score object
    duration = m21score.duration.quarterLength
    score = Score(duration=float(duration))

    parts: list[Part | None] = []  # All the Parts in score
    m21parts: list[stream.Part] = []  # Corresponding m21 parts
    group_ids: list[int] = []  # list of group identifiers
    next_group_id = 0  # groups are named by small integers
    if isinstance(m21score, stream.Score):
        group_ids = [-1] * len(m21score.parts)

    # Iterate over parts in the music21 score

    # We start with separate Part with Staff for each original part or staff.
    # We also have three lists that are "parallel" with Parts:
    # parts[i] is a list of all the Parts in order
    # m21parts[i] is the list of m21 parts corresponding to parts[i]
    # group_ids[i] is the group that the ith Part belongs to, so we can search
    #     to find all Parts whose Staff belong together.

    if isinstance(m21score, stream.Part):
        music21_convert_part(m21score, score, duration)
    elif isinstance(m21score, stream.Score):
        for i, m21part in enumerate(m21score.parts):
            if isinstance(m21part, stream.Part):
                # Convert the music21 part into an AMADS Part and
                # append it to the Score:
                part = music21_convert_part(m21part, score, duration)
                parts.append(part)
                m21parts.append(m21part)
                # if m21part is a PartStaff (subclass of Part), keep
                # a dictionary of names and Parts:
                if isinstance(m21part, stream.PartStaff):
                    next_group_id += 1
                    group_id = next_group_id
                    spanners = m21part.getSpannerSites()
                    for spanner in spanners:
                        if spanner.__class__.__name__ == "StaffGroup":
                            for elem in spanner.getSpannedElements():
                                if isinstance(elem, stream.PartStaff):
                                    assert elem in m21parts
                                    j = m21parts.index(elem)
                                    group_ids[j] = group_id
                                    break  # only one PartStaff spanner
            else:
                warnings.warn(
                    f"Ignoring non-Part element of Music21 score: {m21part}"
                )
    else:
        raise ValueError("expected Score or Part from music21 reader")

    # If group_by_instrument, we form groups by looking for matching
    # instruments:
    if group_by_instrument:
        instruments = []
        for i in range(len(parts)):
            try:
                # later, parts[i] can be None, so type checker complains here:
                j = instruments.index(parts[i].instrument)  # type: ignore
            except ValueError:
                instruments.append(parts[i].instrument)  # type: ignore
                continue
            instruments.append(parts[i].instrument)  # type: ignore
            if group_ids[i] == -1:  # part j is not in a group
                if group_ids[j] == -1:  # neither is i, so make a new group
                    next_group_id += 1
                    group_ids[j] = next_group_id
                    group_ids[i] = next_group_id
                    next_group_id += 1
                else:  # j is in a group, so assign that to i
                    group_ids[i] = group_ids[j]
            # else both i and j are in groups already, must be from MusicXML
            # staff grouping; probably correct already, so do no merge them

    # Now, grouping is complete.
    # To process Parts, for each i, see if group_ids[i] is not None. If not,
    # find all other Parts with matching group_id and merge them. As you do it,
    # remove the other Parts from the score.

    for i in range(len(parts)):
        to_part = cast(Part, parts[i])
        if group_ids[i] != -1:
            # find all other parts with matching group_ids[j]:
            group_id = group_ids[i]
            j = i
            while True:
                group_ids[j] = -1  # so j will not match
                try:
                    j = group_ids.index(group_id)
                except ValueError:  # no match, nothing else in group
                    break  # no more staffs to merge
                from_part = cast(Part, parts[j])
                parts[j] = None  # soon this part will be gone
                if to_part.instrument is None:
                    to_part.instrument = from_part.instrument
                score.remove(from_part)
                from_staff = cast(Staff, from_part.content[0])
                from_part.remove(from_staff)
                to_part.insert(from_staff)

    if flatten or collapse:
        score = score.flatten(collapse=collapse)
    return score


def music21_convert_note(m21note, measure):
    """
    Convert a music21 note into an AMADS Note and append it to the Measure.

    Parameters
    ----------
    m21note : music21.note.Note
        The music21 note to convert.
    measure : Measure
        The Measure object to which the converted Note will be appended.
    """
    duration = float(m21note.duration.quarterLength)
    dynamic = m21note.volume.velocity
    if isinstance(dynamic, int):
        dynamic = min(max(dynamic, 1), 127)
    note = Note(
        parent=measure,
        onset=float(measure.onset + m21note.offset),
        pitch=Pitch(pitch=m21note.pitch.midi, alt=m21note.pitch.alter),
        duration=duration,
        dynamic=dynamic,
    )
    if m21note.tie is not None:
        music21_convert_tie(m21note.pitch.midi, note, m21note.tie.type)


def music21_convert_tie(key_num: int, note: Note, tie_type: str) -> None:
    """Handle tie to and/or from music21 note

    Parameters
    ----------
    key_num: int
        the MIDI key number (pitch)
    note : Note
        the note we are creating, corresponds to m21note
    tie_type : str
        the tie type, one of "start", "continue", "stop"
    """
    if tie_type == "start":
        # Start of a tie
        if key_num in tied_notes:
            # If the note is already tied, we should not see "start":
            import warnings

            warnings.warn(
                f"music21 note (key_num {key_num} at beat"
                f" {note.onset}) starts a tie, but there is already"
                " an open tie for that pitch. Maybe MIDI file has"
                " multiple note-on events without an intervening"
                " note-off event."
            )
            # make a list of started ties
            tied_note = tied_notes[key_num]
            if isinstance(tied_note, list):
                tied_note.append(note)
            else:
                tied_notes[key_num] = [tied_note, note]
        else:
            tied_notes[key_num] = note
    elif tie_type == "continue":  # Continuation of a tie
        if key_num in tied_notes:
            origin = tied_notes[key_num]
            if isinstance(origin, list):
                origin_note = origin.pop(0)
                origin_note.tie = note
                origin.append(note)  # this note is tied to something too
                origin = origin_note
            else:
                tied_notes[key_num] = note  # to be continued :-)
            origin.tie = note
        else:  # missing start note
            import warnings

            warnings.warn(
                f"music21 note (key_num {key_num} at beat"
                f" {note.onset}) continues a tie, but there is no"
                " start note for that pitch."
            )
    elif tie_type == "stop":  # End of a tie
        if key_num in tied_notes:
            origin = tied_notes[key_num]
            if isinstance(origin, list):
                origin_note = origin.pop(0)
                if len(origin) == 1:  # restore to non-list single note
                    tied_notes[key_num] = origin[0]
                origin = origin_note
            else:
                del tied_notes[key_num]  # remove the origin
            origin.tie = note
        else:  # missing start note
            import warnings

            warnings.warn(
                f"music21 note (key_num {key_num} at beat"
                f" {note.onset}) ends a tie, but there is no start"
                " note for that pitch."
            )


def music21_convert_rest(m21rest, measure):
    """
    Convert a music21 rest into an AMADS Rest and append it to the Measure.

    Parameters
    ----------
    m21rest : music21.note.Rest
        The music21 rest to convert.
    measure : Measure
        The Measure object to which the converted Rest will be appended.
    """
    duration = float(m21rest.quarterLength)
    # Create a new Rest object and associate it with the Measure
    Rest(
        parent=measure,
        onset=float(measure.onset + m21rest.offset),
        duration=duration,
    )


def music21_convert_chord(m21chord, measure, offset):
    """
    Convert a music21 chord into an AMADS Chord and append it to the Measure.
    Apparently, chord notes cannot be tied, so we ignore ties.

    Parameters
    ----------
    m21chord : music21.chord.Chord
        The music21 chord to convert.
    measure : Measure
        The Measure object to which the converted Chord will be appended.
    """
    duration = float(m21chord.quarterLength)
    chord = Chord(
        parent=measure,
        onset=float(measure.onset + m21chord.offset),
        duration=duration,
    )
    for pitch in m21chord.pitches:
        note = Note(
            parent=chord,
            onset=float(measure.onset + m21chord.offset),
            pitch=Pitch(pitch=pitch.midi, alt=pitch.alter),
            duration=duration,
        )
        if m21chord.tie is not None:
            music21_convert_tie(pitch.midi, note, m21chord.tie.type)


def update_part_instrument(caller_id, part, m21instr):
    assert part is not None
    name = m21instr.partName
    name = None if name == "Unknown" else name
    if part.instrument is None:
        part.instrument = name
    elif name != part.instrument:
        warnings.warn(
            f"Music21_convert_measure ignoring {m21instr.__class__}"
            f" ({m21instr}) because part already has different"
            f" instrument {part.instrument}."
        )
        part_program = part.get("midi_program")
        measure_program = m21instr.midiProgram
        if part_program is None:
            part.set("midi_program", measure_program)
        elif part_program != measure_program:
            warnings.warn(
                f"music21.instrument midi_program conflict: {m21instr},"
                " program change ignored)"
            )


def _remove_clef_from_measure(measure: Measure, onset: float) -> None:
    """Removes Clefs near onset time in measure."""
    to_remove = [
        elem
        for elem in measure.content
        if (
            isinstance(elem, Clef) and isclose(elem.onset, onset, abs_tol=0.001)
        )
    ]
    for elem in to_remove:
        measure.remove(elem)


def append_items_to_measure(
    measure: Measure, source: stream.Stream, offset: float
) -> None:
    """
    Append items from a source to the Measure.

    Parameters
    ----------
    measure : Measure
        The Measure object to which items will be appended.
    source : music21.stream.Stream
        The source stream containing items to append.
    """
    for element in source.iter():
        if isinstance(element, note.Note):
            music21_convert_note(element, measure)
        elif isinstance(element, note.Rest):
            music21_convert_rest(element, measure)
        elif isinstance(element, m21TimeSignature):
            # Create a TimeSignature object and insert into the score
            # if the TimeSignature changes at this time:
            upper = element.numerator
            lower = element.denominator
            if abs(element.offset) > 1e-3:
                warnings.warn(
                    "Music21 time signature found that is not at the"
                    f" measure beginning: {element}. Moving the"
                    " signature to the beginning of the measure."
                )
            # what TimeSignature is in effect?
            ts = measure.time_signature()
            if ts.upper != upper or ts.lower != lower:
                last_ts = measure.score.time_signatures[-1]  # type: ignore
                if last_ts.time > measure.onset:
                    warnings.warn(
                        "Encountered a new Music21 time signature"
                        " placed BEFORE an earlier time signature:"
                        " {element}. Something is probably wrong"
                        " with this score. Ignoring the time"
                        " signature in conversion to AMADS."
                    )
                else:
                    ts = TimeSignature(measure.onset, upper, lower)
                    measure.score.append_time_signature(ts)  # type: ignore
        elif isinstance(element, key.KeySignature):
            # Create a KeySignature object and associate it with the Measure
            KeySignature(
                measure, measure.onset + element.offset, key_sig=element.sharps
            )
        elif isinstance(element, clef.Clef):
            # Partitura will write Clef for staff 1 without a number attribute
            # in MusicXML, and if there is a <clef> and a <clef number="2">,
            # Music21 apparently puts *both* into staff 2. To prevent this,
            # we will remove any Clef appearing at the same time in the same
            # measure
            _remove_clef_from_measure(measure, measure.onset + element.offset)
            # Create a Clef object and associate it with the Measure
            Clef(measure, measure.onset + element.offset, clef=element.name)
        elif isinstance(element, chord.Chord):
            music21_convert_chord(element, measure, offset)
        elif isinstance(element, stream.Voice):
            # Voice containers are ignored, so promote contents to the Measure
            append_items_to_measure(measure, element, offset + element.offset)
        elif isinstance(element, tempo.MetronomeMark):
            # update tempo
            time_map = measure.score.time_map  # type: ignore (measure has
            #     a parent)
            last_beat = time_map.changes[-1].quarter
            tempo_change_onset = offset + element.offset
            if last_beat > tempo_change_onset:
                warnings.warn(
                    f"music21 tempo mark at {tempo_change_onset}"
                    " is within existing time mmap, ignoring"
                )
            else:
                qpm = element.getQuarterBPM()
                # ignore music21 tempo mark if it returns None for BPM
                if qpm is None:
                    warnings.warn(
                        f"Music21 tempo mark at {tempo_change_onset}"
                        " has no BPM, ignoring"
                    )
                else:
                    time_map.append_change(tempo_change_onset, qpm)
        elif isinstance(element, bar.Barline):
            pass  # ignore barlines, e.g. Barline type="final"
        elif isinstance(element, instrument.Instrument):
            part = measure.part
            update_part_instrument("FOUND INSTRUMENT IN MEASURE", part, element)
        else:
            warnings.warn(
                "Music21_convert_measure ignoring non-Note element"
                f" {element} : {element.__class__}."
            )


def music21_convert_measure(m21measure, staff):
    """
    Convert a music21 measure into an AMADS Measure and append it to the Staff.

    Parameters
    ----------
    m21measure : music21.stream.Measure
        The music21 measure to convert.
    staff : Staff
        The Staff object to which the converted Measure will be appended.
    """
    # Create a new Measure object and associate it with the Staff
    measure = Measure(
        parent=staff,
        onset=m21measure.offset,
        duration=float(m21measure.barDuration.quarterLength),
    )

    # Iterate over elements in the music21 measure
    append_items_to_measure(measure, m21measure, m21measure.offset)
    return measure


def music21_convert_part(m21part, score, duration):
    """
    Convert a music21 part into an AMADS Part and append it to the Score.

    Parameters
    ----------
    m21part : music21.stream.Part
        The music21 part to convert.
    score : Score
        The Score object to which the converted Part will be appended.
    """
    global tied_notes  # temporary data to track tied notes
    # Create a new Part object and associate it with the Score
    name = m21part.partName
    if name == "Unknown":  # AMADS uses "Unknown" to represent None.
        # Of course, if a user really names an instrument "Unknown",
        # that particular name will not be stored in the Part.
        name = None
    part = Part(parent=score, instrument=name, duration=duration)
    staff = Staff(parent=part)  # Assuming a single staff for simplicity
    tied_notes.clear()
    # Iterate over elements in the music21 part
    for element in m21part.iter():
        if isinstance(element, stream.Measure):
            # Convert music21 Measure to our Measure class
            music21_convert_measure(element, staff)
        elif isinstance(element, instrument.Instrument):
            update_part_instrument("FOUND INSTRUMENT IN PART", part, element)
        else:
            warnings.warn(
                f"music21_convert_part ignoring non-Measure element: {element}"
            )
    if len(tied_notes.keys()) > 0:
        warnings.warn(
            f"music21_convert_part: tied notes in {part} from these"
            f" notes were not closed at the end of the part:"
            f" {tied_notes.values()}"
        )
    tied_notes.clear()

    # expand first measure to a full measure if necessary
    # what is the maximum offset of the first measure?
    if len(staff.content) > 0:
        m1 = staff.content[0]
        m1 = cast(Measure, m1)
        max_offset = 0
        for elem in m1.content:
            max_offset = max(max_offset, elem.offset)
        if max_offset < m1.offset - 0.001:  # need to insert rest
            gap = m1.offset - max_offset
            for elem in m1.content:
                if (
                    isinstance(elem, Note)
                    or isinstance(elem, Rest)
                    or isinstance(elem, Chord)
                ):
                    elem.time_shift(gap)
            # insert Rest, Since m1 is first, m1.onset == 0
            _ = Rest(m1, m1.onset, duration=gap)

    return part
