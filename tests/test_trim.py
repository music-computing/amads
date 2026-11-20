from amads.algorithms.trim import trim
from amads.core.basics import Note, Part, Score, TimeSignature


def test_trim():
    """trim shifts so the first note starts at 0.0 without mutating input."""
    my_score = Score()
    my_part = Part(parent=my_score)

    Note(parent=my_part, onset=6.0, duration=1.0, pitch=60)
    Note(parent=my_part, onset=7.0, duration=1.0, pitch=10)
    Note(parent=my_part, onset=8.0, duration=2.0, pitch=20)

    trimmed_score = trim(my_score)
    notes = trimmed_score.get_sorted_notes()

    assert trimmed_score is not my_score
    assert trimmed_score.onset == 0.0
    assert trimmed_score.content[0].onset == 0.0

    assert notes[0].onset == 0.0
    assert notes[0].pitch.midi_num == 60
    assert notes[1].onset == 1.0
    assert notes[1].pitch.midi_num == 10
    assert notes[2].onset == 2.0
    assert notes[2].pitch.midi_num == 20

    original_notes = my_score.get_sorted_notes()
    assert original_notes[0].onset == 6.0


def test_trim_shifts_framework():
    """trim also moves time_map and time_signatures with the notes."""
    n = Note(onset=4.0, duration=1.0, pitch="C4")
    score = Score(Part(n))
    score.time_map.append_change(4.0, 120.0)
    score.append_time_signature(TimeSignature(quarters=4.0, upper=3.0, lower=4))

    trimmed = trim(score)
    assert trimmed is not score  # returns a copy, not the input
    assert trimmed.get_sorted_notes()[0].onset == 0.0  # leading silence removed

    assert len(trimmed.time_map.changes) == 1
    assert (
        trimmed.time_map.changes[0].quarter == 0.0
    )  # change now at score start
    assert trimmed.time_map.quarter_to_tempo(0.0) == 120.0  # tempo kept
    assert len(trimmed.time_signatures) == 1
    assert trimmed.time_signatures[0].quarters == 0.0
    assert trimmed.time_signatures[0].upper == 3.0  # still 3/4
    assert trimmed.time_signatures[0].lower == 4

    # Input score is unchanged
    assert score.time_map.changes[1].quarter == 4.0
    assert score.time_map.quarter_to_tempo(0.0) == 100.0
    assert score.time_signatures[1].quarters == 4.0
    assert score.time_signatures[1].upper == 3.0


if __name__ == "__main__":
    test_trim()
