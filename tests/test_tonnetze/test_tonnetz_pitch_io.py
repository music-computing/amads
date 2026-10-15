import pytest

from amads.core.basics import Chord, Note
from amads.core.pitch import Pitch, PitchCollection
from amads.harmony.tonnetze._pitch_io import (
    load_pitch_multiset,
    pitch_class_set,
    transform_pitch_multiset,
)


def test_load_pitch_multiset_from_list():
    """A plain list of MIDI pitches passes through unchanged, order and all."""
    assert load_pitch_multiset([60, 64, 67]) == (60, 64, 67)


def test_load_pitch_multiset_preserves_duplicates_and_octave():
    """Octave placement and duplicate pitches must not be collapsed."""
    assert load_pitch_multiset([60, 60, 72]) == (60, 60, 72)


def test_load_pitch_multiset_from_chord():
    """A Chord's Note pitches are read out as key numbers, in Chord order."""
    chord = Chord(Note(pitch=60), Note(pitch=64), Note(pitch=67))
    assert load_pitch_multiset(chord) == (60, 64, 67)


def test_load_pitch_multiset_from_pitch_collection_preserves_octave():
    """A PitchCollection must be read via pitch_num_multiset, not pitch_class_multiset,
    or octave information silently disappears."""
    pitches = PitchCollection([Pitch(x) for x in ["D4", "F4", "A4"]])
    result = load_pitch_multiset(pitches)
    assert result == (62, 65, 69)
    assert (
        max(result) > 11
    )  # regression check: these are key numbers, not bare pitch classes


def test_load_pitch_multiset_rejects_bad_type():
    """Only List[int], Chord and PitchCollection are accepted."""
    with pytest.raises(TypeError):
        load_pitch_multiset("not a chord")


def test_load_pitch_multiset_rejects_empty():
    """An empty chord is not a valid input."""
    with pytest.raises(ValueError):
        load_pitch_multiset([])


def test_load_pitch_multiset_rejects_negative():
    """Negative pitch numbers are not valid MIDI key numbers."""
    with pytest.raises(ValueError):
        load_pitch_multiset([-1, 60, 64])


def test_pitch_class_set_reduces_modulo_12():
    """Pitch class set collapses octaves and removes duplicates."""
    assert pitch_class_set((60, 64, 67, 72)) == frozenset({0, 4, 7})


def test_transform_pitch_multiset_shifts_only_matching_pitch_class():
    """Only pitches matching the target pitch class are shifted, others untouched."""
    assert transform_pitch_multiset((60, 64, 67), 0, -1) == (59, 64, 67)


def test_transform_pitch_multiset_shifts_all_octaves_of_matching_class():
    """Every occurrence of the matching pitch class shifts, regardless of octave."""
    assert transform_pitch_multiset((60, 64, 67, 72), 0, -1) == (59, 64, 67, 71)


def test_transform_pitch_multiset_bare_pitch_class_wraps():
    """A bare pitch class 0-11 wraps modulo 12, rather than going negative."""
    assert transform_pitch_multiset((0, 4, 7), 0, -1) == (11, 4, 7)


def test_transform_pitch_multiset_midi_num_does_not_wrap():
    """A full key number is shifted directly, without wrapping modulo 12."""
    assert transform_pitch_multiset((60, 64, 67), 0, 2) == (62, 64, 67)
