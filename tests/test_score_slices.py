"""
test_score_slices.py

Tests for `score_slices.py`.

Deliberately avoids depending on any bundled example score file.
Scores are built in-memory instead,
which also keeps these tests fast and fully offline.
"""

from amads.core.basics import Note, Part, Score
from amads.core.pitch import Pitch, PitchCollection
from amads.harmony.freie_leittoneinstellung import is_freie_Leittoneinstellung
from amads.harmony.score_slices import (
    get_score_slices,
    iter_slice_pair_collections,
    iter_slice_pair_strings,
    iter_slice_pairs,
    slice_to_pitch_collection,
    slice_to_pitch_string,
)


def _chord_part(pitch_names, onset: float, duration: float = 1.0) -> Part:
    """
    Build a `Part` containing one simultaneous chord
    (all notes share the same onset/duration),
    as a lightweight way to build vertical sonorities
    without a full multi-Part score.
    """
    part = Part(onset=onset)
    for name in pitch_names:
        Note(part, onset, duration, Pitch(name, accidental_chars="-#"))
    return part


def _two_chord_score() -> Score:
    """
    A minimal Score:
    one chord followed immediately by another, using the
    "E-6 G#5 B4 G4" -> "D6 A5 C5 F#4" literature example from
    `freie_leittoneinstellung`,
    so the expected `is_freie_Leittoneinstellung` result is already known.
    """
    part = Part(onset=0.0)
    for name in ["E-6", "G#5", "B4", "G4"]:
        Note(part, 0.0, 1.0, Pitch(name, accidental_chars="-#"))
    for name in ["D6", "A5", "C5", "F#4"]:
        Note(part, 1.0, 1.0, Pitch(name, accidental_chars="-#"))
    return Score(part)


class TestGetScoreSlices:
    def test_accepts_score_object_directly_no_io(self):
        """
        Passing an already-built Score should work with no file
        (this is the "default direct from score" path).
        """
        score = _two_chord_score()
        slices = get_score_slices(score)
        assert len(slices) == 2

    def test_slice_contents_round_trip_to_pitch_collection(self):
        score = _two_chord_score()
        slices = get_score_slices(score)
        first = slice_to_pitch_collection(slices[0])
        assert isinstance(first, PitchCollection)
        # `PitchCollection.pitch_name_multiset` always uses the "b#" default
        # hence "Eb6" here rather than the "-#"-style spelling used elsewhere.
        assert sorted(first.pitch_name_multiset) == sorted(
            ["Eb6", "G#5", "B4", "G4"]
        )


class TestIterSlicePairs:
    def test_pairs_are_consecutive(self):
        score = _two_chord_score()
        slices = get_score_slices(score)
        pairs = list(iter_slice_pairs(slices))
        assert len(pairs) == 1
        assert pairs[0] == (slices[0], slices[1])

    def test_pair_strings_match_literature_example(self):
        score = _two_chord_score()
        slices = get_score_slices(score)
        ((s1, s2),) = list(iter_slice_pair_strings(slices))
        assert sorted(s1.split()) == sorted("E-6 G#5 B4 G4".split())
        assert sorted(s2.split()) == sorted("D6 A5 C5 F#4".split())

    def test_pair_collections_feed_directly_into_the_rule(self):
        """
        End-to-end:
        Score
        -> slices
        -> PitchCollection pairs
        -> is_freie_Leittoneinstellung,
        with no string round-trip.
        """
        score = _two_chord_score()
        slices = get_score_slices(score)
        ((pc1, pc2),) = list(iter_slice_pair_collections(slices))
        assert isinstance(pc1, PitchCollection)
        assert isinstance(pc2, PitchCollection)
        assert is_freie_Leittoneinstellung(pc1, pc2)


class TestSliceToPitchString:
    def test_accepts_pitch_collection_too(self):
        """
        `slice_to_pitch_string`
        should also accept an already-converted `PitchCollection`,
        not just a raw `Slice`.
        """
        collection = PitchCollection([Pitch("C4"), Pitch("E4"), Pitch("G4")])
        assert slice_to_pitch_string(collection) == "C4 E4 G4"
