import pytest

from amads.core.basics import Chord, Measure, Note, Part, Score, Staff


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


def test_from_melody_empty_pitches():
    """Test that an empty list of pitches creates a valid empty score."""
    score = Score.from_melody(pitches=[])
    assert score.duration == 0.0
    assert len(score.content) == 1  # should have one empty part
    assert len(score.content[0].content) == 0  # part should have no notes


def test_is_monophonic():
    score = Score.from_melody([60, 64, 67])
    assert score.is_monophonic

    # Test a score with overlapping notes
    score = Score()
    part = Part()
    part.insert(Note(pitch=60, duration=2.0, delta=0))
    part.insert(
        Note(pitch=64, duration=1.0, delta=1.0)
    )  # starts before first note ends
    score.insert(part)
    assert not score.is_monophonic


def test_get_notes_empty_score():
    """Test get_notes on an empty score returns empty generator."""
    score = Score()
    assert score.notes == []


def test_get_notes_single_note():
    """Test get_notes on a score with a single note."""
    score = Score()
    part = Part()
    note = Note(duration=1, pitch=60)
    part.insert(note)
    score.insert(part)

    notes = score.notes
    assert len(notes) == 1
    assert notes[0].pitch.keynum == 60
    assert notes[0].duration == 1


def test_get_notes_multiple_parts():
    """Test get_notes on a score with multiple parts and notes."""
    score = Score()

    # Create first part with two notes
    part1 = Part()
    note1 = Note(duration=1, pitch=60)
    note2 = Note(duration=2, pitch=62, delta=1)
    part1.insert(note1)
    part1.insert(note2)
    score.insert(part1)

    # Create second part with one note
    part2 = Part()
    note3 = Note(duration=1, pitch=64, delta=2)
    part2.insert(note3)
    score.insert(part2)

    notes = score.notes
    assert len(notes) == 3
    # Notes should be sorted by onset time
    assert [n.pitch.keynum for n in notes] == [60, 62, 64]
    assert [n.start for n in notes] == [0, 1, 2]


def test_get_notes_with_measures():
    """Test get_notes on a score with measures."""
    score = Score()
    part = Part()
    staff = Staff()

    # Create two measures with notes
    measure1 = Measure(duration=4)
    note1 = Note(duration=1, pitch=60)
    note2 = Note(duration=1, pitch=62, delta=2)
    measure1.insert(note1)
    measure1.insert(note2)

    measure2 = Measure(duration=4, delta=4)
    note3 = Note(duration=2, pitch=64)
    measure2.insert(note3)

    staff.insert(measure1)
    staff.insert(measure2)
    part.insert(staff)
    score.insert(part)

    notes = score.notes
    assert len(notes) == 3
    assert [n.pitch.keynum for n in notes] == [60, 62, 64]
    assert [n.start for n in notes] == [0, 2, 4]


def test_get_notes_with_chords():
    """Test get_notes on a score with chords."""
    score = Score()
    part = Part()

    # Create a chord with two notes
    chord = Chord(duration=2)
    note1 = Note(duration=2, pitch=60)  # C4
    note2 = Note(duration=2, pitch=64)  # E4
    chord.insert(note1)
    chord.insert(note2)

    # Add a regular note after the chord
    note3 = Note(duration=1, pitch=67, delta=2)  # G4

    part.insert(chord)
    part.insert(note3)
    score.insert(part)

    notes = score.notes
    assert len(notes) == 3
    # Notes from chord should be included
    assert sorted([n.pitch.keynum for n in notes if n.start == 0]) == [60, 64]
    # Regular note should follow
    assert [n.pitch.keynum for n in notes if n.start == 2] == [67]


