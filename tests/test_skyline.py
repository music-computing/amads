from amads.core.basics import Note, Part, Score
from amads.polyphony.extreme import extreme
from amads.polyphony.superlative import superlative

# from amads.polyphony.skyline import skyline # TODO


def test_extreme():
    """Test that extreme('high') and extreme('low') keeps the highest/lowest pitched note at each onset."""
    score = Score()
    part = Part(parent=score)

    Note(
        parent=part, onset=0.0, duration=1.0, pitch=60
    )  # C4 lowest at onset 0.0 (and overall)
    Note(
        parent=part, onset=0.0, duration=1.0, pitch=64
    )  # E4 highest at onset 0.0
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)  # D4
    Note(parent=part, onset=1.0, duration=1.0, pitch=67)  # G4 only note at 1.0

    high_result = extreme(score, method="high")
    high_notes = high_result.get_sorted_notes()

    assert len(high_notes) == 2
    assert high_notes[0].pitch.midi_num == 64
    assert high_notes[1].pitch.midi_num == 67

    low_result = extreme(score, method="low")
    low_notes = low_result.get_sorted_notes()

    assert len(low_notes) == 2
    assert low_notes[0].pitch.midi_num == 60
    assert low_notes[1].pitch.midi_num == 67


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
    assert [n.pitch.midi_num for n in notes] == [60, 62, 64]


def test_superlative():
    """
    Basic test of extreme 'high' and 'low' from dummy example.
    """
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=1.0, pitch=60)  # C4
    Note(parent=part, onset=0.0, duration=1.0, pitch=64)  # E4
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)  # D4
    Note(parent=part, onset=1.0, duration=1.0, pitch=67)  # G4

    assert superlative(score, attribute="high") == 67
    assert superlative(score, attribute="low") == 60
