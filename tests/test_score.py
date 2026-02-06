import io
import math
from typing import List, Union, cast

import pytest

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


def test_event_onset_none_raises():
    note = Note(parent=None, onset=None, duration=1.0)
    try:
        _ = note.onset
    except ValueError as e:
        assert str(e) == "Onset time is not set."
    else:
        assert False, "Expected ValueError when onset is None"


def test_from_melody_overlapping_notes():
    """Test that overlapping notes raise a ValueError."""
    with pytest.raises(ValueError) as exc_info:
        Score.from_melody(
            pitches=[60, 62],
            durations=2.0,  # half notes
            iois=1.0,  # but only 1 beat apart
        )
    assert (
        str(exc_info.value)
        == "Notes overlap: note 0 ends at 2.00 but note 1 starts at 1.00"
    )


def test_from_melody_iois_onsets():
    """Test that iois + onsets raise a ValueError."""
    with pytest.raises(ValueError) as exc_info:
        Score.from_melody(pitches=[60, 62], onsets=[0, 1], iois=1.0)
    assert str(exc_info.value) == "Cannot specify both iois and onsets"


def test_from_melody_onsets_len():
    """Test that onsets length problems raise a ValueError."""
    with pytest.raises(ValueError) as exc_info:
        Score.from_melody(pitches=[60, 62], onsets=[0, 1, 2])
    assert str(exc_info.value) == "onsets list must have same length as pitches"


def test_from_melody_list_lens():
    """Test that list length problems raise a ValueError."""
    with pytest.raises(ValueError) as exc_info:
        Score.from_melody(pitches=[60, 62], onsets=[0, 1], durations=[1, 1, 1])
    assert str(exc_info.value) == "All input lists must have the same length"


def test_from_melody_iois_len():
    """Test that iois list length problems raise a ValueError."""
    with pytest.raises(ValueError) as exc_info:
        Score.from_melody(pitches=[60, 62], iois=[0, 1])
    assert str(exc_info.value) == "iois list must have length len(pitches) - 1"


def test_from_melody_empty_pitches():
    """Test that an empty list of pitches creates a valid empty score."""
    score = Score.from_melody(pitches=[])
    assert score.duration == 0.0
    assert len(score.content) == 1  # should have one empty part
    # part should have no notes:
    assert len(cast(Part, score.content[0]).content) == 0


def test_invalid_note():
    melody: list[Union[Pitch, int, float, str]] = ["C", "H", "G"]
    with pytest.raises(ValueError):
        Score.from_melody(melody)


def test_copy_score():
    score = Score.from_melody(pitches=[60, 62, 64], durations=1.0)
    copied_score = cast(Score, score.copy())

    copied_note = cast(Note, cast(Part, copied_score.content[0]).content[0])
    assert isinstance(copied_note, Note)

    copied_part = copied_score.content[0]
    assert isinstance(copied_part, Part)

    assert copied_note.parent == copied_part
    assert copied_part.parent == copied_score

    assert copied_part.parent != score


def test_parent():
    score = Score.from_melody(pitches=[60, 62, 64], durations=1.0)

    part = score.content[0]
    assert isinstance(part, Part)
    assert part.part is None
    assert part.parent == part.score == score

    note = part.content[0]
    assert isinstance(note, Note)
    assert note.part == part
    assert note.score == score


