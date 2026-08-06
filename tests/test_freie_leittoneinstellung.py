"""
test_freie_leittoneinstellung.py

Tests for
`freie_leittoneinstellung.is_freie_Leittoneinstellung`
and helpers.

Currently broadly mirrors doctests.
TODO expand
"""

import pytest

from amads.core.pitch import Pitch, PitchCollection
from amads.harmony.freie_leittoneinstellung import (
    SpellingRequirements,
    is_freie_Leittoneinstellung,
    pitch_string_to_pitch_collection,
)

# ---------------------------------------------------------------------------

# Literature examples (from the module docstring / Mozart 40 mvt. i, mm. 148-152)


class TestLiteratureExamples:
    def test_parallel_diminished_sevenths_excluded_by_default(self):
        """
        slice_1 is itself a (complete) diminished 7th,
        so it's excluded by the default `require_slice_1_not_common=True`.
        """
        assert not is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("B5 G#5 D5 E#4"),
            pitch_string_to_pitch_collection("C6 A5 E-5 F#4"),
        )

    def test_swapped_voicing_with_false_relation_is_true(self):
        """
        The G-F# false-relation voice,
        together with the highly dissonant slice_1,
        makes this a positive case.
        """
        assert is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("E-6 G#5 B4 G4"),
            pitch_string_to_pitch_collection("D6 A5 C5 F#4"),
        )

    def test_string_and_pitch_collection_inputs_agree(self):
        """
        The string convenience path and constructing a PitchCollection
        by hand should be interchangeable."""
        via_string = is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("E-6 G#5 B4 G4"),
            pitch_string_to_pitch_collection("D6 A5 C5 F#4"),
        )
        via_pitches = is_freie_Leittoneinstellung(
            PitchCollection(
                [Pitch("E-6"), Pitch("G#5"), Pitch("B4"), Pitch("G4")]
            ),
            PitchCollection(
                [Pitch("D6"), Pitch("A5"), Pitch("C5"), Pitch("F#4")]
            ),
        )
        via_bare_pitches = is_freie_Leittoneinstellung(
            [Pitch("E-6"), Pitch("G#5"), Pitch("B4"), Pitch("G4")],
            [Pitch("D6"), Pitch("A5"), Pitch("C5"), Pitch("F#4")],
        )
        assert via_string is True
        assert via_pitches is True
        assert via_bare_pitches is True


# ---------------------------------------------------------------------------

# Input coercion


class TestInputCoercion:
    def test_accepts_midi_numbers(self):
        """
        Bare MIDI numbers should work too, via `Pitch(...)` coercion,
        for callers who don't care about spelling at all.

        Here test same pitch classes/registers as the literature example,
        spelled/entered as plain integers instead of names.
        """
        slice_1 = [63, 68, 71, 67]  # E-6 G#5 B4 G4, as key_nums
        slice_2 = [62, 69, 72, 66]  # D6 A5 C5 F#4, as key_nums
        assert is_freie_Leittoneinstellung(slice_1, slice_2)


# ---------------------------------------------------------------------------

# min_distinct


class TestMinDistinct:
    def test_min_distinct_below_3_raises(self):
        with pytest.raises(ValueError):
            is_freie_Leittoneinstellung(
                pitch_string_to_pitch_collection("C4 E4 G4"),
                pitch_string_to_pitch_collection("C4 E4 G4"),
                min_distinct=2,
            )

    def test_fewer_than_min_distinct_pitch_classes_returns_false(self):
        """
        slice_1 has only 2 *distinct pitch classes*
        (C4 and C5 share a pitch class), even though it has 3 notes.

        This should count as 2, not 3,
        and so fail the default `min_distinct=3` requirement.
        """
        assert not is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 C5 E4"),
            pitch_string_to_pitch_collection("D4 F#4 A4"),
        )

    def test_min_distinct_counts_pitch_classes_not_notes(self):
        """
        A slice with 4 notes but only 3 distinct pitch classes
        (e.g., an octave doubling) is treated as num_distinct == 3,
        so quality checks run against the triad rules, not the seventh rules.

        Here, C4 E4 G4 C5 is a doubled C major triad, spelled with 4 notes.
        This should be excluded under defaults,
        because slice_1 counts as a (3-note) major triad,
        which require_slice_1_not_common rejects.

        """
        assert not is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 E4 G4 C5"),
            pitch_string_to_pitch_collection("D4 F#4 A4"),
        )


