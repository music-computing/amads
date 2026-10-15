"""
Tests for variability.py.

Unit tests cover the core numeric functions directly.
Integration tests exercise the Score-level wrappers
(score_npvi and score_npvi_by_part) using
programmatically constructed AMADS Score objects.

 We do not test file I/O here as that is handled in test_readscore
 (and requires network access).
"""

import math

import pytest

from amads.core.basics import Note, Part, Score
from amads.time.variability import (
    _iois_from_notes,
    isochrony_proportion,
    normalized_pairwise_calculation,
    normalized_pairwise_variability_index,
    pairwise_anisochronous_contrast_index,
    phrase_normalized_pairwise_variability_index,
    score_npvi,
    score_npvi_by_part,
)

# ---------------------------------------------------------------------------

# Helpers


def _make_monophonic_score(*onset_duration_pairs) -> Score:
    """Build a single-part monophonic Score from (onset, duration) pairs."""
    notes = [
        Note(onset=onset, duration=dur, pitch=60)
        for onset, dur in onset_duration_pairs
    ]
    return Score(Part(*notes))


def _make_two_part_score(part1_pairs, part2_pairs) -> Score:
    """Build a two-part Score from two lists of (onset, duration) pairs."""
    p1 = Part(*[Note(onset=o, duration=d, pitch=60) for o, d in part1_pairs])
    p2 = Part(
        *[Note(onset=o, duration=d, pitch=48) for o, d in part2_pairs],
        instrument="Bass",
    )
    return Score(p1, p2)


# ---------------------------------------------------------------------------

# _validate_inputs (tested indirectly via public functions)


class TestValidation:
    def test_too_few_durations(self):
        with pytest.raises(ValueError, match="at least 2"):
            normalized_pairwise_variability_index([1.0])

    def test_zero_duration(self):
        with pytest.raises(ValueError, match="positive"):
            normalized_pairwise_variability_index([1.0, 0.0, 1.0])

    def test_negative_duration(self):
        with pytest.raises(ValueError, match="positive"):
            normalized_pairwise_variability_index([1.0, -0.5, 1.0])

    def test_accepts_generator(self):
        """Iterable (not just list) input must work."""
        result = normalized_pairwise_variability_index(
            [x for x in [1.0, 2.0, 1.0]]
        )
        assert isinstance(result, float)


# ---------------------------------------------------------------------------

# normalized_pairwise_variability_index


class TestNPVI:
    def test_isochronous_is_zero(self):
        assert (
            normalized_pairwise_variability_index([1.0, 1.0, 1.0, 1.0]) == 0.0
        )

    def test_daniele_patel_appendix(self):
        """Example from Daniele & Patel (2013, Appendix)."""
        durs = [
            1.0,
            1 / 2,
            1 / 2,
            1.0,
            1 / 2,
            1 / 2,
            1 / 3,
            1 / 3,
            1 / 3,
            2.0,
            1 / 3,
            1 / 3,
            1 / 3,
            1 / 3,
            1 / 3,
            1 / 3,
            3 / 2,
            1.0,
            1 / 2,
        ]
        assert round(normalized_pairwise_variability_index(durs), 1) == 42.2

    def test_condit_schultz_figure2_a(self):
        durs = [0.25, 0.25, 0.25, 0.25, 1.0, 0.25, 0.25, 0.25, 0.25, 1.0]
        assert round(normalized_pairwise_variability_index(durs), 1) == 40.0

    def test_condit_schultz_figure2_b(self):
        durs = [0.25, 0.25, 0.5, 1.0, 0.25, 0.25, 0.5, 1.0]
        assert round(normalized_pairwise_variability_index(durs), 1) == 55.2

    def test_two_durations(self):
        """Minimum valid input: two durations."""
        result = normalized_pairwise_variability_index([1.0, 2.0])
        assert round(result, 2) == 66.67

    def test_symmetric(self):
        """nPVI([a, b]) == nPVI([b, a])."""
        a = normalized_pairwise_variability_index([1.0, 3.0])
        b = normalized_pairwise_variability_index([3.0, 1.0])
        assert math.isclose(a, b)


# ---------------------------------------------------------------------------

# normalized_pairwise_calculation


