from amads.algorithms.trim import trim
from amads.core.basics import Note, Part, Score


def test_trim():
    """Test that the trim function correctly shifts the score so the first note starts at 0.0"""

    # Setup our test data
    my_score = Score()
    my_part = Part(parent=my_score)

    Note(parent=my_part, onset=6.0, duration=1.0, pitch=60)
    Note(parent=my_part, onset=7.0, duration=1.0, pitch=10)
    Note(parent=my_part, onset=8.0, duration=2.0, pitch=20)

    # Run trim() function
    trimmed_score = trim(my_score)
    notes = trimmed_score.get_sorted_notes()

    # Verify the results using assert
    assert trimmed_score.onset == 0.0
    assert trimmed_score.content[0].onset == 0.0  # part should start at 0.0 too

    # The first note should now be at 0.0
    assert notes[0].onset == 0.0
    assert notes[0].pitch.key_num == 60

    # The second note should be at 1.0
    assert notes[1].onset == 1.0
    assert notes[1].pitch.key_num == 10

    # The third note should be at 2.0
    assert notes[2].onset == 2.0
    assert notes[2].pitch.key_num == 20

    # The original score should be unchanged
    original_notes = my_score.get_sorted_notes()
    assert original_notes[0].onset == 6.0


if __name__ == "__main__":
    test_trim()