def test_quantize():
    """See if when tied notes quantize to zero that the tied note
    is removed correctly.
    """
    # case 1: C tied to short C
    note1 = Note(duration=1, pitch="C4")
    note2 = Note(duration=0.125, pitch="C4")
    note1.tie = note2
    meas1 = Measure(note1, note2)
    staff = Staff(meas1)
    score = Score(Part(staff))

    # case 2: short D tied to long D
    note1 = Note(parent=meas1, onset=1.875, duration=0.125, pitch="D4")
    note2 = Note(parent=meas1, onset=2, duration=1, pitch="D4")
    note1.tie = note2

    # case 3: same as case 1 but F4 tied across measure
    note1 = Note(parent=meas1, onset=3, duration=1, pitch="F4")
    meas2 = Measure(parent=staff, onset=4)
    assert staff.duration == 4
    assert meas2.offset == 8
    staff.inherit_duration()
    assert staff.duration == 8
    note2 = Note(parent=meas2, onset=4, duration=0.125, pitch="F4")
    note1.tie = note2

    # case 4: short G tied to long G tied to short G
    note1 = Note(parent=meas2, onset=4.875, duration=0.125, pitch="G4")
    note2 = Note(parent=meas2, onset=5, duration=1, pitch="G4")
    note3 = Note(parent=meas2, onset=6, duration=0.125, pitch="G4")
    note1.tie = note2
    note2.tie = note3

    # case 5: two short tied A's that quantize to eighth (0.5), but each
    #     alone quantizes to zero
    note1 = Note(parent=meas2, onset=7, duration=0.24, pitch="A4")
    note2 = Note(parent=meas2, onset=7.24, duration=0.24, pitch="A4")
    note1.tie = note2

    # case 6: a single short B that quantizes to zero duration
    Note(parent=meas2, onset=7.5, duration=0.125, pitch="B4")

    print("Before quantize:")
    score.show(4)
    assert score.has_ties()
    score.quantize(2)
    print("After quantize:")
    score.show(4)
    assert not score.has_ties()

    # Check Score structure
    assert isinstance(score, Score)
    assert score.onset == 0.0
    assert score.duration == 4.0

    # Check Part
    assert len(score.content) == 1
    part = score.content[0]
    assert isinstance(part, Part)
    assert part.onset == 0.0

    # Check Staff
    assert len(part.content) == 1
    staff = part.content[0]
    assert isinstance(staff, Staff)
    assert staff.onset == 0.0

    # Check Measures
    assert len(staff.content) == 2
    m1, m2 = staff.content
    assert isinstance(m1, Measure)
    assert isinstance(m2, Measure)
    assert m1.onset == 0.0
    assert m1.duration == 4.0
    assert m2.onset == 4.0
    assert m2.duration == 4.0

    # Check Notes in Measure 1
    n1, n2, n3 = m1.content
    assert (
        n1.onset == 0.0 and n1.duration == 1.0 and cast(Note, n1).key_num == 60
    )
    assert (
        n2.onset == 2.0 and n2.duration == 1.0 and cast(Note, n2).key_num == 62
    )
    assert (
        n3.onset == 3.0 and n3.duration == 1.0 and cast(Note, n3).key_num == 65
    )

    # Check Notes in Measure 2
    n4, n5, n6 = m2.content
    assert (
        n4.onset == 5.0 and n4.duration == 1.0 and cast(Note, n4).key_num == 67
    )
    assert (
        n5.onset == 7.0 and n5.duration == 0.5 and cast(Note, n5).key_num == 69
    )
    assert (
        n6.onset == 7.5 and n6.duration == 0.5 and cast(Note, n6).key_num == 71
    )

    # Since we have a full score here, test some other core functions:
    # staff test:
    assert n1.staff == staff
    assert n5.staff == staff

    # measure test:
    # n1 is in measure 1
    assert n1.measure == m1
    # n5 is in measure 2
    assert n5.measure == m2

    # part test:
    assert n1.part == part
    assert n6.part == part

    # score test:
    # n3 is in score
    assert n3.score == score
    # n4 is in score
    assert n4.score == score


def test_lyrics():
    note1 = Note(onset=0, duration=1, pitch="C4", lyric="Hello")
    assert (
        str(note1) == "Note(onset=0.000, duration=1.000,"
        " lyric=Hello, pitch=C4/60)"
    )


def test_step():
    note1 = Note(onset=0, duration=1, pitch="C4")
    assert note1.step == "C"
    note2 = Note(onset=0, duration=1, pitch="D#4")
    assert note2.step == "D"
    note3 = Note(onset=0, duration=1, pitch="Fb4")
    assert note3.step == "F"
    note4 = Note(onset=0, duration=1, pitch="G##4")
    assert note4.step == "G"


def test_name():
    note1 = Note(onset=0, duration=1, pitch="C4")
    assert note1.name == "C"
    note2 = Note(onset=0, duration=1, pitch="D#4")
    assert note2.name == "D#"
    note3 = Note(onset=0, duration=1, pitch="Fb4")
    assert note3.name == "Fb"
    note4 = Note(onset=0, duration=1, pitch="G##4")
    assert note4.name == "G##"


def test_pitch_class():
    note1 = Note(onset=0, duration=1, pitch="C4")
    assert note1.pitch_class == 0
    note2 = Note(onset=0, duration=1, pitch="D#4")
    assert note2.pitch_class == 3
    note3 = Note(onset=0, duration=1, pitch="Fb4")
    assert note3.pitch_class == 4
    note4 = Note(onset=0, duration=1, pitch="G##4")
    assert note4.pitch_class == 9


