import warnings
from math import isclose
from pathlib import Path
from typing import Optional, cast

from music21 import (
    chord,
    clef,
    expressions,
    instrument,
    key,
    layout,
    metadata,
    musicxml,
    note,
    pitch,
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
    Pitch,
    Rest,
    Score,
    Staff,
)
from amads.io.m21_show import music21_show
from amads.io.pm_midi_export import _get_midi_time_signatures

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


def _m21_clef(clef_str: str, aclef: Clef) -> clef.Clef:
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
    if clef_str == "treble8va":
        return clef.Treble8vaClef()  # type: ignore
    if clef_str == "treble8vb":
        return clef.Treble8vbClef()  # type: ignore
    if clef_str == "bass8va":
        return clef.Bass8vaClef()  # type: ignore
    if clef_str == "bass8vb":
        return clef.Bass8vbClef()  # type: ignore
    if clef_str == "bass8va":
        return clef.Bass8vaClef()  # type: ignore
    if clef_str == "soprano":
        return clef.SopranoClef()  # type: ignore
    if clef_str == "cbaritone":
        return clef.CBaritoneClef()  # type: ignore
    if clef_str == "french_violin":
        return clef.FrenchViolinClef()  # type: ignore
    if clef_str == "gsoprano":
        return clef.GSopranoClef()  # type: ignore
    if clef_str == "mezzosoprano":
        return clef.MezzoSopranoClef()  # type: ignore
    if clef_str == "subbass":
        return clef.SubBassClef()  # type: ignore
    info = Clef._clef_info.get(clef_str)
    if not info:
        info = aclef.get("clef_info")
    if info is not None:
        # construct a clef from info
        c = None
        if info[0] == "G":
            c = clef.GClef()
            c.line = info[1]
            c.octaveChange = info[2]
        elif info[0] == "F":
            c = clef.FClef()
            c.line = info[1]
            c.octaveChange = info[2]
        elif info[0] == "C":
            c = clef.CClef()
            c.line = info[1]
            c.octaveChange = info[2]
        if c is not None:
            return c
    raise ValueError(f"Unknown clef string {clef_str} or clef {aclef}.")


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


def _add_measure_content(m21measure, measure, ties, ismidi) -> None:
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
    ties: dict
        See ties initialization comment in _score_to_music21.
    ismidi: bool
        Is this going to be a MIDI file? Requires non-zero durations.

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

        for voice_num, voice in enumerate(voices):
            m21voice = stream.Voice(id=str(voice_num + 1))
            _add_measure_content_from_list(
                m21voice, measure, voice, ties, ismidi
            )
            m21measure.insert(0, m21voice)
    else:
        _add_measure_content_from_list(
            m21measure, measure, measure.content, ties, ismidi
        )


def _add_expressions_to_m21(m21note, item):
    """make m21 expressions from any expression data in item's properties"""
    global _m21trills, _m21turns, _m21mordents
    if item.get("has_trill", False):
        trill = expressions.Trill()
        _m21trills.append((m21note, trill, item.get("trill_pitch")))
        m21note.expressions.append(trill)
    if item.get("has_trill_extension", False):
        m21note.expressions.append(expressions.TrillExtension())
    if item.get("has_turn", False):
        turn = expressions.Turn()
        _m21turns.append((m21note, turn, item.get("turn_pitches")))
        m21note.expressions.append(turn)
    if item.get("has_inverted_turn", False):
        turn = expressions.InvertedTurn()
        _m21turns.append((m21note, turn, item.get("inverted_turn_pitches")))
        m21note.expressions.append(turn)
    if item.get("has_mordent", False):
        mordent = expressions.GeneralMordent()
        _m21mordents.append((m21note, mordent, item.get("mordent_pitch")))
        m21note.expressions.append(mordent)
    if item.get("has_inverted_mordent", False):
        mordent = expressions.InvertedMordent()
        apitch = item.get("inverted_mordent_pitch")
        _m21mordents.append((m21note, mordent, apitch))
        m21note.expressions.append(mordent)
    if item.get("has_shake", False):
        m21note.expressions.append(expressions.Shake())
    if item.get("has_schleifer", False):
        m21note.expressions.append(expressions.Schleifer())