class TestNPC:
    def test_equal_durations(self):
        assert normalized_pairwise_calculation([1.0, 1.0]) == [0.0]

    def test_2_to_1_ratio(self):
        assert round(normalized_pairwise_calculation([1.0, 2.0])[0], 2) == 66.67

    def test_3_to_1_ratio(self):
        assert normalized_pairwise_calculation([1.0, 3.0]) == [100.0]

    def test_length(self):
        """Returns m-1 values for m durations."""
        result = normalized_pairwise_calculation([1.0, 2.0, 1.0, 2.0])
        assert len(result) == 3

    def test_npvi_is_mean_of_npc(self):
        """nPVI must equal the arithmetic mean of nPC values."""
        durs = [1.0, 2.0, 1.0, 0.5, 1.0]
        npcs = normalized_pairwise_calculation(durs)
        npvi = normalized_pairwise_variability_index(durs)
        assert math.isclose(npvi, sum(npcs) / len(npcs))


# ---------------------------------------------------------------------------

# isochrony_proportion


class TestIsochronyProportion:
    def test_fully_isochronous(self):
        assert isochrony_proportion([1.0, 1.0, 1.0, 1.0]) == 1.0

    def test_no_isochronous(self):
        assert isochrony_proportion([1.0, 2.0, 1.0, 2.0]) == 0.0

    def test_mixed(self):
        assert isochrony_proportion([1, 1, 2, 2, 1, 0.5]) == pytest.approx(0.4)

    def test_near_equal_within_tolerance(self):
        """Values within TINY (1e-4) of each other count as isochronous."""
        assert isochrony_proportion([1.0, 1.00005, 1.0]) == 1.0


# ---------------------------------------------------------------------------

# pairwise_anisochronous_contrast_index


class TestPACI:
    def test_all_isochronous_raises(self):
        with pytest.raises(ValueError, match="non-isochronous"):
            pairwise_anisochronous_contrast_index([1.0, 1.0, 1.0])

    def test_ignores_isochronous_pairs(self):
        """pACI should ignore the 1:1 pairs and only score the 2:1 pair."""
        # [1, 1, 2]: pairs are (1,1) isochronous, (1,2) non-isochronous
        result = pairwise_anisochronous_contrast_index([1.0, 1.0, 2.0])
        assert round(result, 2) == 66.67

    def test_no_isochronous_equals_npvi(self):
        """When there are no isochronous pairs, pACI == nPVI."""
        durs = [1.0, 2.0, 1.0, 2.0]
        paci = pairwise_anisochronous_contrast_index(durs)
        npvi = normalized_pairwise_variability_index(durs)
        assert math.isclose(paci, npvi)


# ---------------------------------------------------------------------------

# phrase_normalized_pairwise_variability_index


class TestPnNPVI:
    def test_no_boundaries_crossed_equals_npvi(self):
        """With a boundary placed after the sequence, pnNPVI == nPVI."""
        durs = [1.0, 2.0, 1.0, 2.0]
        npvi = normalized_pairwise_variability_index(durs)
        pnnpvi = phrase_normalized_pairwise_variability_index(durs, [999.0])
        assert math.isclose(npvi, pnnpvi)

    def test_all_pairs_cross_boundary_raises(self):
        with pytest.raises(ValueError, match="All pairs"):
            phrase_normalized_pairwise_variability_index([1.0, 2.0], [0.5])

    def test_boundary_excludes_straddling_pair(self):
        """A boundary inside the first pair's window should exclude that pair only.

        durs=[1, 1, 2]: pair windows are counter=[0,2] and counter=[1,4].
        A boundary at 0.5 falls in [0,2] but not in [1,4], so only the
        first (1,1) pair is excluded; the (1,2) pair is scored.
        """
        durs = [1.0, 1.0, 2.0]
        result = phrase_normalized_pairwise_variability_index(durs, [0.5])
        expected = normalized_pairwise_variability_index([1.0, 2.0])
        assert math.isclose(result, expected)


# ---------------------------------------------------------------------------

# _iois_from_notes


class TestIoisFromNotes:
    def test_basic(self):
        notes = [
            Note(onset=0.0, duration=1.0, pitch=60),
            Note(onset=1.0, duration=1.0, pitch=62),
            Note(onset=2.5, duration=0.5, pitch=64),
        ]
        assert _iois_from_notes(notes) == [1.0, 1.5]

    def test_zeros_removed(self):
        """Simultaneous onsets (chords in resultant rhythm) are filtered out."""
        notes = [
            Note(onset=0.0, duration=1.0, pitch=60),
            Note(onset=0.0, duration=1.0, pitch=64),  # simultaneous → zero diff
            Note(onset=1.0, duration=1.0, pitch=62),
        ]
        # The zero IOI between the two simultaneous notes is removed
        assert _iois_from_notes(notes) == [1.0]


