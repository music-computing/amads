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
    """trim uses shift_framework=True so tempo/TS moves with content."""
    n = Note(onset=4.0, duration=1.0, pitch="C4")
    score = Score(Part(n))
    score.time_map.append_change(4.0, 120.0)
    score.append_time_signature(TimeSignature(quarters=4.0, upper=3.0, lower=4))

    trimmed = trim(score)
    assert trimmed is not score
    assert trimmed.get_sorted_notes()[0].onset == 0.0
    assert trimmed.time_map.changes[1].quarter == 0.0
    assert trimmed.time_signatures[1].quarters == 0.0
    # original framework unchanged
    assert score.time_map.changes[1].quarter == 4.0
    assert score.time_signatures[1].quarters == 4.0


if __name__ == "__main__":
    test_trim()
