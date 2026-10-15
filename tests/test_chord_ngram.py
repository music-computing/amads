"""
test_chord_ngram.py
--------------------

Pytest suite for `chord_ngram.py`.

Covers:

1. construction / input validation
2. order groups (Ø, R, C, D, P) in isolation
3. content groups ("", I, K, IK) in isolation
4. equivalence-relation properties (reflexive, symmetric, transitive) of
   `ChordNgram.__eq__` for a representative sample of regimes
5. the specific semantics claimed in the module docstring
   (retrograde reverses, rotation cycles, permutation is order-blind, ...)
6. `order_group_size` against hand-computed values,
7. the `coarsen` lattice (valid moves succeed, invalid moves raise)
8. hashing / use in sets and dicts
9. that the n = 2 case exactly reproduces `ChordBigram`'s partition.
"""

import itertools

import pytest

from amads.core.chord import Chord
from amads.harmony.chord_bigram import ChordBigram
from amads.harmony.chord_ngram import (
    _CONTENT_GROUPS,
    _ORDER_GROUPS,
    EQUIVALENCES,
    ChordNgram,
)

# ---------------------------------------------------------------------------

# Fixtures / shared test data


def chord(pc, quality="major"):
    return Chord(pc, quality)


C, Cis, D, Dsh, E, F, Fsh, G, Gsh, A, Ash, B = (chord(pc) for pc in range(12))
Cm, Em, Gm, Am, Fm = (
    chord(0, "minor"),
    chord(4, "minor"),
    chord(7, "minor"),
    chord(9, "minor"),
    chord(5, "minor"),
)


@pytest.fixture
def triad_progression():
    """A 3-chord succession of distinct, non-periodic chords."""
    return [C, E, G]


@pytest.fixture
def tetra_progression():
    """A 4-chord succession of distinct, non-periodic chords."""
    return [C, E, G, A]


# ---------------------------------------------------------------------------

# EQUIVALENCES table


class TestEquivalenceTable:
    def test_twenty_regimes(self):
        assert len(EQUIVALENCES) == 20

    def test_all_labels_unique_and_string(self):
        assert len(EQUIVALENCES) == len(set(EQUIVALENCES))
        assert all(isinstance(e, str) for e in EQUIVALENCES)

    @pytest.mark.parametrize(
        "label",
        [
            "Ø",
            "R",
            "C",
            "D",
            "P",
            "I",
            "IR",
            "IC",
            "ID",
            "IP",
            "K",
            "KR",
            "KC",
            "KD",
            "KP",
            "IK",
            "IKR",
            "IKC",
            "IKD",
            "IKP",
        ],
    )
    def test_expected_labels_present(self, label):
        assert label in EQUIVALENCES


# ---------------------------------------------------------------------------

# Construction / validation


class TestConstruction:
    def test_requires_at_least_two_chords(self):
        with pytest.raises(ValueError):
            ChordNgram([C], "Ø")

    def test_empty_list_rejected(self):
        with pytest.raises(ValueError):
            ChordNgram([], "Ø")

    def test_two_chords_allowed(self):
        ng = ChordNgram([C, E], "Ø")
        assert ng.n == 2

    def test_invalid_equivalence_label_rejected(self):
        with pytest.raises(ValueError):
            ChordNgram([C, E, G], "ZZ")

    def test_default_equivalence_is_identity(self):
        ng = ChordNgram([C, E, G])
        assert ng.equivalence == "Ø"

    @pytest.mark.parametrize("label", sorted(EQUIVALENCES))
    def test_every_regime_constructs_without_error(
        self, label, triad_progression
    ):
        ng = ChordNgram(triad_progression, label)
        assert ng.equivalence == label
        assert isinstance(ng.canonical, tuple)


# ---------------------------------------------------------------------------

# Order groups (structural properties, independent of ChordNgram)


