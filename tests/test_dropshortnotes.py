from amads.algorithms.dropshortnotes import dropshortnotes
from amads.core.basics import Note, Part, Score


def test_dropshortnotes_basic():
    """Notes with (tied) duration <= threshold are removed."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=0.1, pitch=60)  # short
    Note(parent=part, onset=0.5, duration=0.5, pitch=62)  # kept
    Note(parent=part, onset=1.0, duration=1.0, pitch=64)  # kept

    result = dropshortnotes(score, threshold=0.25)
    notes = result.get_sorted_notes()

    assert len(notes) == 2
    assert notes[0].pitch.key_num == 62  # type: ignore
    assert notes[1].pitch.key_num == 64  # type: ignore


def test_dropshortnotes_grace_notes():
    """Threshold of 0 drops only zero-duration grace notes."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=0.0, pitch=60)  # grace note
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)  # kept

    result = dropshortnotes(score, threshold=0)
    notes = result.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].pitch.key_num == 62  # type: ignore


def test_dropshortnotes_threshold_is_exclusive():
    """Notes with (tied) duration exactly equal to threshold are kept."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=0.25, pitch=60)  # exactly 0.25, kept
    Note(parent=part, onset=1.0, duration=0.5, pitch=62)  # kept

    result = dropshortnotes(score, threshold=0.25)
    notes = result.get_sorted_notes()

    assert len(notes) == 2


def test_dropshortnotes_tied_chain():
    """A tied chain is evaluated by its total (tied) duration and removed entirely."""
    score = Score()
    part = Part(parent=score)

    # create a simple tie between 2 notes below threshold
    n1 = Note(parent=part, onset=0.0, duration=0.125, pitch=60)
    n2 = Note(parent=part, onset=0.125, duration=0.125, pitch=60)
    n1.tie = n2

    # create a chain of 3 notes below threshold
    n1 = Note(parent=part, onset=0.25, duration=0.1, pitch=62)
    n2 = Note(parent=part, onset=0.35, duration=0.1, pitch=62)
    n1.tie = n2
    n3 = Note(parent=part, onset=0.40, duration=0.05, pitch=62)
    n2.tie = n3

    # create a single note longer than the threshold
    Note(parent=part, onset=1.0, duration=1.0, pitch=64)  # kept

    result = dropshortnotes(score, threshold=0.3)
    notes = result.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].pitch.key_num == 64  # type: ignore


if __name__ == "__main__":
    test_dropshortnotes_basic()
    test_dropshortnotes_grace_notes()
    test_dropshortnotes_threshold_is_exclusive()
    test_dropshortnotes_tied_chain()