def test_pitch_class_setter():
    note1 = Note(onset=0, duration=1, pitch="C4")
    note1.pitch_class = 4  # Set to E
    assert note1.pitch_class == 4
    assert note1.name_with_octave == "E4"

    note2 = Note(onset=0, duration=1, pitch="D#4")
    note2.pitch_class = 7  # Set to G
    assert note2.pitch_class == 7
    assert note2.name_with_octave == "G4"


def test_octave():
    note1 = Note(onset=0, duration=1, pitch="C4")
    assert note1.octave == 4
    note2 = Note(onset=0, duration=1, pitch="D#5")
    assert note2.octave == 5
    note3 = Note(onset=0, duration=1, pitch="Fb3")
    assert note3.octave == 3
    note4 = Note(onset=0, duration=1, pitch="G##2")
    assert note4.octave == 2


def test_octave_setter():
    note1 = Note(onset=0, duration=1, pitch="C4")
    note1.octave = 5
    assert note1.octave == 5
    assert note1.name_with_octave == "C5"

    note2 = Note(onset=0, duration=1, pitch="D#4")
    note2.octave = 3
    assert note2.octave == 3
    assert note2.name_with_octave == "D#3"


def test_key_num():
    note1 = Note(onset=0, duration=1, pitch="C4")
    assert note1.key_num == 60
    note2 = Note(onset=0, duration=1, pitch="D#5")
    assert note2.key_num == 75
    note3 = Note(onset=0, duration=1, pitch="Fb3")
    assert note3.key_num == 52
    note4 = Note(onset=0, duration=1, pitch="G##2")
    assert note4.key_num == 45
    try:
        note5 = Note(onset=0, duration=1, pitch=None)
        _ = note5.key_num
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"


def test_enharmonic():
    note1 = Note(onset=0, duration=1, pitch="C4")
    enharmonic1 = note1.enharmonic()
    assert enharmonic1.name_with_octave == "B#3"

    note2 = Note(onset=0, duration=1, pitch="D#4")
    enharmonic2 = note2.enharmonic()
    assert enharmonic2.name_with_octave == "Eb4"

    note3 = Note(onset=0, duration=1, pitch="Fb4")
    enharmonic3 = note3.enharmonic()
    assert enharmonic3.name_with_octave == "E4"

    note4 = Note(onset=0, duration=1, pitch="G##4")
    enharmonic4 = note4.enharmonic()
    assert enharmonic4.name_with_octave == "A4"

    note5 = Note(onset=0, duration=1, pitch=None)
    try:
        _ = note5.enharmonic()
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"


def test_upper_enharmonic():
    note1 = Note(onset=0, duration=1, pitch="C4")
    enharmonic1 = note1.upper_enharmonic()
    assert enharmonic1.name_with_octave == "Dbb4"

    note2 = Note(onset=0, duration=1, pitch="D#4")
    enharmonic2 = note2.upper_enharmonic()
    assert enharmonic2.name_with_octave == "Eb4"

    note3 = Note(onset=0, duration=1, pitch="Fb4")
    enharmonic3 = note3.upper_enharmonic()
    assert enharmonic3.name_with_octave == "Gbbb4"

    note4 = Note(onset=0, duration=1, pitch="G##4")
    enharmonic4 = note4.upper_enharmonic()
    assert enharmonic4.name_with_octave == "A4"

    note5 = Note(onset=0, duration=1, pitch=None)
    try:
        _ = note5.upper_enharmonic()
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"


def test_lower_enharmonic():
    note1 = Note(onset=0, duration=1, pitch="C4")
    enharmonic1 = note1.lower_enharmonic()
    assert enharmonic1.name_with_octave == "B#3"

    note2 = Note(onset=0, duration=1, pitch="D#4")
    enharmonic2 = note2.lower_enharmonic()
    assert enharmonic2.name_with_octave == "C###4"

    note3 = Note(onset=0, duration=1, pitch="Fb4")
    enharmonic3 = note3.lower_enharmonic()
    assert enharmonic3.name_with_octave == "E4"

    note4 = Note(onset=0, duration=1, pitch="G##4")
    enharmonic4 = note4.lower_enharmonic()
    assert enharmonic4.name_with_octave == "F####4"

    note5 = Note(onset=0, duration=1, pitch=None)
    try:
        _ = note5.lower_enharmonic()
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"


