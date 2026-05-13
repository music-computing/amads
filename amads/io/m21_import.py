import warnings
from math import isclose
from pathlib import Path
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


class _TiedNotes:
    """Temporary data to track tied notes.

    This is a mapping from key number to Note object for notes that
    originate a tie. When we see a note that ends or continues a tie, we
    look up the origin of the tie in this dictionary and link it to the note
    that ends or continues the tie. Note that we do not encode 'let-ring' or
    'continue-let-ring' in the AMADS data model, so we ignore those cases.

    You might expect that if you encounter a tied note at a certain
    pitch, then the next note at that pitch would be the note that the tie
    connects to, but surprisingly, things are not so simple. As far as I
    can tell, the order of notes is pretty arbitrary, maybe because of
    voices, which are apparently created when notes are tied or beamed or
    have stems in opposite directions, or even when you have notes of
    different durations that overlap.

    In any case, it seems to be ambiguous how ties connect. (Music
    notation itself is ambiguous, e.g., does a tie from a chord to a chord
    tie all notes in the chords or just one?) When we get a "start" tie
    for pitch P, we set tied_notes[P] to the corresponding AMADS Note. If
    tied_notes[P] already exists, we convert it to a list and put the Note
    on the list. Then, when we find a note that continues or ends a tie,
    we search tied_notes[P] for the best match, noting that tied notes
    are not necessarily adjacent (n1.offset may not be exactly n2.onset).
    """

    tied_notes: Dict[int, Note | list[Note]]

    def __init__(self):
        self.tied_notes = {}

    def insert_start_note(self, key_num: int, note: Note) -> None:
        if key_num in self.tied_notes:
            tied_note = self.tied_notes[key_num]
            if isinstance(tied_note, list):
                tied_note.append(note)
            else:
                self.tied_notes[key_num] = [tied_note, note]
        else:
            self.tied_notes[key_num] = note

    def find_and_remove_predecessor(
        self, choices: list[Note], note: Note
    ) -> Note:
        """find closest thing to an immediate predecessor to note in choices"""
        # this will search for the note p in choices with an offset that is
        # closest to the onset of note, i.e., where p and note are adjacent:
        pred = min(choices, key=lambda p: abs(note.onset - p.offset))
        # now remove pred from tied_notes
        choices.remove(pred)
        return pred

    def continue_note(self, key_num: int, note: Note) -> None:
        if key_num in self.tied_notes:
            origin = self.tied_notes[key_num]
            if isinstance(origin, list):
                origin_note = self.find_and_remove_predecessor(origin, note)
                origin.append(note)  # this note is tied to something too
                origin = origin_note

            else:  # there is only one note that can be the predecessor.
                # since note is labeled "continue", it becomes a predecessor
                self.tied_notes[key_num] = note
            if abs(note.onset - origin.offset > 0.1):
                warnings.warn(
                    f"music21 note (key_num {key_num} at beat "
                    f"{note.onset} continues a tie but the best "
                    f"candidate for its predecessor (at beat "
                    f"{origin.onset} is not adjacent. It ends at "
                    f"beat {origin.offset}. Tying to it anyway."
                )
            origin.tie = note
        else:  # missing start note
            warnings.warn(
                f"music21 note (key_num {key_num} at beat"
                f" {note.onset}) continues a tie, but there is no"
                " start note for that pitch. The tie is ignored."
            )

    def stop_note(self, key_num: int, note: Note) -> None:
        if key_num in self.tied_notes:
            origin = self.tied_notes[key_num]
            if isinstance(origin, list):
                origin_note = self.find_and_remove_predecessor(origin, note)
                if len(origin) == 1:  # restore to non-list single note
                    self.tied_notes[key_num] = origin[0]
                origin = origin_note
            else:
                del self.tied_notes[key_num]  # remove the origin
            if abs(note.onset - origin.offset > 0.1):
                warnings.warn(
                    f"music21 note (key_num {key_num} at beat "
                    f"{note.onset} ends a tie but the best "
                    f"candidate for its predecessor (at beat "
                    f"{origin.onset} is not adjacent. It ends at "
                    f"beat {origin.offset}. Tying to it anyway."
                )
            origin.tie = note
        else:  # missing start note
            warnings.warn(
                f"music21 note (key_num {key_num} at beat"
                f" {note.onset}) ends a tie, but there is no start"
                " note for that pitch. The tie is ignored."
            )

    def has_open_ties(self) -> bool:
        return len(self.tied_notes) > 0

    def get_predecessors(self) -> list[Note]:
        """Get a list of all the predecessor notes that have not been matched
        with a note that continues or ends the tie.
        """
        preds = []
        for tied_note in self.tied_notes.values():
            if isinstance(tied_note, list):
                preds.extend(tied_note)
            else:
                preds.append(tied_note)
        return preds