class TestOrderGroups:
    @pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
    def test_identity_group_size(self, n):
        assert len(_ORDER_GROUPS["Ø"](n)) == 1

    @pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
    def test_retrograde_group_size(self, n):
        assert len(_ORDER_GROUPS["R"](n)) == 2

    @pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
    def test_rotation_group_size(self, n):
        assert len(_ORDER_GROUPS["C"](n)) == n

    @pytest.mark.parametrize("n", [3, 4, 5, 6])
    def test_dihedral_group_size(self, n):
        assert len(_ORDER_GROUPS["D"](n)) == 2 * n

    @pytest.mark.parametrize("n", [2, 3, 4, 5])
    def test_permutation_group_size(self, n):
        import math

        assert len(_ORDER_GROUPS["P"](n)) == math.factorial(n)

    def test_permutation_group_rejects_large_n(self):
        with pytest.raises(ValueError):
            _ORDER_GROUPS["P"](9)

    def test_rotation_matches_docstring_example(self):
        # ABC -> BCA -> CAB
        perms = _ORDER_GROUPS["C"](3)
        seq = ("A", "B", "C")
        rotated = [tuple(seq[i] for i in p) for p in perms]
        assert ("A", "B", "C") in rotated
        assert ("B", "C", "A") in rotated
        assert ("C", "A", "B") in rotated

    def test_retrograde_group_is_involution(self):
        perms = _ORDER_GROUPS["R"](4)
        # applying the non-identity element twice returns the identity perm
        identity = tuple(range(4))
        non_identity = [p for p in perms if p != identity][0]
        twice = tuple(non_identity[i] for i in non_identity)
        assert twice == identity

    def test_dihedral_contains_rotation_and_retrograde(self):
        n = 4
        dihedral = set(_ORDER_GROUPS["D"](n))
        rotation = set(_ORDER_GROUPS["C"](n))
        retrograde = set(_ORDER_GROUPS["R"](n))
        assert rotation <= dihedral
        assert retrograde <= dihedral


# ---------------------------------------------------------------------------

# Content groups


class TestContentGroups:
    def test_none_group_is_singleton(self):
        seq = ((0, "major"), (4, "major"))
        assert _CONTENT_GROUPS[""](seq) == [seq]

    def test_inversion_group_flips_every_chord_together(self):
        seq = ((0, "major"), (4, "minor"))
        variants = _CONTENT_GROUPS["I"](seq)
        assert seq in variants
        assert ((0, "minor"), (4, "major")) in variants
        assert len(variants) == 2

    def test_inversion_does_not_flip_only_one_chord(self):
        seq = ((0, "major"), (4, "major"))
        variants = _CONTENT_GROUPS["I"](seq)
        assert ((0, "minor"), (4, "major")) not in variants

    def test_key_group_has_twelve_transpositions(self):
        seq = ((0, "major"), (4, "major"))
        variants = _CONTENT_GROUPS["K"](seq)
        assert len(variants) == 12
        assert seq in variants
        assert ((7, "major"), (11, "major")) in variants  # transpose by 7

    def test_flip_rejects_invalid_quality(self):
        from amads.harmony.chord_ngram import _flip

        with pytest.raises(ValueError):
            _flip("diminished")

    def test_key_group_preserves_relative_intervals(self):
        seq = ((0, "major"), (4, "major"), (7, "major"))
        for variant in _CONTENT_GROUPS["K"](seq):
            pcs = [pc for pc, _ in variant]
            assert (pcs[1] - pcs[0]) % 12 == 4
            assert (pcs[2] - pcs[0]) % 12 == 7

    def test_inversion_key_group_size(self):
        seq = ((0, "major"), (4, "major"))
        assert len(_CONTENT_GROUPS["IK"](seq)) == 24


# ---------------------------------------------------------------------------

# Equivalence-relation properties of ChordNgram.__eq__


REPRESENTATIVE_REGIMES = ["Ø", "R", "C", "D", "P", "I", "K", "IK", "IKR", "IKP"]


