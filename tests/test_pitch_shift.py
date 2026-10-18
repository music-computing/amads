from amads.core.basics import Note, Score


def test_pitch_shift_simple():
    """Shift every note in a melody up by an octave."""
    score = Score.from_melody([60, 62, 64])
    score.pitch_shift(12)
    notes = score.get_sorted_notes()
    assert [note.midi_num for note in notes] == [72, 74, 76]


def test_pitch_shift_returns_self():
    """pitch_shift is in-place and returns the same Score object."""
    score = Score.from_melody([60, 62, 64])
    result = score.pitch_shift(12)
    assert result is score


def test_pitch_shift_tied_updates_all_heads():
    """Head and tied-to notes both change; ties are not merged."""
    score = Score.from_melody([60, 60])
    head, tied_to = list(score.find_all(Note, include_tied_to_notes=True))
    head.tie = tied_to
    score.pitch_shift(12)
    assert head.midi_num == 72
    assert tied_to.midi_num == 72
    assert head.tie is tied_to


def test_pitch_shift_skips_unpitched():
    """Unpitched notes stay None; pitched notes still shift."""
    score = Score.from_melody([60, 62])
    unpitched, pitched = list(score.find_all(Note, include_tied_to_notes=True))
    unpitched.pitch = None  # make this note unpitched
    score.pitch_shift(12)
    assert unpitched.pitch is None
    assert pitched.midi_num == 74


def test_pitch_shift_copy_does_not_mutate_original():
    """Copy then shift must not change the original."""
    score = Score.from_melody([60, 62, 64])
    copied = score.copy()
    copied.pitch_shift(12)
    original = [note.midi_num for note in score.get_sorted_notes()]
    shifted = [note.midi_num for note in copied.get_sorted_notes()]
    assert original == [60, 62, 64]
    assert shifted == [72, 74, 76]


def test_pitch_shift_preserves_alt():
    """pitch_shift copies alt, so F# becomes G# rather than Ab."""
    score = Score.from_melody(["F#4"])
    note = score.get_sorted_notes()[0]
    assert note.pitch is not None
    assert note.pitch.alt == 1
    score.pitch_shift(2)
    assert note.midi_num == 68
    assert note.pitch is not None
    assert note.pitch.alt == 1


def test_note_pitch_shift():
    """A bare Note can pitch_shift without an EventGroup."""
    note = Note(onset=0.0, duration=1.0, pitch=60)
    result = note.pitch_shift(12)
    assert result is note
    assert note.midi_num == 72
    assert note.onset == 0.0


def test_note_pitch_shift_unpitched():
    """A bare unpitched Note is left unchanged."""
    note = Note(onset=0.0, duration=1.0, pitch=None)
    result = note.pitch_shift(1)
    assert result is note
    assert note.pitch is None


def test_pitch_shift_empty_score():
    """An empty score returns self and does not raise."""
    score = Score.from_melody([])
    result = score.pitch_shift(12)
    assert result is score
