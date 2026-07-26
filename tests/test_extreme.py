from amads.algorithms.extreme import extreme
from amads.core.basics import Note, Part, Score


def test_extreme_high():
    """Test that extreme('high') keeps the highest pitched note at each onset."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=1.0, pitch=60)  # C4
    Note(parent=part, onset=0.0, duration=1.0, pitch=64)  # E4 (highest)
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)  # D4
    Note(parent=part, onset=1.0, duration=1.0, pitch=67)  # G4 (only note)

    result = extreme(score, method="high")
    notes = result.get_sorted_notes()

    assert len(notes) == 2
    assert notes[0].pitch.key_num == 64
    assert notes[1].pitch.key_num == 67


def test_extreme_low():
    """Test that extreme('low') keeps the lowest pitched note at each onset."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=1.0, pitch=60)  # C4 (lowest)
    Note(parent=part, onset=0.0, duration=1.0, pitch=64)  # E4
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)  # D4
    Note(parent=part, onset=1.0, duration=1.0, pitch=67)  # G4 (only note)

    result = extreme(score, method="low")
    notes = result.get_sorted_notes()

    assert len(notes) == 2
    assert notes[0].pitch.key_num == 60
    assert notes[1].pitch.key_num == 67


def test_extreme_monophonic():
    """Test that a monophonic score is returned unchanged."""
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=1.0, pitch=60)
    Note(parent=part, onset=1.0, duration=1.0, pitch=62)
    Note(parent=part, onset=2.0, duration=1.0, pitch=64)

    result = extreme(score, method="high")
    notes = result.get_sorted_notes()

    assert len(notes) == 3
    assert [n.pitch.key_num for n in notes] == [60, 62, 64]


if __name__ == "__main__":
    test_extreme_high()
    test_extreme_low()
    test_extreme_monophonic()
