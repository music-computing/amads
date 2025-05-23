import warnings

from music21 import (
    bar,
    chord,
    clef,
    converter,
    instrument,
    key,
    metadata,
    meter,
    note,
    stream,
    tempo,
)

from ..core.basics import (
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


def music21_xml_import(filename: str, show: bool = False) -> Score:
    """
    Use music21 to import a MusicXML file and convert it to a Score.

    Parameters
    ----------
    filename : str
        The path to the MusicXML file.
    show : bool, optional
        If True, print the music21 score structure for debugging.

    Returns
    -------
    Score
        The converted AMADS Score object.
    """
    # Load the MusicXML file using music21
    m21score = converter.parse(filename, format="xml")

    if show:
        # Print the music21 score structure for debugging
        print(f"Music21 score structure from {filename}:")
        for element in m21score:
            if isinstance(element, metadata.Metadata):
                print(element.all())
        print(m21score.show("text", addEndTimes=True))

    # Create an empty Score object
    score = Score()

    # Iterate over parts in the music21 score
    for m21part in m21score.parts:
        if isinstance(m21part, stream.base.Part):
            # Convert the music21 part into an AMADS Part and append it to the Score
            music21_convert_part(m21part, score)
        else:
            warnings.warn(f"Ignoring non-Part element of Music21 score: {m21part}")

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
    # print("music21_convert_note: m21note offset", m21note.offset,
    #       "float", float(m21note.offset))
    print(
        "music21_convert_note: m21note duration",
        m21note.duration.quarterLength,
        "float",
        float(m21note.duration.quarterLength),
    )
    # Handle rests if present
    # Create a new Note object and associate it with the Measure
    # print("music21_convert_note: m21note pitch", m21note.pitch, "beat",
    #       m21note.beat, "offset", m21note.offset, "measure onset", measure.onset,
    #       "measure offset", measure.offset)
    # if m21note.tie:
    #     print(f"music21_convert_note: tie: {m21note},",
    #           f"time: {measure.onset + m21note.offset},",
    #           f"dur: {m21note.quarterLength}, tie type: {m21note.tie.type}")
    if m21note.pitch.midi == 68:
        print(
            "music21_convert_note: m21note pitch",
            m21note.pitch,
            "beat",
            m21note.beat,
            "offset",
            m21note.offset,
            "measure onset",
            measure.onset,
            "measure offset",
            measure.offset,
        )
        pass
    note = Note(
        parent=measure,
        onset=float(measure.onset + m21note.offset),
        pitch=Pitch(pitch=m21note.pitch.midi, alt=m21note.pitch.alter),
        duration=duration,
    )
    print("music21_convert_note created", note)
    if m21note.tie is not None:
        music21_convert_tie(m21note.pitch.midi, note, m21note.tie.type)


def music21_convert_tie(key_num, note, tie_type) -> None:
    """Handle tie to and/or from music21 note

    Parameters
    ----------
    m21note
        a music 21 note
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
            # print("music21_convert_note: tie continue:", origin, "to", note)
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
            # print("music21_convert_note: tie stop:", origin, "to", note)
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
    Rest(parent=measure, onset=float(measure.onset + m21rest.offset), duration=duration)


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
        parent=measure, onset=float(measure.onset + m21chord.offset), duration=duration
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


def append_items_to_measure(
    measure: Measure, source: stream.base.Stream, offset: float
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
        elif isinstance(element, meter.base.TimeSignature):
            # Create a TimeSignature object and associate it with the Measure
            TimeSignature(
                parent=measure, upper=element.numerator, lower=element.denominator
            )
        elif isinstance(element, key.KeySignature):
            # Create a KeySignature object and associate it with the Measure
            KeySignature(parent=measure, key_sig=element.sharps)
        elif isinstance(element, clef.Clef):
            # Create a Clef object and associate it with the Measure
            Clef(parent=measure, clef=element.name)
        elif isinstance(element, chord.Chord):
            music21_convert_chord(element, measure, offset)
        elif isinstance(element, stream.Voice):
            # Voice containers are ignored, so promote contents to the Measure
            append_items_to_measure(measure, element, offset + element.offset)
        elif isinstance(element, tempo.MetronomeMark):
            # update tempo
            time_map = measure.score.time_map
            last_beat = time_map.beats[-1].beat
            tempo_change_onset = offset + element.offset
            if last_beat > tempo_change_onset:
                warnings.warn(
                    f"music21 tempo mark at {tempo_change_onset}"
                    " is within existing time mmap, ignoring"
                )
            else:
                bpm = element.getQuarterBPM()
                # music21 tempo mark may return None for BPM, so provide a default
                if bpm is None:
                    warnings.warn(
                        f"Music21 tempo mark at {tempo_change_onset}"
                        " has no BPM, ignoring"
                    )
                else:
                    # print("music21 MetronomeMark: tempo_change_onset",
                    #      tempo_change_onset, "bpm", bpm)
                    time_map.append_beat_tempo(tempo_change_onset, bpm)
        elif isinstance(element, bar.Barline):
            pass  # ignore barlines, e.g. Barline type="final"
        else:
            warnings.warn(
                "Music21_convert_measure ignoring non-Note element" f" {element}."
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


def music21_convert_part(m21part, score):
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
    part = Part(parent=score, instrument=m21part.partName)
    staff = Staff(parent=part)  # Assuming a single staff for simplicity
    tied_notes.clear()
    # Iterate over elements in the music21 part
    for element in m21part.iter():
        if isinstance(element, stream.Measure):
            # Convert music21 Measure to our Measure class
            music21_convert_measure(element, staff)
        elif isinstance(element, instrument.Instrument):
            part.instrument = element.instrumentName
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
