from amads.core.basics import Note, Score
from amads.pitch.key.transpose2c import transpose2c

C_MAJOR_SCALE_UP_SI_DOWN = [
    60,
    62,
    64,
    65,
    67,
    69,
    71,
    72,
    71,
    69,
    67,
    65,
    64,
    62,
    60,
]

G_MAJOR_SCALE = [67, 69, 71, 72, 74, 76, 78, 79]
C_NATURAL_MINOR_SCALE = [60, 62, 63, 65, 67, 68, 70, 72]


def test_transpose2c_empty_score():
    """An empty score returns a copy and does not raise."""
    score = Score.from_melody([])
    result = transpose2c(score)
    assert result is not score


def test_transpose2c_c_major_unchanged():
    """A C major scale stays on C; the input score is not mutated."""
    score = Score.from_melody(C_MAJOR_SCALE_UP_SI_DOWN)
    result = transpose2c(score)
    assert result is not score  # not the same object, new score object
    assert [note.midi_num for note in result.get_sorted_notes()] == (
        C_MAJOR_SCALE_UP_SI_DOWN
    )


def test_transpose2c_g_major_to_c():
    """A G major scale being shifted down to C."""
    score = Score.from_melody(G_MAJOR_SCALE)
    result = transpose2c(score)
    assert [note.midi_num for note in result.get_sorted_notes()] == [
        60,
        62,
        64,
        65,
        67,
        69,
        71,
        72,
    ]
    assert [
        note.midi_num for note in score.get_sorted_notes()
    ] == G_MAJOR_SCALE  # original score is not mutated


def test_transpose2c_tied_updates_all_heads():
    """Head and tied-to notes stay pitch-consistent after transpose."""
    score = Score.from_melody(
        [67, 67] + G_MAJOR_SCALE[1:]
    )  # G major scale including tied notes
    # making the tied score object
    head, tied_to, *_ = list(score.find_all(Note, include_tied_to_notes=True))
    head.tie = tied_to
    # transposing the score
    result = transpose2c(score)
    result_head, result_tied_to, *_ = list(
        result.find_all(Note, include_tied_to_notes=True)
    )
    assert result_head.midi_num == 60
    assert result_tied_to.midi_num == 60
    assert result_head.tie is result_tied_to
    assert head.midi_num == 67
    assert tied_to.midi_num == 67


def test_transpose2c_c_minor_does_not_drop_octave():
    """checking minor scale case"""
    score = Score.from_melody(C_NATURAL_MINOR_SCALE)
    result = transpose2c(score)
    assert [note.midi_num for note in result.get_sorted_notes()] == (
        C_NATURAL_MINOR_SCALE
    )