@pytest.mark.skip(reason="Score.strip_ties() is not working properly yet.")
def test_get_notes_with_ties():
    """Test get_notes on a score with tied notes."""
    score = Score()
    part = Part()

    # Create two tied notes
    note1 = Note(duration=2, pitch=60)
    note1.tie = "start"
    note2 = Note(duration=2, pitch=60, delta=2)
    note2.tie = "stop"

    part.insert(note1)
    part.insert(note2)
    score.insert(part)

    notes = score.notes

    # TODO: currently this test fails, we are getting two notes not one
    assert len(notes) == 1  # Tied notes should be merged into one

    assert notes[0].pitch.keynum == 60
    assert notes[0].duration == 4  # Duration should be combined
    assert notes[0].tie is None  # Tie should be stripped


def test_get_notes_sorted_by_start_and_pitch():
    """Test that notes are returned sorted by start time and then by pitch."""
    score = Score()
    part = Part()
    score.insert(part)

    # Create notes in scrambled order
    # Three notes at t=0 with different pitches (67, 64, 60)
    note1 = Note(duration=1, pitch=67, delta=0)  # G4
    note2 = Note(duration=1, pitch=64, delta=0)  # E4
    note3 = Note(duration=1, pitch=60, delta=0)  # C4

    # Two notes at t=2 with different pitches (65, 62)
    note4 = Note(duration=1, pitch=65, delta=2)  # F4
    note5 = Note(duration=1, pitch=62, delta=2)  # D4

    # Insert notes in an order different from both start time and pitch
    part.insert(note1)  # t=0, G4
    part.insert(note4)  # t=2, F4
    part.insert(note2)  # t=0, E4
    part.insert(note5)  # t=2, D4
    part.insert(note3)  # t=0, C4

    # Convert to list to ensure iterability
    notes = list(score.notes)
    assert len(notes) == 5

    # Notes at t=0 should be sorted by pitch (C4, E4, G4)
    first_three = notes[:3]
    assert [n.pitch.keynum for n in first_three] == [60, 64, 67]
    assert all(n.start == 0 for n in first_three)

    # Notes at t=2 should be sorted by pitch (D4, F4)
    last_two = notes[3:]
    assert [n.pitch.keynum for n in last_two] == [62, 65]
    assert all(n.start == 2 for n in last_two)

    # Verify the complete sequence
    assert [(n.start, n.pitch.keynum) for n in notes] == [
        (0, 60),  # C4
        (0, 64),  # E4
        (0, 67),  # G4
        (2, 62),  # D4
        (2, 65),  # F4
    ]


def test_next_and_previous_note():
    """Test next_note and previous_note properties."""
    score = Score()
    part = Part()
    score.insert(part)

    # Create notes in a specific order to test both sequential and simultaneous notes
    # t=0: C4, E4, G4 (chord)
    # t=2: D4
    # t=3: F4

    # Create a chord with three notes at t=0
    chord = Chord(duration=1.0)
    for pitch in [60, 64, 67]:  # C4, E4, G4
        note = Note(duration=1.0, pitch=pitch)
        chord.insert(note)
    part.insert(chord)

    # Add D4 at t=2
    note_d = Note(duration=1.0, pitch=62, delta=2.0)
    part.insert(note_d)

    # Add F4 at t=3
    note_f = Note(duration=1.0, pitch=65, delta=3.0)
    part.insert(note_f)

    notes = score.notes
    assert len(notes) == 5

    # First note (C4 at t=0)
    assert notes[0].pitch.keynum == 60
    assert notes[0].previous_note is None
    assert notes[0].next_note.pitch.keynum == 64

    # Second note (E4 at t=0)
    assert notes[1].pitch.keynum == 64
    assert notes[1].previous_note.pitch.keynum == 60
    assert notes[1].next_note.pitch.keynum == 67

    # Third note (G4 at t=0)
    assert notes[2].pitch.keynum == 67
    assert notes[2].previous_note.pitch.keynum == 64
    assert notes[2].next_note.pitch.keynum == 62

    # Fourth note (D4 at t=2)
    assert notes[3].pitch.keynum == 62
    assert notes[3].previous_note.pitch.keynum == 67
    assert notes[3].next_note.pitch.keynum == 65

    # Fifth note (F4 at t=3)
    assert notes[4].pitch.keynum == 65
    assert notes[4].previous_note.pitch.keynum == 62
    assert notes[4].next_note is None