def test_simplest_enharmonic():
    note1 = Note(onset=0, duration=1, pitch="C4")
    enharmonic1 = note1.simplest_enharmonic()
    assert enharmonic1.name_with_octave == "C4"

    note2 = Note(onset=0, duration=1, pitch="D#4")
    enharmonic2 = note2.simplest_enharmonic()
    assert enharmonic2.name_with_octave == "Eb4"

    note3 = Note(onset=0, duration=1, pitch="Fb4")
    enharmonic3 = note3.simplest_enharmonic()
    assert enharmonic3.name_with_octave == "E4"

    note4 = Note(onset=0, duration=1, pitch="G##4")
    enharmonic4 = note4.simplest_enharmonic()
    assert enharmonic4.name_with_octave == "A4"

    note5 = Note(onset=0, duration=1, pitch=None)
    try:
        _ = note5.simplest_enharmonic()
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"


def test_clef():
    clef = Clef(onset=4.0, clef="treble")
    assert clef.clef == "treble"
    assert clef.onset == 4.0
    assert clef.duration == 0.0
    assert str(clef) == "Clef(onset=4.000, treble)"

    try:
        _ = Clef(onset=0, clef="wrong")
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError for invalid clef"


def test_key_sig():
    key_sig = KeySignature(onset=4, key_sig=2)
    assert key_sig.key_sig == 2
    assert key_sig.onset == 4.0
    assert key_sig.duration == 0.0
    assert str(key_sig) == "KeySignature(onset=4.000, 2 sharps)"


def test_eventgroup():
    note1 = Note(onset=0, duration=1, pitch="C4")
    note2 = Note(onset=1, duration=1, pitch="E4")
    eg = Part(note1, note2, onset=0)
    try:
        _ = Part(note1, note2)
    except Exception:
        pass
    else:
        assert False, "Expected ValueError adding event with parent"
    assert eg.onset == 0.0
    assert eg.duration == 2.0
    assert len(eg.content) == 2
    assert str(eg) == "Part(onset=0.000, duration=2.000)"

    eg2 = Measure()
    try:
        _ = eg2.onset
    except ValueError as e:
        assert str(e) == "Onset time is not set"
    else:
        assert False, "Expected ValueError when onset is None"

    eg3 = Measure(duration=2)
    note1 = note1.insert_copy_into(eg3)
    note2 = note2.insert_copy_into(eg3)
    eg3.onset = 4
    assert eg3.onset == 4.0
    assert eg3.duration == 2.0
    assert len(eg3.content) == 2
    assert note1.onset == 4.0
    assert note2.onset == 5.0
    assert str(eg3) == "Measure(onset=4.000, duration=2.000)"

    part = Part(eg3, onset=0)
    assert part.onset == 0.0
    assert part.duration == 6.0
    assert len(part.content) == 1
    assert str(part) == "Part(onset=0.000, duration=6.000)"
    assert part.has_instanceof(Note)
    assert part.has_instanceof(Measure)
    assert not part.has_instanceof(Staff)
    assert part.has_rests() is False
    _ = Measure(Rest(onset=0, duration=4), onset=0, parent=part)
    assert part.has_rests() is True

    assert part.has_measures() is True

    assert part.has_chords() is False
    chord = Chord(
        Note(duration=1, pitch="D4"),
        Note(duration=1, pitch="F#4"),
        onset=6,
        parent=eg3,
    )
    assert part.has_chords() is True

    no_rests = part.remove_rests()
    assert no_rests.has_rests() is False
    buf = io.StringIO()
    no_rests.show(file=buf)
    correct = """Part(onset=0.000, duration=6.000)
    Measure(onset=0.000, duration=4.000)
    Measure(onset=4.000, duration=2.000)
        Note(onset=4.000, duration=1.000, pitch=C4/60)
        Note(onset=5.000, duration=1.000, pitch=E4/64)
        Chord(onset=6.000, duration=1.000)
            Note(onset=6.000, duration=1.000, pitch=D4/62)
            Note(onset=6.000, duration=1.000, pitch=F#4/66)
"""
    assert buf.getvalue() == correct
    assert chord.onset == 6.0
    assert chord.duration == 1.0
    assert str(chord) == "Chord(onset=6.000, duration=1.000)"

    eg4 = Staff(
        Note(pitch="C4"),
        Note(pitch="E4"),
        Note(pitch="G4"),
        Chord(Note(pitch="B3"), Note(pitch="D4")),
    )
    eg4.pack()
    eg4.show()
    assert eg4.onset == 0.0
    assert eg4.duration == 4.0
    assert len(eg4.content) == 4

    # let's test is_well_formed_full_part by moving the Part
    # content to a Staff and putting the Staff in the Part
    # and putting the Part in a Score - maybe it would have
    # been better to construct from scratch because it's a
    # pain to move all the members to a new parent.
    content = part.content
    part.content = []
    for elem in content:
        elem.parent = None  # ready to move to Staff
    Staff(*content, onset=0, parent=part)
    score = Score(part)
    assert score.is_well_formed_full_score() is True
    assert score.units_are_quarters is True
    assert score.units_are_seconds is False

    score.convert_to_seconds()
    assert score.units_are_quarters is False
    assert score.units_are_seconds is True

    # idempotent:
    score.convert_to_seconds()
    assert score.units_are_quarters is False
    assert score.units_are_seconds is True

    score.convert_to_quarters()
    score.convert_to_quarters()  # exercise a no-op path
    assert score.units_are_quarters is True
    assert score.units_are_seconds is False
    assert score.units_are_seconds is False  # exercise a no-op path
    assert score.is_well_formed_full_score() is True


