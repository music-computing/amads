import pytest

from amads.core.basics import Score


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


def test_flatten():
    """
    Test that calling score.flatten() does not change the part's parent.
    """
    score = Score.from_melody(pitches=[60, 62, 64], durations=1.0)

    part = score.content[0]
    assert part.parent == score

    score.flatten()

    part = score.content[0]
    assert part.parent == score