# ---------------------------------------------------------------------------

# require_slice_1_not_common / require_slice_2_common


class TestCommonChordRequirements:
    def test_slice_1_common_triad_excluded_by_default(self):
        assert not is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 E4 G4"),
            pitch_string_to_pitch_collection("C#4 F4 G#4"),
        )

    def test_slice_1_common_triad_allowed_when_disabled(self):
        assert is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 E4 G4"),
            pitch_string_to_pitch_collection("C#4 F4 G#4"),
            require_slice_1_not_common=False,
        )

    def test_slice_2_must_be_common_by_default(self):
        """slice_1 non-common (not a triad),
        but slice_2 is *also* non-common:
        should fail `require_slice_2_common`."""
        assert not is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 C#4 D4"),
            pitch_string_to_pitch_collection("C#4 D4 D#4"),
        )

    def test_slice_2_need_not_be_common_when_disabled(self):
        assert is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 C#4 D4"),
            pitch_string_to_pitch_collection("C#4 D4 D#4"),
            require_slice_2_common=False,
        )

    def test_augmented_and_diminished_count_as_common_triads(self):
        """
        TRIAD_QUALITIES includes augmented/diminished, not just major/minor.
        An augmented slice_1 should still be excluded by default."""
        assert not is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 E4 G#4"),
            pitch_string_to_pitch_collection("C#4 F4 A4"),
        )


# ---------------------------------------------------------------------------

# require_no_common_tone


class TestCommonTone:
    def test_shared_pitch_allowed_by_default(self):
        """
        `require_no_common_tone` defaults to False,
        so a shared pitch (same MIDI number in both slices)
        shouldn't by itself cause a rejection,
        as long as the step-size check still passes for every
        note."""
        # slice_2 keeps G4 in common with slice_1.
        result = is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 C#4 G4"),
            pitch_string_to_pitch_collection("C#4 D4 G4"),
            require_slice_2_common=False,
        )
        assert result

    def test_shared_pitch_rejected_when_required(self):
        result = is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 C#4 G4"),
            pitch_string_to_pitch_collection("C#4 D4 G4"),
            require_slice_2_common=False,
            require_no_common_tone=True,
        )
        assert not result


# ---------------------------------------------------------------------------

# max_step


class TestMaxStep:
    def test_note_beyond_max_step_rejected(self):
        """
        One note (D4 -> F4) moves by 3 semitones,
        beyond the default `max_step=1`."""
        assert not is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 C#4 D4"),
            pitch_string_to_pitch_collection("C#4 D4 F4"),
            require_slice_2_common=False,
        )

    def test_note_within_relaxed_max_step_allowed(self):
        assert is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("C4 C#4 D4"),
            pitch_string_to_pitch_collection("C#4 D4 F4"),
            require_slice_2_common=False,
            max_step=3,
        )


# ---------------------------------------------------------------------------

# spelling_requirements (stub)


class TestSpellingRequirementsStub:
    def test_default_is_permissive(self):
        assert is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("E-6 G#5 B4 G4"),
            pitch_string_to_pitch_collection("D6 A5 C5 F#4"),
        )

    def test_stub_check_always_true(self):
        sr = SpellingRequirements(
            require_slice_1_remote_spelling=True,
            require_simplest_resolution_spelling=True,
            max_alteration=0,
        )
        assert sr.check(
            pitch_string_to_pitch_collection("E-6 G#5 B4 G4"),
            pitch_string_to_pitch_collection("D6 A5 C5 F#4"),
        )
        assert is_freie_Leittoneinstellung(
            pitch_string_to_pitch_collection("E-6 G#5 B4 G4"),
            pitch_string_to_pitch_collection("D6 A5 C5 F#4"),
            spelling_requirements=sr,
        )