def test_event_str():
    note = Note(onset=1, duration=2, pitch="A4")
    s = str(note)
    assert s.startswith("Note(")
    assert "onset=1.000" in s
    assert "duration=2.000" in s
    assert "pitch=A4" in s


def test_quantize_alignment():
    """Quantize should snap onsets and durations to multiples of 1/divisions."""
    # create a score with non-aligned onsets/durations
    score = Score.from_melody(
        pitches=[60, 62, 64],
        onsets=[0.13, 1.37, 2.88],
        durations=[0.47, 0.99, 0.26],
    )

    divisions = 4  # quarter divided into 4 -> quantum = 0.25
    for p in score.content:
        part = cast(Part, p)
        for event in part.content:
            assert event.units_are_quarters is True
            assert event.units_are_seconds is False
    score.convert_to_seconds()  # exercise conversion
    for p in score.content:
        part = cast(Part, p)
        for event in part.content:
            assert event.units_are_quarters is False
            assert event.units_are_seconds is True
    score.convert_to_quarters()  # back to quarters
    score.show()

    score.quantize(divisions)

    # traverse notes and assert onsets and durations are multiples of 1/divisions
    for part in score.content:
        for staff in getattr(part, "content", []):
            for measure in getattr(staff, "content", []):
                for note in getattr(measure, "content", []):
                    # skip non-Note objects
                    if not isinstance(note, Note):
                        continue
                    on_mul = note.onset * divisions
                    dur_mul = note.duration * divisions
                    assert math.isclose(
                        on_mul, round(on_mul), abs_tol=1e-8
                    ), f"onset {note.onset} not on grid for divisions={divisions}"
                    assert math.isclose(
                        dur_mul, round(dur_mul), abs_tol=1e-8
                    ), f"duration {note.duration} not on grid for divisions={divisions}"


def test_merge_tied_notes():
    """Test merging tied notes into single notes."""
    score = Score.from_melody(
        pitches=["C4", "C4", "E4", "E4", "E4", "G4"],
        durations=[1.0, 0.5, 0.5, 0.5, 1.0, 1.0],
        ties=[True, False, True, True, False, False],
    )
    print("Before merging tied notes:")
    score.show(4)

    score = score.merge_tied_notes()

    print("After merging tied notes:")
    score.show(4)

    # Check that tied notes have been merged correctly
    part: Part = score.content[0]  # type: ignore (score.content[i] is a Part)
    notes = [event for event in part.content if isinstance(event, Note)]
    assert len(notes) == 3  # Should be 3 notes after merging

    assert (
        notes[0].pitch
        and notes[0].pitch.key_num == 60
        and notes[0].duration == 1.5
    )
    assert (
        notes[1].pitch
        and notes[1].pitch.key_num == 64
        and notes[1].duration == 2.0
    )
    assert (
        notes[2].pitch
        and notes[2].pitch.key_num == 67
        and notes[2].duration == 1.0
    )