# ---------------------------------------------------------------------------

# score_npvi


class TestScoreNPVI:
    def test_isochronous_score(self):
        """All equal IOIs → nPVI of 0."""
        score = _make_monophonic_score(
            (0.0, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0)
        )
        assert score_npvi(score) == 0.0

    def test_known_value(self):
        """Hand-verify against direct nPVI call on the same IOIs."""
        pairs = [(0.0, 1.0), (1.0, 0.5), (1.5, 1.0), (2.5, 0.5)]
        score = _make_monophonic_score(*pairs)
        onsets = [o for o, _ in pairs]
        iois = [onsets[i] - onsets[i - 1] for i in range(1, len(onsets))]
        expected = normalized_pairwise_variability_index(iois)
        assert math.isclose(score_npvi(score), expected)

    def test_two_part_resultant(self):
        """score_npvi merges all parts; result is based on combined onset stream."""
        score = _make_two_part_score(
            [(0.0, 1.0), (2.0, 1.0)],  # part 1 onsets: 0, 2
            [(1.0, 1.0), (3.0, 1.0)],  # part 2 onsets: 1, 3
        )
        # Resultant IOIs: [1, 1, 1] → nPVI = 0
        assert score_npvi(score) == 0.0

    def test_polyphonic_score_chord_then_note(self):
        """score_npvi on a score with a chord followed by a note uses the
        resultant onsets; simultaneous notes contribute a zero IOI that is
        filtered, leaving a valid sequence."""
        # Two notes at onset 0, one at onset 1 and one at onset 2 → IOIs [1, 1]
        nc1 = Note(onset=0.0, duration=1.0, pitch=60)
        nc2 = Note(onset=0.0, duration=1.0, pitch=64)  # simultaneous
        nc3 = Note(onset=1.0, duration=1.0, pitch=62)
        nc4 = Note(onset=2.0, duration=1.0, pitch=65)
        score = Score(Part(nc1, nc2, nc3, nc4))
        # Resultant IOIs after zero-filter: [1.0, 1.0] → nPVI = 0
        assert score_npvi(score) == 0.0


# ---------------------------------------------------------------------------

# score_npvi_by_part


class TestScoreNPVIByPart:
    def test_single_part_returns_one_entry(self):
        score = _make_monophonic_score(
            (0.0, 1.0), (1.0, 0.5), (1.5, 1.0), (2.5, 0.5)
        )
        result = score_npvi_by_part(score)
        assert len(result) == 1

    def test_single_part_matches_direct_npvi(self):
        pairs = [(0.0, 1.0), (1.0, 0.5), (1.5, 1.0), (2.5, 0.5)]
        score = _make_monophonic_score(*pairs)
        onsets = [o for o, _ in pairs]
        iois = [onsets[i] - onsets[i - 1] for i in range(1, len(onsets))]
        expected = normalized_pairwise_variability_index(iois)
        (value,) = score_npvi_by_part(score).values()
        assert math.isclose(value, expected)

    def test_two_parts_returns_two_entries(self):
        score = _make_two_part_score(
            [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)],
            [(0.0, 0.5), (0.5, 0.5), (1.0, 1.0)],
        )
        result = score_npvi_by_part(score)
        assert len(result) == 2

    def test_part_keyed_by_instrument(self):
        score = _make_two_part_score(
            [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)],
            [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)],
        )
        result = score_npvi_by_part(score)
        assert "Bass" in result

    def test_polyphonic_raises(self):
        """Chords in any part must raise ValueError."""
        nc1 = Note(onset=0.0, duration=1.0, pitch=60)
        nc2 = Note(onset=0.0, duration=1.0, pitch=64)  # chord
        nc3 = Note(onset=1.0, duration=1.0, pitch=62)
        score = Score(Part(nc1, nc2, nc3))
        with pytest.raises(ValueError, match="monophonic"):
            score_npvi_by_part(score)

    def test_isochronous_parts_are_zero(self):
        score = _make_two_part_score(
            [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)],
            [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)],
        )
        for value in score_npvi_by_part(score).values():
            assert value == 0.0