class TestEquivalenceRelationProperties:
    @pytest.mark.parametrize("regime", REPRESENTATIVE_REGIMES)
    def test_reflexive(self, regime, tetra_progression):
        ng = ChordNgram(tetra_progression, regime)
        assert ng == ng

    @pytest.mark.parametrize("regime", REPRESENTATIVE_REGIMES)
    def test_symmetric(self, regime, tetra_progression):
        a = ChordNgram(tetra_progression, regime)
        b = ChordNgram(list(reversed(tetra_progression)), regime)
        assert (a == b) == (b == a)

    @pytest.mark.parametrize("regime", REPRESENTATIVE_REGIMES)
    def test_transitive(self, regime):
        perms = list(itertools.permutations([C, E, G, A]))
        seqs = [ChordNgram(list(p), regime) for p in perms]
        for a, b, c in itertools.islice(itertools.product(seqs, repeat=3), 500):
            if a == b and b == c:
                assert a == c

    def test_not_equal_to_non_ngram(self):
        ng = ChordNgram([C, E], "Ø")
        assert (ng == "not a ChordNgram") is False
        assert ng != 42

    def test_different_regimes_are_not_equal_even_with_same_chords(self):
        a = ChordNgram([C, E, G], "Ø")
        b = ChordNgram([C, E, G], "R")
        assert a != b


# ---------------------------------------------------------------------------

# Semantics: order axis


class TestOrderSemantics:
    def test_identity_requires_exact_order(self, triad_progression):
        exact = ChordNgram(triad_progression, "Ø")
        reordered = ChordNgram([G, E, C], "Ø")
        assert exact != reordered
        assert exact == ChordNgram(list(triad_progression), "Ø")

    def test_retrograde_matches_exact_reverse_only(self, triad_progression):
        forward = ChordNgram(triad_progression, "R")
        reverse = ChordNgram([G, E, C], "R")
        rotated = ChordNgram([E, G, C], "R")
        assert forward == reverse
        assert forward != rotated

    def test_rotation_matches_cyclic_shifts_only(self, triad_progression):
        forward = ChordNgram(triad_progression, "C")
        rot1 = ChordNgram([E, G, C], "C")
        rot2 = ChordNgram([G, C, E], "C")
        non_cyclic = ChordNgram([C, G, E], "C")
        assert forward == rot1 == rot2
        assert forward != non_cyclic

    def test_dihedral_matches_rotations_of_the_retrograde_too(
        self, triad_progression
    ):
        forward = ChordNgram(triad_progression, "D")
        rotated_retrograde = ChordNgram(
            [G, C, E], "D"
        )  # rotation of C,E,G reversed (G,E,C)
        assert forward == rotated_retrograde

    def test_permutation_is_order_blind(self, triad_progression):
        forward = ChordNgram(triad_progression, "P")
        for perm in itertools.permutations(triad_progression):
            assert forward == ChordNgram(list(perm), "P")

    def test_two_chords_collapse_R_C_D_P(self):
        forms = {
            regime: ChordNgram([C, E], regime).canonical
            for regime in ("R", "C", "D", "P")
        }
        assert len(set(forms.values())) == 1


# ---------------------------------------------------------------------------

# Semantics: content axis


class TestContentSemantics:
    def test_inversion_flips_all_qualities_together(self, triad_progression):
        original = ChordNgram(triad_progression, "I")
        all_flipped = ChordNgram([Cm, Em, Gm], "I")
        assert original == all_flipped

    def test_inversion_rejects_partial_flip(self, triad_progression):
        original = ChordNgram(triad_progression, "I")
        partially_flipped = ChordNgram([Cm, E, G], "I")
        assert original != partially_flipped

    def test_key_equivalence_transposition_invariant(self, triad_progression):
        original = ChordNgram(triad_progression, "K")
        transposed = ChordNgram(
            [A, Cis, E], "K"
        )  # up a major 6th (9 semitones)
        assert original == transposed

    def test_key_equivalence_rejects_wrong_transposition(
        self, triad_progression
    ):
        original = ChordNgram(triad_progression, "K")
        wrong = ChordNgram([A, Cis, F], "K")  # not a consistent transposition
        assert original != wrong

    def test_combined_ik_regime(self, triad_progression):
        original = ChordNgram(triad_progression, "IK")
        transposed_and_flipped = ChordNgram([Fm, Am, Cm], "IK")
        assert original == transposed_and_flipped


# ---------------------------------------------------------------------------

# order_group_size