def test_pack():
    """Test merging tied notes into single notes."""
    score = Score.from_melody(
        pitches=["C4", "D4", "E4", "F4", "G4", "A4"],
        onsets=[0, 2, 3, 4, 5, 6],
        durations=[1.0, 0.5, 0.5, 0.5, 1.0, 1.0],
    )
    print("Before packing:")
    score.show(4)
    score.pack(0.0, sequential=True)
    print("After packing:")
    score.show(4)
    assert score.ismonophonic()
    assert score.parts_are_monophonic()


def test_well_formed():
    # Test is_well_formed_full_score method for various scenarios
    score = Score(
        Part(
            Staff(
                Measure(
                    Note(onset=0, duration=1.0, pitch="C4"),
                    Note(onset=1.0, duration=1.0, pitch="E4"),
                    Chord(
                        Note(onset=2.0, duration=1.0, pitch="G4"),
                        Note(onset=2.0, duration=1.0, pitch="B4"),
                        onset=2.0,
                    ),
                )
            )
        )
    )
    score1: Score = score.copy()  # type: ignore

    assert score1.is_well_formed_full_score() is True
    chord: Chord = next(score1.find_all(Chord))  # type: ignore
    Chord(
        Note(onset=2, duration=1.0, pitch="D5"),
        Note(onset=2, duration=1.0, pitch="F#5"),
        onset=2,
        parent=chord,
    )
    print("Modified score with invalid chord:")
    score1.show(4)
    assert score1.is_well_formed_full_score() is False

    score1: Score = score.copy()  # type: ignore
    assert score1.is_well_formed_full_score() is True
    measure: Measure = next(score1.find_all(Measure))  # type: ignore
    Measure(
        Note(onset=3.0, duration=1.0, pitch="A4"),
        Note(onset=4.0, duration=1.0, pitch="C5"),
        onset=3.0,
        parent=measure,
    )
    assert score1.is_well_formed_full_score() is False

    # insert a Staff directly into Score
    score1: Score = score.copy()  # type: ignore
    assert score1.is_well_formed_full_score() is True
    Staff(
        Note(onset=0, duration=1.0, pitch="D4"),
        Note(onset=1.0, duration=1.0, pitch="F#4"),
        onset=0,
        parent=score1,
    )
    assert score1.is_well_formed_full_score() is False

    # insert a Note directly into Part
    score1: Score = score.copy()  # type: ignore
    assert score1.is_well_formed_full_score() is True
    part: Part = score1.content[0]  # type: ignore
    Note(onset=0, duration=1.0, pitch="D4", parent=part)
    assert score1.is_well_formed_full_score() is False

    # put a rest in a staff
    score1: Score = score.copy()  # type: ignore
    assert score1.is_well_formed_full_score() is True
    staff: Staff = next(score1.find_all(Staff))  # type: ignore
    Rest(onset=2.0, duration=1.0, parent=staff)
    assert score1.is_well_formed_full_score() is False


def make_a_full_score() -> Score:
    """Helper function to create a well-formed full score for testing."""
    score = Score(
        Part(
            Staff(
                Measure(
                    Note(onset=0, duration=1.0, pitch="C4"),
                    Note(onset=1.0, duration=1.0, pitch="E4"),
                ),
                number=1,
            ),
            Staff(
                Measure(
                    Note(onset=0, duration=1.0, pitch="G4"),
                    Note(onset=1.0, duration=1.0, pitch="B4"),
                    Note(onset=2.0, duration=1.0, pitch="D5"),
                ),
                number=2,
            ),
            # duration None tests a case in the Part constructor:
            instrument="Flute",
            duration=None,
        ),
        Part(
            Staff(
                Measure(
                    Note(onset=0, duration=1.0, pitch="D4"),
                    Note(onset=1.0, duration=1.0, pitch="F#4"),
                ),
                number=3,
            ),
            instrument="Violin",
        ),
    )
    return score