def _add_measure_content_from_list(
    m21parent, measure, content, ties, ismidi
) -> None:
    """
    insert content (Notes, Chords, Rests) from a Measure to m21 stream

    The m21 stream, called `m21parent`, can be a Music21 measure or voice.
    Voices are needed when content overlaps. `content` must be non-overlapping.
    m21parent is padded with a rest to achieve a duration of `dur`
    """
    # keep track of the maximum offset of any item in the measure, so we can
    # add a rest at the end if needed to fill out the measure.
    max_offset = measure.onset
    measure_position = 0  # keeps track of expected next onset time
    for item in content:
        actual_onset = item.onset
        actual_offset = item.offset
        if ismidi and actual_offset < actual_onset + 0.001:
            actual_offset = actual_onset + 0.001  # minimum midi dur is 0.001qtr
        max_offset = max(max_offset, actual_offset)
        measure_delta = actual_onset - measure.onset
        duration = actual_offset - actual_onset
        print(
            "m21_export: duration",
            duration,
            "actual_onset",
            actual_onset,
            "actual_offset",
            actual_offset,
        )
        if isinstance(item, (Note, Rest, Chord)) and (
            measure_delta > measure_position + 1e-6
        ):
            m21rest = note.Rest()
            m21rest.offset = measure_position
            m21rest.duration.quarterLength = measure_delta - measure_position
            m21parent.insert(measure_position, m21rest)

        # measure_position is the place where the item after this one
        # is expected. It is used to determine on the next iteration if
        # we need to pad with a rest
        measure_position = actual_offset - measure.onset

        # now that we've padded to measure_position with a rest if necessary,
        # insert the Note, Rest, or Chord from the score:
        if isinstance(item, Note):
            m21note = note.Note(nameWithOctave=item.name_with_octave)
            m21note.offset = measure_delta  # "offset" = "from measure start"
            # special encoding for grace notes:
            if not ismidi and (duration == 0 or item.get("is_grace")):
                grace_ql = duration if duration > 0 else 0.25
                m21note.duration = m21Duration(grace_ql).getGraceDuration()
            else:
                m21note.duration.quarterLength = duration
            print("m21_export duration", m21note.duration.quarterLength)
            print("    ismidi", ismidi)
            _add_expressions_to_m21(m21note, item)
            if item.get("hide_on_print", False):
                m21note.style.hideObjectOnPrint = True
            if isinstance(item.dynamic, int):
                m21note.volume.velocity = item.dynamic
            # otherwise, use default because I am not sure how
            #     to translate anything other dynamic value.
            m21parent.insert(m21note.offset, m21note)
            # if note is tied or tied to, enter it in ties:
            if item.tie:  # item is tied to item.tie
                # I think if (item in ties) it must be because it is tied to,
                # but we'll use the tied_to field just in case.
                is_tied_to = (item in ties) and ties[item][1]
                ties[item] = (m21note, is_tied_to)
                # set ties[item.tie]'s is_tied_to field to True
                # I don't expect ties[item.tie] to even exist, but if it does,
                # we've already created the m21 note corresponding to item.tie
                # and need to maintain the mapping from AMADS Note to m21 note:
                tied_to_m21 = None
                if item.tie in ties:
                    tied_to_m21 = ties[item.tie][0]
                ties[item.tie] = (tied_to_m21, True)
            if (item in ties) and (ties[item][0] is None):
                # update entry with m21note. This happens when we executed
                # ties[item.tie] = (tied_to_m21, True) just above, but we
                # did not yet create the m21 note corresponding to item. We
                # have it now, so save the mapping now:
                ties[item] = (m21note, ties[item][1])
        elif isinstance(item, Rest):
            m21rest = note.Rest()
            m21rest.offset = measure_delta
            m21rest.duration.quarterLength = duration
            m21parent.insert(m21rest.offset, m21rest)
        elif isinstance(item, Chord):
            amads_notes: list[Note] = item.list_all(Note)  # type: ignore
            pitches = [n.name_with_octave for n in amads_notes]
            m21chord = chord.Chord(pitches)
            m21chord.offset = measure_delta
            m21chord.duration.quarterLength = duration
            m21parent.insert(m21chord.offset, m21chord)
            # handle ties on individual notes within the chord
            for amads_note, m21note in zip(amads_notes, m21chord.notes):
                if amads_note.tie:
                    is_tied_to = (amads_note in ties) and ties[amads_note][1]
                    ties[amads_note] = (m21note, is_tied_to)
                    tied_to_m21 = None
                    if amads_note.tie in ties:
                        tied_to_m21 = ties[amads_note.tie][0]
                    ties[amads_note.tie] = (tied_to_m21, True)
                if (amads_note in ties) and (ties[amads_note][0] is None):
                    ties[amads_note] = (m21note, ties[amads_note][1])

    if max_offset < measure.offset - 1e-6:
        # need a rest to fill out the measure in Music21,
        # otherwise, it will shorten the duration of the measure
        m21rest = note.Rest()
        # music21 offset is relative to measure:
        m21rest.offset = max_offset - measure.onset
        m21rest.duration.quarterLength = measure.offset - max_offset
        assert (
            m21rest.duration.quarterLength > 0
        ), "rest duration must be positive"
        m21parent.insert(m21rest.offset, m21rest)