class TestOrderGroupSize:
    def test_all_distinct_tetragram(self, tetra_progression):
        sizes = {
            regime: ChordNgram(tetra_progression, regime).order_group_size
            for regime in ("Ø", "R", "C", "D", "P")
        }
        assert sizes == {"Ø": 1, "R": 2, "C": 4, "D": 8, "P": 24}

    def test_periodic_abab_reduces_rotation_count(self):
        seq = [C, E, C, E]
        assert ChordNgram(seq, "C").order_group_size == 2  # not 4
        assert ChordNgram(seq, "P").order_group_size == 6  # 4! / (2! 2!)

    def test_all_identical_chords_collapses_to_one(self):
        seq = [C, C, C, C]
        for regime in ("Ø", "R", "C", "D", "P"):
            assert ChordNgram(seq, regime).order_group_size == 1

    def test_palindrome_is_a_fixed_point_of_retrograde(self):
        seq = [C, E, G, E, C]
        assert ChordNgram(seq, "R").order_group_size == 1

    def test_order_group_size_never_exceeds_theoretical_max(
        self, tetra_progression
    ):
        import math

        n = len(tetra_progression)
        maxima = {"Ø": 1, "R": 2, "C": n, "D": 2 * n, "P": math.factorial(n)}
        for regime, cap in maxima.items():
            assert ChordNgram(tetra_progression, regime).order_group_size <= cap


# ---------------------------------------------------------------------------

# coarsen()


class TestCoarsen:
    def test_coarsen_to_self_is_a_noop(self, triad_progression):
        ng = ChordNgram(triad_progression, "R")
        coarsened = ng.coarsen("R")
        assert coarsened == ng

    def test_content_axis_valid_coarsening(self, triad_progression):
        ng = ChordNgram(triad_progression, "Ø")
        assert ng.coarsen("I").equivalence == "I"
        assert ng.coarsen("K").equivalence == "K"
        assert ng.coarsen("IK").equivalence == "IK"

    def test_order_axis_valid_coarsening(self, triad_progression):
        ng = ChordNgram(triad_progression, "Ø")
        assert ng.coarsen("R").equivalence == "R"
        assert ng.coarsen("C").equivalence == "C"
        assert ng.coarsen("D").equivalence == "D"
        assert ng.coarsen("P").equivalence == "P"

    def test_combined_axis_valid_coarsening(self, triad_progression):
        ng = ChordNgram(triad_progression, "R")
        assert ng.coarsen("IKD").equivalence == "IKD"

    def test_cannot_coarsen_order_sideways(self, triad_progression):
        # R and C are incomparable (neither is a subset of the other)
        ng = ChordNgram(triad_progression, "R")
        with pytest.raises(ValueError):
            ng.coarsen("C")

    def test_cannot_coarsen_to_a_finer_content_regime(self, triad_progression):
        ng = ChordNgram(triad_progression, "IK")
        with pytest.raises(ValueError):
            ng.coarsen("I")

    def test_cannot_coarsen_to_a_finer_order_regime(self, triad_progression):
        ng = ChordNgram(triad_progression, "P")
        with pytest.raises(ValueError):
            ng.coarsen("D")

    def test_coarsen_rejects_invalid_label(self, triad_progression):
        ng = ChordNgram(triad_progression, "Ø")
        with pytest.raises(ValueError):
            ng.coarsen("ZZ")

    def test_coarsened_result_agrees_with_direct_construction(
        self, triad_progression
    ):
        ng = ChordNgram(triad_progression, "R")
        assert ng.coarsen("P") == ChordNgram(triad_progression, "P")


# ---------------------------------------------------------------------------

# labels property


class TestLabelsProperty:
    def test_includes_self(self, triad_progression):
        ng = ChordNgram(triad_progression, "R")
        assert "R" in ng.labels

    def test_includes_fully_coarsened_regime(self, triad_progression):
        ng = ChordNgram(triad_progression, "R")
        assert "IKP" in ng.labels

    def test_excludes_incomparable_regime(self, triad_progression):
        ng = ChordNgram(triad_progression, "R")
        assert "C" not in ng.labels

    def test_identity_regime_reaches_everything(self, triad_progression):
        ng = ChordNgram(triad_progression, "Ø")
        assert set(ng.labels) == EQUIVALENCES


# ---------------------------------------------------------------------------

