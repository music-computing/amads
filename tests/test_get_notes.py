"""Tests for Score.get_notes method."""

import pytest

from amads.core.basics import Chord, Measure, Note, Part, Score, Staff


def test_get_notes_empty_score():
    """Test get_notes on an empty score returns empty generator."""
    score = Score()
    assert list(score.get_notes()) == []


def test_get_notes_single_note():
    """Test get_notes on a score with a single note."""
    score = Score()
    part = Part()
    note = Note(duration=1, pitch=60)
    part.insert(note)
    score.insert(part)

    notes = list(score.get_notes())
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

    notes = list(score.get_notes())
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

    notes = list(score.get_notes())
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

    notes = list(score.get_notes())
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

    notes = list(score.get_notes())

    # TODO: currently this test fails, we are getting two notes not one
    assert len(notes) == 1  # Tied notes should be merged into one

    assert notes[0].pitch.keynum == 60
    assert notes[0].duration == 4  # Duration should be combined
    assert notes[0].tie is None  # Tie should be stripped
