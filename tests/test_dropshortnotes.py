from amads.algorithms.dropshortnotes import dropshortnotes
from amads.core.basics import Note, Part, Score


def test_dropshortnotes_basic():
    """Notes with tied_duration <= threshold are removed."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=0.1, pitch=60)  # short
    Note(parent=part, onset=0.5, duration=0.5, pitch=62)  # kept
    Note(parent=part, onset=1.0, duration=1.0, pitch=64)  # kept

    result = dropshortnotes(score, threshold=0.25)
    notes = result.get_sorted_notes()

    assert len(notes) == 2
    assert notes[0].pitch.key_num == 62
    assert notes[1].pitch.key_num == 64


def test_dropshortnotes_grace_notes():
    """Threshold of 0 drops only zero-duration grace notes."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=0.0, pitch=60)  # grace note
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)  # kept

    result = dropshortnotes(score, threshold=0)
    notes = result.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].pitch.key_num == 62


def test_dropshortnotes_threshold_is_inclusive():
    """Notes with tied_duration exactly equal to threshold are dropped."""
    score = Score()
    part = Part(parent=score)

    Note(
        parent=part, onset=0.0, duration=0.25, pitch=60
    )  # exactly 0.25 so dropped
    Note(parent=part, onset=1.0, duration=0.5, pitch=62)  # kept

    result = dropshortnotes(score, threshold=0.25)
    notes = result.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].pitch.key_num == 62


def test_dropshortnotes_tied_chain():
    """A tied chain is evaluated by its total tied_duration and removed entirely."""
    score = Score()
    part = Part(parent=score)

    n1 = Note(parent=part, onset=0.0, duration=0.125, pitch=60)
    n2 = Note(parent=part, onset=0.125, duration=0.125, pitch=60)
    n1.tie = n2
    Note(parent=part, onset=1.0, duration=1.0, pitch=64)  # kept

    result = dropshortnotes(score, threshold=0.25)
    notes = result.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].pitch.key_num == 64


if __name__ == "__main__":
    test_dropshortnotes_basic()
    test_dropshortnotes_grace_notes()
    test_dropshortnotes_threshold_is_inclusive()
    test_dropshortnotes_tied_chain()