# label / repr / str / hash


class TestDisplayAndHashing:
    def test_label_contains_equivalence_code(self, triad_progression):
        ng = ChordNgram(triad_progression, "IKD")
        assert ng.equivalence in ng.label

    def test_str_matches_label(self, triad_progression):
        ng = ChordNgram(triad_progression, "R")
        assert str(ng) == ng.label

    def test_repr_contains_class_name_and_regime(self, triad_progression):
        ng = ChordNgram(triad_progression, "R")
        assert "ChordNgram" in repr(ng)
        assert "R" in repr(ng)

    def test_label_rejects_invalid_quality(self):
        from amads.harmony.chord_ngram import _q

        with pytest.raises(ValueError):
            _q("diminished")

    def test_equal_objects_have_equal_hash(self, triad_progression):
        a = ChordNgram(triad_progression, "C")
        b = ChordNgram([E, G, C], "C")  # a rotation
        assert a == b
        assert hash(a) == hash(b)

    def test_usable_as_set_members_collapses_equivalents(
        self, triad_progression
    ):
        rotations = [
            ChordNgram([C, E, G], "C"),
            ChordNgram([E, G, C], "C"),
            ChordNgram([G, C, E], "C"),
        ]
        assert len(set(rotations)) == 1

    def test_usable_as_dict_keys(self, triad_progression):
        d = {ChordNgram(triad_progression, "P"): "seed"}
        lookup_key = ChordNgram([G, C, E], "P")
        assert d[lookup_key] == "seed"


# ---------------------------------------------------------------------------

# n = 2 cross-check against ChordBigram


ALL_MAJOR_MINOR_CHORDS = [
    Chord(pc, q) for pc in range(12) for q in ("major", "minor")
]


class TestBigramCrossCheck:
    """
    ChordNgram's order axis collapses to a single non-trivial option (R)
    when n = 2, matching ChordBigram's original 'R' semantics exactly.
    ChordNgram's content axis ("", I, K, IK) is unchanged from
    ChordBigram, so the two modules should partition bigram-space
    identically for every regime ChordBigram supports.
    """

    @pytest.mark.parametrize(
        "bigram_regime,ngram_regime",
        [
            ("Ø", "Ø"),
            ("I", "I"),
            ("K", "K"),
            ("IK", "IK"),
            ("R", "R"),
            ("IR", "IR"),
            ("RK", "KR"),
            ("IRK", "IKR"),
        ],
    )
    def test_partition_matches(self, bigram_regime, ngram_regime):
        sample = ALL_MAJOR_MINOR_CHORDS[::3]  # 8 chords, keeps the test fast
        for a, b in itertools.combinations(sample, 2):
            for c, d in itertools.combinations(sample, 2):
                bg1 = ChordBigram(a, b, bigram_regime, key_pitch_class=0)
                bg2 = ChordBigram(c, d, bigram_regime, key_pitch_class=0)
                ng1 = ChordNgram([a, b], ngram_regime)
                ng2 = ChordNgram([c, d], ngram_regime)
                assert (bg1 == bg2) == (ng1 == ng2)

    def test_IR_no_longer_transposition_invariant(self):
        """
        Regression test for a fixed upstream bug: chord_bigram.py's 'IR'
        canonicalisation used to reduce to a single directed-interval
        value (min of the two directions), which made it accidentally
        transposition-invariant -- i.e. it behaved like 'IRK' rather
        than 'IR'. It has been fixed to keep the unordered *pair of
        absolute pitch classes* (mirroring plain 'R'), so a bare
        transposition is no longer treated as IR-equivalent.
        """
        a = ChordBigram(
            Chord(0, "major"), Chord(3, "minor"), "IR", key_pitch_class=0
        )
        b = ChordBigram(
            Chord(5, "major"), Chord(8, "minor"), "IR", key_pitch_class=0
        )
        assert a != b

        ng_a = ChordNgram([Chord(0, "major"), Chord(3, "minor")], "IR")
        ng_b = ChordNgram([Chord(5, "major"), Chord(8, "minor")], "IR")
        assert ng_a != ng_b
        # and the two modules now agree
        assert (a == b) == (ng_a == ng_b)
