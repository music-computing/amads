import warnings
from math import isclose
from typing import Optional, cast

from music21 import (
    chord,
    clef,
    instrument,
    key,
    layout,
    metadata,
    musicxml,
    note,
    stream,
    tempo,
    tie,
)
from music21.duration import Duration as m21Duration
from music21.meter.base import TimeSignature as m21TimeSignature

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


def fix_part_ids(musicxml_string):
    """Replace auto-generated part IDs with P1, P2, etc.

    The problem is that when I write PartStaff objects, Music21 generates
    unique IDs that are really ugly and not like other MusicXML files with,
    e.g., <part id="P1">, so this hack rewrites the XML with cleaner part
    names, as suggested by Claude after multiple attempts to set the ID's
    in the Music21 data structure.
    """
    import re

    # Find all unique part IDs
    part_ids = re.findall(
        r'<(?:score-)?part id="(P[a-f0-9]+)"', musicxml_string
    )
    unique_ids = list(dict.fromkeys(part_ids))  # Preserve order

    # Replace with simple IDs
    for i, old_id in enumerate(unique_ids, 1):
        musicxml_string = musicxml_string.replace(f'"{old_id}"', f'"P{i}"')

    return musicxml_string


def _add_measure_content(m21measure, measure, ties) -> None:
    """
    insert content (Notes, Chords, Rests) from a Measure to m21 measure

    This is complicated in that overlapping content must be separated
    out into voices.

    Parameters
    ----------
    m21measure: stream.measure
        The Music21 measure in which to add content

    measure: Measure
        The AMADS measure serving as a content source

    Returns
    -------
    float
        the maximum offset time of any

    """
    # see if there is any overlapping content
    need_voices = False
    for item, next_item in zip(measure.content, measure.content[1:]):
        if item.offset > next_item.onset + 1e-6:
            need_voices = True
            break
    if need_voices:  # collect voices - uses simple greedy algorithm
        # pick
        content = measure.content.copy()
        voices = []
        while len(content) > 0:
            print("need_voices, content:", content)
            # scan content, moving non-overlapping items into voice[].
            # overlapping items are saved at index i for the next voice(s)
            i = 0  # i is index of left-overs
            j = 0  # j is index to scan through content
            voice = []
            last_offset = 0
            for j in range(len(content)):
                if content[j].onset < last_offset - 1e-6:
                    content[i] = content[j]  # save for next voice(s)
                    i += 1
                else:
                    voice.append(content[j])
                    last_offset = content[j].offset
            # now, i is the length of overlapping items we want to keep
            del content[i:]
            voices.append(voice)
        print("voices:", voices)

        for voice_num, voice in enumerate(voices):
            m21voice = stream.Voice(id=str(voice_num + 1))
            _add_measure_content_from_list(
                m21voice, measure, voice, measure.offset, ties
            )
            m21measure.insert(0, m21voice)
    else:
        _add_measure_content_from_list(
            m21measure, measure, measure.content, measure.offset, ties
        )