_accidentals = ["double-flat", "flat", "natural", "sharp", "double-sharp"]


def lookup_accidental(diff: int) -> str:
    """convert pitch difference to accidental requuired

    If diff is out of range, just return double-flat or double-sharp.
    """
    diff = max(-2, min(2, diff))
    return _accidentals[diff + 2]


def _get_turn_pitches(
    turn: expressions.Turn, m21note: note.Note
) -> tuple[pitch.Pitch, pitch.Pitch]:
    """resolve upper and lower turn pitches from music21"""
    turn.resolveOrnamentalPitches(m21note)
    m21pitches = turn.ornamentalPitches
    if m21pitches[0].midi > m21pitches[1].midi:
        return (m21pitches[0], m21pitches[1])
    else:
        return (m21pitches[1], m21pitches[0])


def _get_pitch_diff(
    m21note: note.Note, expr: expressions.Ornament, apitch: Pitch
) -> int:
    """factors out a common calculation for trills and mordents"""
    expr.resolveOrnamentalPitches(m21note)
    return apitch.key_num - expr.ornamentalPitches[0].midi


def music21_resolve_ornaments():
    """fix up ornaments that need accidentals"""
    global _m21trills, _m21turns, _m21mordents
    for item in _m21trills:
        (m21note, trill, apitch) = item
        # see if trill pitches are already correct
        diff = _get_pitch_diff(m21note, trill, apitch)
        if diff != 0:
            trill.accidental = lookup_accidental(diff)
            # if there was already an accidental, we might get the wrong result
            diff2 = _get_pitch_diff(m21note, trill, apitch)
            if diff2 != 0:
                trill.accidental = lookup_accidental(diff + diff2)
                diff3 = _get_pitch_diff(m21note, trill, apitch)
                if diff3 != 0:
                    raise Exception(
                        "Could not resolve trill accidental."
                        f" Trilled note is {m21note}, desired pitch is "
                        f"{trill.ornamentalPitches[0]}. Pitch differences "
                        f"were {diff} and {diff2}. Tried "
                        f"{lookup_accidental(diff)} and "
                        f"{lookup_accidental(diff + diff2)}."
                    )

    for item in _m21turns:
        (m21note, turn, pitches) = item
        assert len(pitches) == 2, "expected 2 Pitches in turn info"
        p0 = pitches[0].key_num
        p1 = pitches[1].key_num
        upper = max(p0, p1)
        lower = min(p0, p1)
        # see if turn pitches are correct
        m21upper, m21lower = _get_turn_pitches(turn, m21note)

        # start with upper pitch and accidental
        diff = upper.key_num - m21upper.midi
        if diff != 0:
            turn.upperAccidental = lookup_accidental(diff)
            # if there was already an accidental, we might get the wrong result
            m21upper, m21lower = _get_turn_pitches(turn, m21note)
            diff2 = upper.key_num - m21upper.midi
            if diff2 != 0:
                turn.upperAccidental = lookup_accidental(diff + diff2)
                m21upper, m21lower = _get_turn_pitches(turn, m21note)
                diff3 = upper.key_num - m21upper.midi
                if diff3 != 0:
                    raise Exception(
                        "Could not resolve upper turn accidental."
                        f" Turn note is {m21note}, desired upper pitch is "
                        f"{m21upper}. Pitch differences were {diff} and "
                        f"{diff2}. Tried {lookup_accidental(diff)} and "
                        f"{lookup_accidental(diff + diff2)}."
                    )

        # now do lower pitch and accidental
        diff = lower.key_num - m21lower.midi
        if diff != 0:
            turn.lowerAccidental = lookup_accidental(diff)
            # if there was already an accidental, we might get the wrong result
            m21lower, m21lower = _get_turn_pitches(turn, m21note)
            diff2 = lower.key_num - m21lower.midi
            if diff2 != 0:
                turn.lowerAccidental = lookup_accidental(diff + diff2)
                m21lower, m21lower = _get_turn_pitches(turn, m21note)
                diff3 = lower.key_num - m21lower.midi
                if diff3 != 0:
                    raise Exception(
                        "Could not resolve lower turn accidental."
                        f" Turn note is {m21note}, desired lower pitch is "
                        f"{m21lower}. Pitch differences were {diff} and "
                        f"{diff2}. Tried {lookup_accidental(diff)} and "
                        f"{lookup_accidental(diff + diff2)}."
                    )

    for item in _m21mordents:
        (m21note, mordent, apitch) = item
        # see if mordent pitches are already correct
        diff = _get_pitch_diff(m21note, mordent, apitch)
        if diff != 0:
            mordent.accidental = lookup_accidental(diff)
            # if there was already an accidental, we might get the wrong result
            mordent.resolveOrnamentalPitches(m21note)
            diff2 = _get_pitch_diff(m21note, mordent, apitch)
            if diff2 != 0:
                mordent.accidental = lookup_accidental(diff + diff2)
                mordent.resolveOrnamentalPitches(m21note)
                diff3 = _get_pitch_diff(m21note, mordent, apitch)
                if diff3 != 0:
                    raise Exception(
                        "Could not resolve mordent accidental."
                        f" Mordented note is {m21note}, desired pitch is "
                        f"{mordent.ornamentalPitches[0]}. Pitch "
                        f"differences were {diff} and {diff2}. Tried "
                        f"{lookup_accidental(diff)} and "
                        f"{lookup_accidental(diff + diff2)}."
                    )