def music21_import(
    filename: str | Path,
    format: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
) -> Score:
    """
    Use music21 to import a file and convert it to a Score.

    Parameters
    ----------
    filename : str
        The path to the music file.
    format: str
        The file format: 'musicxml', 'kern', 'mei'
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
    # Load the file using music21
    if format == "kern":
        format = "humdrum"  # music21 uses "humdrum" for kern files
    # other formats are the same for both AMADS and music21
    qp = format != "midi"  # quantize non-MIDI files until we discover this is
    # a bad idea. MIDI files may have expressive timing, so we never quantize.
    m21score = converter.parse(
        filename, format=format, forceSource=True, quantizePost=qp
    )

    # m21score can be an Opus, but this is checked in music21_to_score, so we
    # can ignore the type error here:
    score = music21_to_score(
        m21score,  # type: ignore
        flatten,
        collapse,
        show,  # type: ignore
        str(filename),
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
        shared_shift = None  # used to check all parts have same time shift
        for i, m21part in enumerate(m21score.parts):
            if isinstance(m21part, stream.Part):
                # Convert the music21 part into an AMADS Part and
                # append it to the Score:
                part, shift = music21_convert_part(m21part, score, duration)
                # check that all parts have the same time shift; this should
                # be true if all first measures have the same number of beats
                # either as notes or rest or some combination.
                if shared_shift is not None:
                    assert isclose(shared_shift, shift, abs_tol=0.001)
                else:
                    shared_shift = shift
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
    global tied_notes
    assert tied_notes is not None  # initialized in music21_convert_part
    print("music21_convert_tie type", tie_type, note)
    print("    tied_notes", repr(tied_notes))
    if tie_type == "start":
        # Start of a tie
        tied_notes.insert_start_note(key_num, note)
    elif tie_type == "continue":  # Continuation of a tie
        tied_notes.continue_note(key_num, note)
    elif tie_type == "stop":  # End of a tie
        tied_notes.stop_note(key_num, note)


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
    tied_notes = _TiedNotes()  # reset tied notes tracking for this part
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
    if tied_notes.has_open_ties():
        warnings.warn(
            f"music21_convert_part: tied notes in {part} from these"
            f" notes were not closed at the end of the part:"
            f" {tied_notes.get_predecessors()}"
        )
    tied_notes = None  # type: ignore , free memory used by tied notes tracking
    staff.offset = staff.content[-1].offset

    shift = 0  # how much did we shift to make a full measure 1?

    # expand first measure to a full measure if necessary
    # what is the maximum offset of the first measure?
    if len(staff.content) > 0:
        m1 = staff.content[0]
        m1 = cast(Measure, m1)
        max_offset = 0
        for elem in m1.content:
            max_offset = max(max_offset, elem.offset)
        if max_offset < m1.offset - 0.001:  # need to insert rest
            shift = m1.offset - max_offset
            for elem in m1.content:
                if (
                    isinstance(elem, Note)
                    or isinstance(elem, Rest)
                    or isinstance(elem, Chord)
                ):
                    elem.time_shift(shift)
            # insert Rest, Since m1 is first, m1.onset == 0
            _ = Rest(m1, m1.onset, duration=shift)

            # now, first measure ending may have shifted, so adjust
            # remainder of the part
            if len(staff.content) > 1:
                m2 = staff.content[1]
                m2 = cast(Measure, m2)
                shift = m1.offset - m2.onset
                if shift > 0.001:  # need to shift everything
                    for m in staff.content[1:]:
                        m.time_shift(shift)
            staff.offset = staff.content[-1].offset
            part.offset = max(part.offset, staff.offset)
            score.offset = max(score.duration, staff.offset)
    return part, shift