def test_collapse_parts():
    """Test collapsing parts in a score into a single part
    where staff is specified."""
    score = make_a_full_score()
    score2: Score = score.copy()  # type: ignore
    print("Original score with multiple parts:")
    score.show(4)
    collapsed_score = score.collapse_parts(part=[0], staff=2)

    print("Collapsed score with single part:")
    collapsed_score.show(4)

    # Check that the collapsed score has only one part
    assert len(collapsed_score.content) == 1
    part: Part = collapsed_score.content[0]  # type: ignore
    # Check that the part contains all notes from staff 2
    notes: List[Note] = list(part.find_all(Note))  # type: ignore
    assert len(notes) == 3

    expected_pitches = {67, 71, 74}  # G4, B4, D5
    actual_pitches = {note.pitch.key_num for note in notes if note.pitch}
    assert actual_pitches == expected_pitches

    score: Score = score2.copy()  # type: ignore  # with has_ties=False:
    collapsed_score = score.collapse_parts(part=[0], staff=2, has_ties=False)

    print("Collapsed score with single part:")
    collapsed_score.show(4)

    # Check that the collapsed score has only one part
    assert len(collapsed_score.content) == 1
    part: Part = collapsed_score.content[0]  # type: ignore
    # Check that the part contains all notes from staff 2
    notes: List[Note] = list(part.find_all(Note))  # type: ignore
    assert len(notes) == 3

    expected_pitches = {67, 71, 74}  # G4, B4, D5
    actual_pitches = {note.pitch.key_num for note in notes if note.pitch}
    assert actual_pitches == expected_pitches

    # is_flat test
    assert score.is_flat

    # flatten test
    score = score2.flatten(collapse=True)
    # expect part instrument to be None
    part: Part = score.content[0]  # type: ignore
    assert part.instrument is None

    # change instruments to match and try again
    for p in score2.content:
        part = cast(Part, p)
        part.instrument = "Piano"
    score = score2.flatten(collapse=True)
    # expect part instrument to be Piano
    part: Part = score.content[0]  # type: ignore
    assert part.instrument == "Piano"

    # more is_flat testing, add Note to Score directly
    # start with score, which is properly flattened
    score3: Score = score.copy()  # type: ignore
    Note(onset=0, duration=1.0, pitch="C4", parent=score3)
    assert not score3.is_flat()

    # # more is_flat testing, add Note to Part directly
    # score3 : Score = score.copy()  # type: ignore
    # part : Part = score3.content[0]  # type: ignore
    # Note(onset=0, duration=1.0, pitch="C4", parent=part)
    # assert not score3.is_flat()

    # more is_flat testing, add non-note to a Part directly
    score3: Score = score.copy()  # type: ignore
    part: Part = score3.content[0]  # type: ignore
    Rest(onset=3, duration=1.0, parent=part)
    assert not score3.is_flat()

    # more is_flat testing, make a tied note
    score3: Score = score.copy()  # type: ignore
    part: Part = score3.content[0]  # type: ignore
    # first note is C4 at onset 0, duration 1.0
    note = Note(onset=1, duration=1.0, pitch="C4", parent=part)
    first_note = next(part.find_all(Note))  # type: ignore
    first_note.tie = note
    print("Score after adding tied Note in Part:")
    score3.show(4)
    assert not score3.is_flat()


def test_note_containers():
    """Test that Note containers work as expected."""
    score = make_a_full_score()
    containers = score.note_containers()
    print("note containers:", containers)

    # Expecting 3 containers
    assert len(containers) == 3
    assert containers[0] == score.content[0].content[0]  # type: ignore
    assert containers[1] == score.content[0].content[1]  # type: ignore
    assert containers[2] == score.content[1].content[0]  # type: ignore

    # test case where a part has no staff and is a container
    # remove staff from 2nd part
    part: Part = score.content[1]  # type: ignore
    part.flatten(in_place=True)  # move content up to Part level
    containers = score.note_containers()
    print("note containers after flattening part 2:", containers)
    # Expecting 3 containers now
    assert len(containers) == 3
    assert containers[0] == score.content[0].content[0]  # type: ignore
    assert containers[1] == score.content[0].content[1]  # type: ignore
    assert containers[2] == score.content[1]  # type: ignore


