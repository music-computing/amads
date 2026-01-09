import warnings
from typing import Optional, cast

from music21 import chord, clef, instrument, key, metadata, note, stream, tie
from music21.meter import TimeSignature as m21TimeSignature

from amads.core.basics import (
    Chord,
    Clef,
    KeySignature,
    Measure,
    Note,
    Part,
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


def _m21_clef(clef_str: str) -> clef.Clef:
    """translate AMADS clef ID string to music21 Clef object"""
    if clef_str == "treble":
        return clef.TrebleClef()  # type: ignore
    if clef_str == "bass":
        return clef.BassClef()  # type: ignore
    if clef_str == "alto":
        return clef.AltoClef()  # type: ignore
    if clef_str == "tenor":
        return clef.TenorClef()  # type: ignore
    if clef_str == "percussion":
        return clef.PercussionClef()  # type: ignore
    if clef_str == "treble8vb":
        return clef.Treble8vbClef()  # type: ignore
    raise ValueError(f"Unknown clef string: {clef_str}")


def score_to_music21(
    score: Score, show: bool = False, filename: Optional[str] = None
) -> stream.Score:
    """
    Convert a Score to music21

    Parameters
    ----------
    score: Score
        The Score to convert
    show : bool, optional
        If True, print the music21 score structure for debugging.
    filename : Optional[str]
        If `show` and not None, `filename` is shown

    Returns
    -------
    stream.Score
        The AMADS Score object converted to music21
    """
    # create a new music21 score
    m21score = stream.Score()
    m21score.metadata = metadata.Metadata()
    if score.has("title"):
        m21score.metadata.title = score.get("title")
    if score.has("composer"):
        m21score.metadata.composer = score.get("composer")

    ties = {}  # map from AMADS Note to (note.Note, tied_to)
    # where note.Note is the music21 note corresponding to the key or
    #     None if not processed yet, and tied_to is True if there is an
    #     incoming tie. (Outgoing ties can be detected by key.tie attribute)

    for part in score.find_all(Part):
        part = cast(Part, part)
        m21part = stream.Part()
        if part.instrument:
            try:
                instr = instrument.fromString(part.instrument)
            except Exception as e:
                warnings.warn(
                    f"Could not create instrument {part.instrument}: {e}"
                )
                instr = instrument.Instrument()
            m21part.insert(0, instr)
        for staff in part.find_all(Staff):
            staff = cast(Staff, staff)
            for measure in staff.find_all(Measure):
                measure = cast(Measure, measure)
                num = measure.number if measure.number else 0
                m21measure = stream.Measure(number=num)
                # add time signature changes
                for ts in measure.find_all(TimeSignature):
                    ts = cast(TimeSignature, ts)
                    ts_element = m21TimeSignature(f"{ts.upper}/{ts.lower}")
                    m21measure.insert(ts.onset - measure.onset, ts_element)
                # add key signature changes
                for ks in measure.find_all(KeySignature):
                    ks = cast(KeySignature, ks)
                    ks_element = key.KeySignature(ks.key_sig)
                    m21measure.insert(ks.onset - measure.onset, ks_element)
                # add clef changes
                for clef_change in measure.find_all(Clef):
                    clef_change = cast(Clef, clef_change)
                    try:
                        clef_element = _m21_clef(clef_change.clef)
                    except ValueError as e:
                        warnings.warn(str(e))
                        continue
                    m21measure.insert(
                        clef_change.onset - measure.onset, clef_element
                    )
                # add notes, rests, chords
                for item in measure.content:
                    measure_delta = item.onset - measure.onset
                    duration = item.duration
                    if isinstance(item, Note):
                        m21note = note.Note(
                            nameWithOctave=item.name_with_octave
                        )
                        m21note.offset = measure_delta
                        m21note.duration.quarterLength = duration
                        if isinstance(item.dynamic, int):
                            m21note.volume.velocity = item.dynamic
                        # otherwise, use default because I am not sure how
                        #     to translate anything other dynamic value.
                        m21measure.insert(m21note.offset, m21note)
                        # if note is tied or tied to, enter it in ties:
                        if item.tie:  # item is tied to item.tie
                            is_tied_to = (item in ties) and ties[item][1]
                            ties[item] = (m21note, is_tied_to)
                            # set ties[item.tie]'s is_tied_to field to True
                            tied_to_m21 = None
                            if item.tie in ties:
                                tied_to_m21 = ties[item.tie][0]
                            ties[item.tie] = (tied_to_m21, True)
                        if (item in ties) and (ties[item][0] is None):
                            # update entry with m21note
                            ties[item] = (m21note, ties[item][1])

                    elif isinstance(item, Rest):
                        m21rest = note.Rest()
                        m21rest.offset = measure_delta
                        m21rest.duration.quarterLength = duration
                        m21measure.insert(m21rest.offset, m21rest)
                    elif isinstance(item, Chord):
                        pitches = [
                            n.name_with_octave  # type: ignore
                            for n in item.find_all(Note)
                        ]
                        m21chord = chord.Chord(pitches)
                        m21chord.offset = measure_delta
                        m21chord.duration.quarterLength = duration
                        m21measure.insert(m21chord.offset, m21chord)
                m21part.append(m21measure)
        m21score.append(m21part)

    # fix up ties
    for amad_note in ties.keys():
        # note is either 'start', 'stop' or 'continue'
        (m21note, is_tied_to) = ties[amad_note]

        if m21note is None:  # note was tied to but we never put the tied-to
            # note into the m21score!
            warnings.warn(
                "In score_to_music21: tied-to note not found:"
                f" {amad_note.tie}"
            )
        elif amad_note.tie and not is_tied_to:
            m21note.tie = tie.Tie("start")
        elif amad_note.tie and is_tied_to:
            m21note.tie = tie.Tie("continue")
        elif not amad_note.tie and is_tied_to:
            m21note.tie = tie.Tie("stop")
        else:  # not amad_note.tie and not is_tied_to
            assert (
                False
            ), f"Internal tie-fix-up error {amad_note}, {ties[amad_note]}"

    if show:
        # Print the music21 score structure for debugging
        print("Music21 score structure", end="")
        if filename is not None:
            print(f" for {filename}:")
        else:
            print(":")
        for element in m21score:
            if isinstance(element, metadata.Metadata):
                print(element.all())
        print(m21score.show("text", addEndTimes=True))

    return m21score


def music21_xml_export(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Save a Score to a file in musicxml format using music21.

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the MusicXML data.
    show : bool, optional
        If True, print the music21 score structure for debugging.

    <small>**Author**: Roger B. Dannenberg</small>
    """
    m21score = score_to_music21(score, show)
    m21score.write("musicxml", filename)