def _score_to_music21(
    score: Score,
    show: bool = False,
    filename: Optional[Path | str] = None,
    ismidi: bool = False,
) -> stream.Score:
    """
    Convert a Score to music21

    Parameters
    ----------
    score: Score
        The Score to convert
    show : bool, optional
        If True, print the music21 score structure for debugging.
    filename : Optional[Path |  str]
        If `show` and not None, `filename` is shown
    ismidi : bool, optional
        If True, the score is to be written as a MIDI file, so constructed
        time signatures are inserted when measure durations do not match the
        notated time signature. (This keeps bar lines in the right place when
        MIDI files are displayed.)

    Returns
    -------
    stream.Score
        The AMADS Score object converted to music21
    """
    # create a new music21 score
    global _m21trills, _m21turns, _m21mordents
    _m21trills = []
    _m21turns = []
    _m21mordents = []
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
    # The keys (AMADS Notes) are every Note with a tie or that is tied to.
    # The keys map to the m21 note and a boolean, giving 3 cases:
    # the m21 note should "start" a tie if the key has a tie and is not tied_to
    # the m21 note should "continue" if the key has a tie and is tied_to
    # the m21 note should "stop" if the key has no tie but is tied_to

    if ismidi:
        time_sig_tuples = _get_midi_time_signatures(score)
    else:
        time_sigs = score.time_signatures
        time_sig_tuples = [
            (ts.quarters, ts.upper, ts.lower, ts.duration) for ts in time_sigs
        ]
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
                m21container.id = part_id
                m21container.groups.append(part_id)
                m21staffs.append(m21container)
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

            time_sig_tuple = (4, 4, 0, 4)
            time_sig_index = 0  # index of the *next* time signature
            if len(time_sig_tuples) > 0 and time_sig_tuples[0][0] < 0.001:
                time_sig_tuple = time_sig_tuples[time_sig_index]
                time_sig_index = 1

            for index, measure in enumerate(staff.find_all(Measure)):
                measure = cast(Measure, measure)
                num = measure.number if measure.number else (index + 1)
                m21measure = stream.Measure(
                    number=num, duration=m21Duration(measure.duration)
                )
                # if measure is incomplete (e.g., pickup measure),
                # set paddingLeft to avoid Music21 padding with a rest.
                # Note that time_sig.duration is the nominal duration in
                # quarters, while time_sig.quarters is the *time* of the time
                # signature, also in quarters. time_sig inherits onset, which
                # gives time in either seconds or quarters.
                if measure.duration < time_sig_tuple[3] - 0.001:
                    m21measure.paddingLeft = (
                        time_sig_tuple[3] - measure.duration
                    )
                # add time signature change if any. If there are no time
                # signatures, time_sig_tuple is just providing a default
                # measure duration and should not be used to create an
                # explicit time signature
                if len(time_sig_tuples) > 0 and isclose(
                    time_sig_tuple[0], measure.onset, abs_tol=1e-3
                ):
                    if time_sig_tuple[1] != round(time_sig_tuple[1]):
                        raise ValueError(
                            "Cannot export fractional time signagure "
                            f"{time_sig_tuple[1]}/{time_sig_tuple[2]} to "
                            "Music21."
                        )
                    ts_element = m21TimeSignature(
                        f"{round(time_sig_tuple[1])}/{time_sig_tuple[2]}"
                    )
                    m21measure.insert(
                        time_sig_tuple[0] - measure.onset, ts_element
                    )
                    # move to the next time_sig, if any left. If not, we do
                    # not change time_sig, but since subsequent measures have
                    # greater onset times, we won't try to add another time_sig
                    if time_sig_index < len(time_sig_tuples):
                        time_sig_tuple = time_sig_tuples[time_sig_index]
                        time_sig_index += 1
                # add key signature changes
                for ks in measure.find_all(KeySignature):
                    ks = cast(KeySignature, ks)
                    ks_element = key.KeySignature(ks.key_sig)
                    m21measure.insert(ks.onset - measure.onset, ks_element)
                # add clef changes
                for clef_change in measure.find_all(Clef):
                    clef_change = cast(Clef, clef_change)
                    try:
                        clef_element = _m21_clef(clef_change.clef, clef_change)
                    except ValueError as e:
                        warnings.warn(str(e))
                        continue
                    m21measure.insert(
                        clef_change.onset - measure.onset, clef_element
                    )
                # add notes, rests, chords
                _add_measure_content(m21measure, measure, ties, ismidi)
                m21container.append(m21measure)
            if time_sig_index != len(time_sig_tuples):
                warnings.warn(
                    f"After converting AMADS staff {staff} to"
                    " Music21, there are left-over, unused time"
                    f" signatures, starting with {time_sig_tuple}."
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
            m21score.insert(0, m21container)  # staff info is in an m21 Part

    # fix up ties
    for amads_note in ties.keys():
        # print("*** amads_note in ties.keys()", amads_note)
        # amads_note.tie points to the next note in the tie (or None if no
        # outgoing tie) is_tied_to indicates if there's an incoming tie
        # from a previous note
        (m21note, is_tied_to) = ties[amads_note]
        # print("    *** m21note", m21note, "is_tied_to", is_tied_to)

        if m21note is None:  # note was tied to but we never put the tied-to
            # note into the m21score!
            warnings.warn(
                "In _score_to_music21: tied-to note not found:"
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
            # print("*** set tie to 'stop' on", m21note)
        elif not amads_note.tie and not is_tied_to:
            # No tie at all - don't set tie attribute
            pass
        else:
            assert (
                False
            ), f"Internal tie-fix-up error {amads_note}, {ties[amads_note]}"

    # fix up ornaments
    music21_resolve_ornaments()

    if show:
        music21_show(m21score, filename)  # type: ignore

    return m21score


def _insert_measures_into(staff, score) -> None:
    """make measures to cover duration of staff based on
    score.time_signatures
    """
    dur = staff.duration
    mdur = 0  # duration of all the measures
    tsi = 0  # index of the next time signature
    tsdur = 4  # default time signature quarters duration
    while mdur < dur:
        # first, update tsdur if we have arrived at a new time signature:
        if (
            tsi < len(score.time_signatures)
            and score.time_signatures[tsi].quarters <= mdur + 0.001
        ):
            tsdur = score.time_signatures[tsi].duration
            tsi += 1
        _ = Measure(parent=staff, onset=mdur, duration=tsdur)
        mdur += tsdur


def _unflatten(score: Score) -> Score:
    """_score_to_music21 expects a full score, so this function makes a
    full score from a flattened one if score is flat. Maybe this should be
    a part of basics.py like score.flatten(), but maybe it is not a good
    idea to encourage unflattening, since flattening can lose a lot of
    information.

    Construct one Staff per Part. Add measures according to the time
    signatures. Fill in measures with tied notes.
    """
    if not score.is_flat():
        return score
    score.convert_to_quarters()
    full_score = cast(Score, score.emptycopy())
    for part in cast(list[Part], score.list_all(Part)):
        full_part = cast(Part, part.insert_copy_into(full_score))
        full_staff = Staff(parent=full_part, duration=full_part.duration)
        _insert_measures_into(full_staff, score)
        # insert each note into measures:
        measures = full_staff.content
        mi = 0  # index of measure
        for a_note in part.content:  # a_note is a Note, note is a Music21 class
            onset = a_note.onset
            while mi + 1 < len(measures) and onset >= measures[mi].offset:
                mi += 1  # advance to next measure
            measure = measures[mi]
            full_note = cast(Note, a_note.insert_copy_into(measure))
            nexti = mi + 1
            while full_note.offset > measure.offset:  # tie across bar line
                next_measure = measures[nexti]
                tied_note = Note(
                    parent=next_measure,
                    onset=next_measure.onset,
                    duration=full_note.offset - next_measure.onset,
                )
                full_note.tie = tied_note
                full_note.duration = tied_note.onset - full_note.onset
                full_note = tied_note
                measure = next_measure
                nexti += 1
    return full_score


def music21_export(
    score: Score, filename: Path | str, format: str, show: bool, is_temp: bool
) -> None:
    """Save a Score to a file using music21.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : Path | str
        The name or path of the file to save to.
    format : str
        The format to export. Must be "musicxml", "midi", "mei",
        "lilypond", or "kern".
    show : bool, optional
        If True, print the music21 score structure for debugging.
    is_temp: bool
        This is ignored since we do not create temp files here.
    """
    score.convert_to_quarters()
    score = _unflatten(score)
    m21score = _score_to_music21(score, show, filename, format == "midi")

    if format == "musicxml":
        # Export as text and fix part id's
        exporter = musicxml.m21ToXml.GeneralObjectExporter(m21score)
        musicxml_bytes = exporter.parse()
        musicxml_str = musicxml_bytes.decode("utf-8")
        fixed_xml = fix_part_ids(musicxml_str)

        # Finally, write the file
        with open(filename, "w") as f:
            f.write(fixed_xml)
    elif format == "midi":
        m21score.write("midi", filename)
    elif format == "kern":
        m21score.write("kern", filename)
    elif format == "mei":
        m21score.write("mei", filename)