def _add_measure_content_from_list(m21parent, measure, content, dur, ties):
    """
    insert content (Notes, Chords, Rests) from a Measure to m21 stream

    The m21 stream, called `m21parent`, can be a Music21 measure or voice.
    Voices are needed when content overlaps. `content` must be non-overlapping.
    m21parent is padded with a rest to achieve a duration of `dur`
    """
    print("_add_measure_content_from_list", content)
    max_offset = measure.onset
    measure_position = 0  # keeps track of expected next onset time
    for item in content:
        measure_delta = item.onset - measure.onset
        duration = item.duration
        max_offset = max(max_offset, item.offset)
        if (
            isinstance(item, Note)
            or isinstance(item, Rest)
            or isinstance(item, Chord)
        ) and (measure_delta > measure_position + 1e-6):
            print(
                "   Padding with rest: offset",
                measure_position,
                "duration",
                measure_delta - measure_position,
                "delta",
                measure_delta,
                "item",
                item,
            )
            m21rest = note.Rest()
            m21rest.offset = measure_position
            m21rest.duration.quarterLength = measure_delta - measure_position
            m21parent.insert(measure_position, m21rest)

        # measure_position is the place where the item after this one
        # is expected. It is used to determine on the next iteration if
        # we need to pad with a rest
        measure_position = measure_delta + duration

        print("   Inserting item:", item)
        # now that we've padded to measure_position with a rest if necessary,
        # insert the Note, Rest, or Chord from the score:
        if isinstance(item, Note):
            m21note = note.Note(nameWithOctave=item.name_with_octave)
            m21note.offset = measure_delta
            m21note.duration.quarterLength = duration
            if isinstance(item.dynamic, int):
                m21note.volume.velocity = item.dynamic
            # otherwise, use default because I am not sure how
            #     to translate anything other dynamic value.
            m21parent.insert(m21note.offset, m21note)
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
            m21parent.insert(m21rest.offset, m21rest)
        elif isinstance(item, Chord):
            pitches = [
                n.name_with_octave for n in item.find_all(Note)  # type: ignore
            ]
            m21chord = chord.Chord(pitches)
            m21chord.offset = measure_delta
            m21chord.duration.quarterLength = duration
            m21parent.insert(m21chord.offset, m21chord)

    if max_offset < measure.offset - 1e-6:
        # need a rest to fill out the measure in Music21,
        # otherwise, it will shorten the duration of the measure
        m21rest = note.Rest()
        # music21 offset is relative to measure:
        print("inserting rest", max_offset, measure.onset, measure.offset)
        m21rest.offset = max_offset - measure.onset
        print("  inserting rest, m21 offset", m21rest.offset)
        m21rest.duration.quarterLength = measure.offset - max_offset
        m21parent.insert(m21rest.offset, m21rest)


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

    # transfer tempo changes to music21
    for i, map_quarter in enumerate(score.time_map.changes):
        mm = score.time_map.get_tempo_at(i)
        m21score.insert(map_quarter.quarter, tempo.MetronomeMark(number=mm))

    ties = {}  # map from AMADS Note to (note.Note, tied_to)
    # where note.Note is the music21 note corresponding to the key or
    #     None if not processed yet, and tied_to is True if there is an
    #     incoming tie. (Outgoing ties can be detected by key.tie attribute)

    time_sigs = score.time_signatures
    for part_num, part in enumerate(score.find_all(Part)):
        part = cast(Part, part)
        part_id = f"P{part_num + 1}"
        staffs = part.list_all(Staff)
        make_staff_group = len(staffs) > 1
        m21staffs = []
        m21container = None  # make type checker happy
        for staff_num, staff in enumerate(staffs):
            if make_staff_group:
                id = f"P{part_num + 1}-Staff{staff_num + 1}"
                m21container = stream.PartStaff(id=id, partName=str(part_num))
                print("Setting part_id:", part_id)
                m21container.id = part_id
                m21container.groups.append(part_id)
                m21staffs.append(m21container)
                print("Is make_staff_group, id", id)
            else:
                m21container = stream.Part(id=part_id)

            if part.instrument:
                try:
                    instr = instrument.fromString(part.instrument)
                except Exception as e:
                    warnings.warn(
                        f"Could not create instrument {part.instrument}: {e}"
                    )
                    instr = instrument.Instrument()
                    instr.instrumentName = part.instrument
                m21container.insert(0, instr)
            staff = cast(Staff, staff)
            time_sig_index = 0
            time_sig = time_sigs[time_sig_index]
            for index, measure in enumerate(staff.find_all(Measure)):
                measure = cast(Measure, measure)
                num = measure.number if measure.number else (index + 1)
                m21measure = stream.Measure(
                    number=num, duration=m21Duration(measure.duration)
                )
                # add time signature change if any
                if isclose(time_sig.time, measure.onset, abs_tol=1e-3):
                    if time_sig.upper != round(time_sig.upper):
                        raise ValueError(
                            "Cannot export fractional time"
                            f" signature {time_sig} to Music21."
                        )
                    ts_element = m21TimeSignature(
                        f"{round(time_sig.upper)}/{time_sig.lower}"
                    )
                    m21measure.insert(time_sig.time - measure.onset, ts_element)
                    # move to the next time_sig, if any left. If not, we do
                    # not change time_sig, but since subsequent measures have
                    # greater onset times, we won't try to add another time_sig
                    time_sig_index += 1
                    if time_sig_index < len(time_sigs):
                        time_sig = time_sigs[time_sig_index]
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
                _add_measure_content(m21measure, measure, ties)
                m21container.append(m21measure)
            if time_sig_index != len(time_sigs):
                warnings.warn(
                    f"After converting AMADS staff {staff} to"
                    " Music21, there are left-over, unused time"
                    f" signatures, starting with {time_sig}."
                )
        # make a layout.StaffGroup to group the staffs if needed
        if make_staff_group:
            for m21staff in m21staffs:
                m21staff._idLastDeepCopyOf = part_id
                m21score.insert(0, m21staff)  # insert each staff
            staff_group = layout.StaffGroup(m21staffs, id=part_id)
            staff_group._idLastDeepCopyOf = part_id  # type: ignore
            m21score.insert(0, staff_group)  # this groups staffs into part
            # this makes no sense, but it works to give the "part" an id,
            # as suggested by Claude
            m21staffs[0].id = part_id
        else:
            print("not make_staff_group, container", m21container)
            m21score.insert(0, m21container)  # staff info is in an m21 Part

    # fix up ties
    for amads_note in ties.keys():
        # amads_note.tie points to the next note in the tie (or None if no
        # outgoing tie) is_tied_to indicates if there's an incoming tie
        # from a previous note
        (m21note, is_tied_to) = ties[amads_note]

        if m21note is None:  # note was tied to but we never put the tied-to
            # note into the m21score!
            warnings.warn(
                "In score_to_music21: tied-to note not found:"
                f" {amads_note.tie}"
            )
        elif amads_note.tie and not is_tied_to:
            # Note is tied to the next note, but not tied from a previous note
            m21note.tie = tie.Tie("start")
        elif amads_note.tie and is_tied_to:
            # Note is tied to the next note AND tied from a previous note
            m21note.tie = tie.Tie("continue")
        elif not amads_note.tie and is_tied_to:
            # Note is not tied to the next note, but is tied from a prev. note
            m21note.tie = tie.Tie("stop")
        elif not amads_note.tie and not is_tied_to:
            # No tie at all - don't set tie attribute
            pass
        else:
            assert (
                False
            ), f"Internal tie-fix-up error {amads_note}, {ties[amads_note]}"

    if show:
        music21_show(m21score, filename)  # type: ignore

    return m21score


def music21_xml_export(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Save a Score to a file in musicxml format using music21.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the MusicXML data.
    show : bool, optional
        If True, print the music21 score structure for debugging.

    """
    m21score = score_to_music21(score, show, filename)

    # Export as text and fix part id's
    exporter = musicxml.m21ToXml.GeneralObjectExporter(m21score)
    musicxml_bytes = exporter.parse()
    musicxml_str = musicxml_bytes.decode("utf-8")
    fixed_xml = fix_part_ids(musicxml_str)

    # Finally, write the file
    with open(filename, "w") as f:
        f.write(fixed_xml)
