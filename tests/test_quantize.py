from amads.core.basics import Note, Part, Score
from amads.time.quantize import quantize


def test_quantize_basic():
    """Test standard quantize with default arguments (onset and duration grids match)"""
    score = Score()
    part = Part(parent=score)
    # create notes slightly off grid (grid = 8 implies 1/8 increments = 0.125)

    # Should quantize to 0.125 and 0.875
    Note(parent=part, onset=0.1, duration=0.9, pitch=60)
    # Should quantize to 1.0 and 0.25
    Note(parent=part, onset=1.05, duration=0.2, pitch=62)

    q_score = quantize(score, onset_divisions=8)
    notes = q_score.get_sorted_notes()

    assert notes[0].onset == 0.125
    assert notes[0].duration == 0.875
    assert notes[1].onset == 1.0
    assert notes[1].duration == 0.25


def test_quantize_separate_grids():
    """Test quantize with different onset and duration grids"""
    score = Score()
    part = Part(parent=score)

    # onset_divisions = 2 (0.5), dur_divisions = 4 (0.25)
    Note(parent=part, onset=0.4, duration=0.2, pitch=60)

    # onset rounds to 0.5, duration rounds to 0.25
    q_score = quantize(score, onset_divisions=2, dur_divisions=4)
    notes = q_score.get_sorted_notes()

    assert notes[0].onset == 0.5
    assert notes[0].duration == 0.25


def test_quantize_filterdiv():
    """Test quantize filtering out short notes"""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=1.0, pitch=60)
    Note(parent=part, onset=1.0, duration=0.1, pitch=62)  # short note

    # filter_divisions = 8 implies threshold = 0.125
    # the second note has duration 0.1 < 0.125, so it should be removed
    q_score = quantize(score, onset_divisions=4, filter_divisions=8)
    notes = q_score.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].pitch.key_num == 60


def test_tied():
    """Test that a tied chain collapses into one note with the total quantized duration."""
    score = Score()
    part = Part(parent=score)

    note_a = Note(parent=part, onset=0.0, duration=0.0, pitch=60)
    note_b = Note(parent=part, onset=0.0, duration=0.25, pitch=60)
    note_c = Note(parent=part, onset=0.25, duration=1.0, pitch=60)
    note_a.tie = note_b
    note_b.tie = note_c

    q_score = quantize(score, onset_divisions=4, dur_divisions=1)
    notes = q_score.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].duration == 1.0


def test_filter():
    """Test that filter=True removes zero-duration notes after quantization."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=1.0, pitch=60)
    Note(parent=part, onset=1.0, duration=0.0, pitch=62)

    q_score = quantize(score, onset_divisions=4, filter=True)
    notes = q_score.get_sorted_notes()

    assert len(notes) == 1
    assert notes[0].pitch.key_num == 60


if __name__ == "__main__":
    test_quantize_basic()
    test_quantize_separate_grids()
    test_quantize_filterdiv()
    test_tied()
    test_filter()