def test_remove_measures():
    """Test removing measures from a score."""
    score = make_a_full_score()
    # add a spurious top-level note to test that it is preserved
    Note(onset=4, duration=1.0, pitch="C5", parent=score)
    # add a spurious note in a staff to test that it is preserved
    part: Part = score.content[0]  # type: ignore
    staff: Staff = part.content[0]  # type: ignore
    Note(onset=8, duration=1.0, pitch="E5", parent=staff)
    print("Original score:")
    score.show(4)

    # Remove measures 1 from part 0
    modified_score = score.remove_measures()

    print("Modified score after removing measures:")
    modified_score.show(4)

    # Check that the measures have been removed correctly
    part: Part = modified_score.content[0]  # type: ignore
    assert len(part.content[0].content) == 3  # type: ignore
    assert len(part.content[1].content) == 3  # type: ignore

    part: Part = modified_score.content[1]  # type: ignore
    assert len(part.content[0].content) == 2  # type: ignore

    # Check that the top-level note is still present
    top_level_notes = [
        event for event in modified_score.content if isinstance(event, Note)
    ]
    assert len(top_level_notes) == 1
    assert (
        top_level_notes[0].pitch and top_level_notes[0].pitch.key_num == 72
    )  # C5

    # Check that the spurious note in staff is still present
    part: Part = modified_score.content[0]  # type: ignore
    staff: Staff = part.content[0]  # type: ignore
    spurious_notes = [
        event
        for event in staff.content
        if isinstance(event, Note) and event.onset == 8
    ]
    assert len(spurious_notes) == 1
    assert (
        spurious_notes[0].pitch and spurious_notes[0].pitch.key_num == 76
    )  # E5


def test_shift_content():
    """Test to see if chord content is shifted when chords are in
    sequence, and also test shifting content in a score."""
    score = Score(
        Part(
            Staff(
                Measure(
                    Chord(Note(pitch="C4"), Note(pitch="E4")),
                    Chord(Note(pitch="D4"), Note(pitch="F4")),
                )
            )
        )
    )
    print("Original score:")
    score.show(4)
    # check times in chords
    part = score.content[0]  # type: ignore
    staff = part.content[0]  # type: ignore
    measure = staff.content[0]  # type: ignore
    chord1 = measure.content[0]  # type: ignore
    chord2 = measure.content[1]  # type: ignore
    assert chord1.onset == 0.0
    assert chord2.onset == 1.0
    note1 = chord1.content[0]  # type: ignore
    note2 = chord1.content[1]  # type: ignore
    note3 = chord2.content[0]  # type: ignore
    note4 = chord2.content[1]  # type: ignore
    assert note1.onset == 0.0
    assert note2.onset == 0.0
    assert note3.onset == 1.0
    assert note4.onset == 1.0

    # Shift content by 2 quarters
    score.time_shift(2.0, content_only=True)

    print("Modified score after shifting content by 2 quarters:")
    score.show(4)

    # Check that all notes have been shifted correctly
    assert score.onset == 0.0
    part = score.content[0]  # type: ignore
    assert part.onset == 2.0
    staff = part.content[0]  # type: ignore
    assert staff.onset == 2.0
    measure = staff.content[0]  # type: ignore
    assert measure.onset == 2.0
    chord1 = measure.content[0]  # type: ignore
    chord2 = measure.content[1]  # type: ignore
    assert chord1.onset == 2.0
    assert chord2.onset == 3.0
    note1 = chord1.content[0]  # type: ignore
    note2 = chord1.content[1]  # type: ignore
    note3 = chord2.content[0]  # type: ignore
    note4 = chord2.content[1]  # type: ignore
    assert note1.onset == 2.0
    assert note2.onset == 2.0
    assert note3.onset == 3.0
    assert note4.onset == 3.0
    assert note4.measure is measure


def test_parts_are_monophonic():
    """Test parts_are_monophonic method."""
    # make a score with two monophonic parts
    score = Score(
        Part(
            Staff(
                Measure(
                    Note(onset=0.0, duration=1.0, pitch="C4"),
                    Note(onset=1.0, duration=1.0, pitch="D4"),
                )
            ),
            instrument="Flute",
        ),
        Part(
            Staff(
                Measure(
                    Note(onset=0.0, duration=1.0, pitch="E4"),
                    Note(onset=1.0, duration=1.0, pitch="F4"),
                )
            ),
            instrument="Oboe",
        ),
    )
    assert score.parts_are_monophonic() is True
    assert score.ismonophonic() is False

    # Add a chord to make it non-monophonic
    part: Part = score.content[0]  # type: ignore
    staff: Staff = part.content[0]  # type: ignore
    measure: Measure = staff.content[0]  # type: ignore
    Chord(
        Note(onset=5.0, duration=1.0, pitch="A4"),
        Note(onset=5.0, duration=1.0, pitch="C5"),
        onset=5.0,
        parent=measure,
    )
    assert score.parts_are_monophonic() is False
