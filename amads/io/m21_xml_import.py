from music21 import (
    bar,
    chord,
    clef,
    converter,
    instrument,
    key,
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
        print(m21score.show("text"))

    # Create an empty Score object
    score = Score()

    # Iterate over parts in the music21 score
    for m21part in m21score.parts:
        if isinstance(m21part, stream.Part):
            # Convert the music21 part into an AMADS Part and append it to the Score
            music21_convert_part(m21part, score)
        else:
            print("Ignoring non-Part element:", m21part)

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
    duration = float(m21note.quarterLength)
    # print("music21_convert_note: m21note offset", m21note.offset,
    #       "float", float(m21note.offset))
    # print ("music21_convert_note: m21note duration",
    #        m21note.duration.quarterLength, "float",
    #        float(m21note.duration.quarterLength))
    # Handle rests if present
    # Create a new Note object and associate it with the Measure
    # print("music21_convert_note: m21note pitch", m21note.pitch, "beat",
    #       m21note.beat, "offset", m21note.offset, "measure onset", measure.onset,
    #       "measure offset", measure.offset)
    Note(
        parent=measure,
        onset=float(measure.onset + m21note.offset),
        pitch=Pitch(pitch=m21note.pitch.midi, alt=m21note.pitch.alter),
        duration=duration,
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
        Note(
            parent=chord,
            onset=float(measure.onset + m21chord.offset),
            pitch=Pitch(pitch=pitch.midi, alt=pitch.alter),
            duration=duration,
        )


def append_items_to_measure(measure: Measure, source: stream, offset: float) -> None:
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
        elif isinstance(element, meter.TimeSignature):
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
                print("music21 tempo mark is within existing time mmap, ignoring")
            else:
                bpm = element.getQuarterBPM()
                # music21 tempo mark may return None for BPM, so provide a default
                if bpm is None:
                    print("music21 tempo mark has no BPM, ignoring")
                else:
                    time_map.append_beat_tempo(tempo_change_onset, bpm)
        elif isinstance(element, bar.Barline):
            pass  # ignore barlines, e.g. Barline type="final"
        else:
            print("music21_convert_measure ignoring non-Note element:", element)


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
    # Create a new Part object and associate it with the Score
    part = Part(parent=score, instrument=m21part.partName)
    staff = Staff(parent=part)  # Assuming a single staff for simplicity

    # Iterate over elements in the music21 part
    for element in m21part.iter():
        if isinstance(element, stream.Measure):
            # Convert music21 Measure to our Measure class
            music21_convert_measure(element, staff)
        elif isinstance(element, instrument.Instrument):
            part.instrument = element.instrumentName
        else:
            print("music21_convert_part ignoring non-Measure element:", element)
