import pytest

from amads.core.basics import Note, Part, Score


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


def test_copy_score():
    score = Score.from_melody(pitches=[60, 62, 64], durations=1.0)
    copied_score = score.copy()

    copied_note = copied_score.content[0].content[0]
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
