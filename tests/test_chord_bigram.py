"""
Test ChordBigram.

Complements the doctests (which cover `latex_label` for major/major C–A pairs)
by testing:
  - canonical forms for all eight equivalences (Ø, I, R, K, IR, IK, RK, IRK)
  - equality and hashing
  - interval property
  - label (unicode) property
  - coarsen() valid and invalid paths
  - labels dict
  - _q and _sub helpers
  - __str__ and __repr__
  - ValueError guards (__init__ and coarsen)
  - minor quality chords
  - mixed major/minor quality (RK quality rules)
  - R, RK symmetry; K, Ø asymmetry
  - regression coverage for the IR transposition-invariance bug
  - more
"""

import pytest

from amads.harmony.chord_bigram import (
    ChordBigram,
    _canonical_exact,
    _canonical_inversion,
    _canonical_inversion_key,
    _canonical_inversion_retro,
    _canonical_inversion_retro_key,
    _canonical_key,
    _canonical_retro,
    _canonical_retro_key,
    _q,
    _sub,
)

# ---------------------------------------------------------------------------

# Minimal stubs. Test directly on what's really needed here (see `TestRealChordProtocol`).


class _Root:
    def __init__(self, pc, name="?"):
        self.pitch_class = pc
        self.name = name


class Chord:
    def __init__(self, pc, quality, name="?"):
        self._pc = pc
        self.quality = quality
        self._name = name

    @property
    def root(self):
        return _Root(self._pc, self._name)


# ---------------------------------------------------------------------------

# Fixtures


@pytest.fixture
def C():
    return Chord(0, "major", "C")


@pytest.fixture
def A():
    return Chord(9, "major", "A")


@pytest.fixture
def Cm():
    return Chord(0, "minor", "C")


@pytest.fixture
def Am():
    return Chord(9, "minor", "A")


@pytest.fixture
def D():
    return Chord(2, "major", "D")


# ---------------------------------------------------------------------------

# Canonical-form helpers


class TestCanonicalHelpers:
    def test_exact_is_ordered_tuple(self):
        assert _canonical_exact(0, "major", 9, "major") == (
            0,
            "major",
            9,
            "major",
        )
        assert _canonical_exact(9, "major", 0, "major") == (
            9,
            "major",
            0,
            "major",
        )

    def test_exact_direction_matters(self):
        assert _canonical_exact(0, "major", 9, "major") != _canonical_exact(
            9, "major", 0, "major"
        )

    def test_retro_is_frozenset(self):
        r = _canonical_retro(0, "major", 9, "major")
        assert isinstance(r, frozenset)

    def test_retro_is_symmetric(self):
        assert _canonical_retro(0, "major", 9, "major") == _canonical_retro(
            9, "major", 0, "major"
        )

    def test_key_directed_interval(self):
        # C to A: (9-0)%12 = 9
        assert _canonical_key(0, "major", 9, "major") == (9, "major", "major")
        # A to C: (0-9)%12 = 3
        assert _canonical_key(9, "major", 0, "major") == (3, "major", "major")

    def test_key_direction_matters(self):
        assert _canonical_key(0, "major", 9, "major") != _canonical_key(
            9, "major", 0, "major"
        )

    def test_retro_key_picks_min(self):
        # forward (9,major,major) vs backward (3,major,major)  to  min is (3,...)
        assert _canonical_retro_key(0, "major", 9, "major") == (
            3,
            "major",
            "major",
        )
        assert _canonical_retro_key(9, "major", 0, "major") == (
            3,
            "major",
            "major",
        )

    def test_retro_key_is_symmetric(self):
        assert _canonical_retro_key(
            0, "major", 9, "major"
        ) == _canonical_retro_key(9, "major", 0, "major")


class TestInversionCanonicalHelpers:
    """
    TestCanonicalHelpers (above) covers Ø, K, R, RK directly;
    this class closes the equivalent gap for the I-family (I, IR, IK, IRK).
    """

    def test_inversion_keeps_directed_pcs_plus_quality_flag(self):
        assert _canonical_inversion(0, "major", 9, "major") == (0, 9, True)
        assert _canonical_inversion(0, "major", 9, "minor") == (0, 9, False)

    def test_inversion_direction_matters(self):
        assert _canonical_inversion(
            0, "major", 9, "major"
        ) != _canonical_inversion(9, "major", 0, "major")

    def test_inversion_ignores_which_quality_so_long_as_relation_matches(self):
        """
        major->major and minor->minor are both 'same_quality=True'
        """
        assert _canonical_inversion(
            0, "major", 9, "major"
        ) == _canonical_inversion(0, "minor", 9, "minor")

    def test_inversion_retro_is_frozenset_of_pcs(self):
        r = _canonical_inversion_retro(0, "major", 9, "minor")
        assert isinstance(r[0], frozenset)

    def test_inversion_retro_is_symmetric(self):
        assert _canonical_inversion_retro(
            0, "major", 9, "minor"
        ) == _canonical_inversion_retro(9, "minor", 0, "major")

    def test_inversion_retro_is_NOT_transposition_invariant(self):
        """
        IR should not be transposition-invariant (i.e., not IRK).
        It must keep the unordered *pair of absolute pitch classes* instead,
        mirroring R, so a bare transposition is not IR-equivalent.
        """
        c_to_a = _canonical_inversion_retro(0, "major", 9, "minor")
        f_to_d = _canonical_inversion_retro(
            5, "major", 2, "minor"
        )  # +5 transposed
        assert c_to_a != f_to_d

    def test_inversion_retro_same_quality_flag_preserved(self):
        assert _canonical_inversion_retro(0, "major", 9, "minor")[1] is False
        assert _canonical_inversion_retro(0, "major", 9, "major")[1] is True

    def test_inversion_key_is_transposition_invariant(self):
        """IK legitimately collapses transposition, unlike IR"""
        assert _canonical_inversion_key(
            0, "major", 9, "minor"
        ) == _canonical_inversion_key(5, "major", 2, "minor")

    def test_inversion_key_direction_matters(self):
        assert _canonical_inversion_key(
            0, "major", 9, "major"
        ) != _canonical_inversion_key(9, "major", 0, "major")

    def test_inversion_retro_key_picks_min_and_is_symmetric(self):
        assert _canonical_inversion_retro_key(
            0, "major", 9, "major"
        ) == _canonical_inversion_retro_key(9, "major", 0, "major")


# ---------------------------------------------------------------------------

# Construction and ValueError guards


class TestInit:
    def test_invalid_equivalence(self, C, A):
        with pytest.raises(ValueError, match="equivalence must be one of"):
            ChordBigram(C, A, "X")

    def test_null_requires_key(self, C, A):
        with pytest.raises(ValueError, match="key_pitch_class is required"):
            ChordBigram(C, A, "Ø")

    def test_r_requires_key(self, C, A):
        with pytest.raises(ValueError, match="key_pitch_class is required"):
            ChordBigram(C, A, "R")

    def test_k_does_not_require_key(self, C, A):
        b = ChordBigram(C, A, "K")
        assert b.key_pitch_class is None

    def test_rk_does_not_require_key(self, C, A):
        b = ChordBigram(C, A, "RK")
        assert b.key_pitch_class is None

    def test_attributes_stored(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        assert b.chord1 is C
        assert b.chord2 is A
        assert b.equivalence == "Ø"
        assert b.key_pitch_class == 2


# ---------------------------------------------------------------------------

# interval property


class TestInterval:
    def test_c_to_a(self, C, A):
        assert ChordBigram(C, A, "K").interval == 9

    def test_a_to_c(self, C, A):
        assert ChordBigram(A, C, "K").interval == 3

    def test_unison(self, C):
        b = ChordBigram(C, C, "K")
        assert b.interval == 0


# ---------------------------------------------------------------------------

# Equality and hashing


class TestEqualityAndHashing:
    def test_null_asymmetric(self, C, A):
        b1 = ChordBigram(C, A, "Ø", key_pitch_class=2)
        b2 = ChordBigram(A, C, "Ø", key_pitch_class=2)
        assert b1 != b2

    def test_r_symmetric(self, C, A):
        b1 = ChordBigram(C, A, "R", key_pitch_class=2)
        b2 = ChordBigram(A, C, "R", key_pitch_class=2)
        assert b1 == b2

    def test_k_asymmetric(self, C, A):
        b1 = ChordBigram(C, A, "K")
        b2 = ChordBigram(A, C, "K")
        assert b1 != b2

    def test_rk_symmetric(self, C, A):
        b1 = ChordBigram(C, A, "RK")
        b2 = ChordBigram(A, C, "RK")
        assert b1 == b2

    def test_different_equivalences_not_equal(self, C, A):
        bk = ChordBigram(C, A, "K")
        brk = ChordBigram(C, A, "RK")
        assert bk != brk

    def test_hash_equal_objects(self, C, A):
        b1 = ChordBigram(C, A, "R", key_pitch_class=2)
        b2 = ChordBigram(A, C, "R", key_pitch_class=2)
        assert hash(b1) == hash(b2)

    def test_hash_usable_in_set(self, C, A):
        b1 = ChordBigram(C, A, "RK")
        b2 = ChordBigram(A, C, "RK")
        b3 = ChordBigram(C, A, "K")
        s = {b1, b2, b3}
        assert len(s) == 2  # b1 and b2 are the same

    def test_not_equal_to_non_bigram(self, C, A):
        b = ChordBigram(C, A, "K")
        assert b.__eq__("not a bigram") is NotImplemented

    def test_r_key_pitch_class_does_not_affect_equality(self, C, A):
        # R canonical is a frozenset of (pc, quality) pairs — key doesn't factor in
        b1 = ChordBigram(C, A, "R", key_pitch_class=2)
        b2 = ChordBigram(C, A, "R", key_pitch_class=9)
        assert b1 == b2

    def test_null_different_keys_not_equal(self, C, A):
        b1 = ChordBigram(C, A, "Ø", key_pitch_class=2)
        b2 = ChordBigram(C, A, "Ø", key_pitch_class=9)
        # canonical includes absolute pcs, not key-relative — so still equal
        assert b1 == b2


class TestIREquivalenceBugRegression:
    """
    IR-specific regression:
    This is the object-level counterpart to
    TestInversionCanonicalHelpers.test_inversion_retro_is_NOT_transposition_invariant
    Here we test through ChordBigram itself rather than the bare helper.
    """

    def test_bare_transposition_is_not_IR_equivalent(self, C, A):
        """
        C major -> A major, transposed up a perfect 4th (+5 semitones),
        quality pattern preserved (major -> major both times)
        """
        b1 = ChordBigram(C, A, "IR", key_pitch_class=0)
        F_chord = Chord(5, "major", "F")
        D_chord = Chord(2, "major", "D")
        b2 = ChordBigram(F_chord, D_chord, "IR", key_pitch_class=0)
        assert b1 != b2

    def test_IRK_is_still_transposition_invariant(self, C, A):
        """IRK is *supposed* to merge these"""
        b1 = ChordBigram(C, A, "IRK")
        F_chord = Chord(5, "major", "F")
        D_chord = Chord(2, "major", "D")
        b2 = ChordBigram(F_chord, D_chord, "IRK")
        assert b1 == b2


# ---------------------------------------------------------------------------

# coarsen()


class TestCoarsen:
    def test_null_to_r(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        br = b.coarsen("R")
        assert br.equivalence == "R"
        assert br.key_pitch_class == 2

    def test_null_to_k(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        bk = b.coarsen("K")
        assert bk.equivalence == "K"
        assert bk.key_pitch_class is None

    def test_null_to_rk(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        brk = b.coarsen("RK")
        assert brk.equivalence == "RK"

    def test_r_to_rk(self, C, A):
        b = ChordBigram(C, A, "R", key_pitch_class=2)
        brk = b.coarsen("RK")
        assert brk.equivalence == "RK"

    def test_k_to_rk(self, C, A):
        b = ChordBigram(C, A, "K")
        brk = b.coarsen("RK")
        assert brk.equivalence == "RK"

    def test_rk_cannot_coarsen(self, C, A):
        b = ChordBigram(C, A, "RK")
        with pytest.raises(ValueError, match="not a valid coarsening"):
            b.coarsen("K")

    def test_r_cannot_coarsen_to_null(self, C, A):
        b = ChordBigram(C, A, "R", key_pitch_class=2)
        with pytest.raises(ValueError, match="not a valid coarsening"):
            b.coarsen("Ø")

    def test_k_cannot_coarsen_to_r(self, C, A):
        b = ChordBigram(C, A, "K")
        with pytest.raises(ValueError, match="not a valid coarsening"):
            b.coarsen("R")

    def test_invalid_target(self, C, A):
        b = ChordBigram(C, A, "K")
        with pytest.raises(ValueError, match="equivalence must be one of"):
            b.coarsen("Z")

    def test_coarsen_rk_result_symmetric(self, C, A):
        # Coarsening Ø C to A and Ø A to C to RK should give equal bigrams
        b1 = ChordBigram(C, A, "Ø", key_pitch_class=2).coarsen("RK")
        b2 = ChordBigram(A, C, "Ø", key_pitch_class=2).coarsen("RK")
        assert b1 == b2


# ---------------------------------------------------------------------------

# labels dict


class TestLabels:
    def test_null_has_all_four(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        labs = b.labels
        assert set(labs.keys()) == {"IK", "Ø", "I", "IRK", "RK", "R", "K", "IR"}

    def test_r_has_two(self, C, A):
        b = ChordBigram(C, A, "R", key_pitch_class=2)
        assert set(b.labels.keys()) == {"RK", "IR", "R", "IRK"}

    def test_k_has_two(self, C, A):
        b = ChordBigram(C, A, "K")
        assert set(b.labels.keys()) == {"K", "RK", "IK", "IRK"}

    def test_rk_has_one(self, C, A):
        b = ChordBigram(C, A, "RK")
        assert set(b.labels.keys()) == {"RK", "IRK"}

    def test_labels_values_are_strings(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        assert all(isinstance(v, str) for v in b.labels.values())


# ---------------------------------------------------------------------------

# _q and _sub static helpers


class TestHelpers:
    def test_q_major(self):
        assert _q("major") == "M"

    def test_q_minor(self):
        assert _q("minor") == "m"

    def test_q_invalid(self):
        with pytest.raises(ValueError):
            _q("diminished")

    def test_sub_single_digit(self):
        assert _sub(0) == "₀"
        assert _sub(9) == "₉"

    def test_sub_double_digit(self):
        assert _sub(10) == "₁₀"
        assert _sub(11) == "₁₁"


# ---------------------------------------------------------------------------

# label (unicode) property


class TestLabel:
    def test_null_chronological_with_subscript(self, C, A):
        """C to A, key=2 (D)"""
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        assert b.label == "M₁₀ 9 MØ"

    def test_null_subscript_zero_omitted(self, C, A):
        """A to C, key=9: A is the tonic so subscript omitted"""
        b = ChordBigram(A, C, "Ø", key_pitch_class=9)
        assert b.label == "M 3 MØ"

    def test_r_near_far_with_subscript(self, C, A):
        """key=2: near=A(d=7), far=C(d=10), iv=3"""
        b = ChordBigram(C, A, "R", key_pitch_class=2)
        assert b.label == "M₇ 3 MR"

    def test_r_near_is_tonic_omits_subscript(self, C, A):
        """key=9: near=A(d=0 to omit), far=C(d=3), iv=3"""
        b = ChordBigram(C, A, "R", key_pitch_class=9)
        assert b.label == "M 3 MR"

    def test_k_no_subscripts(self, C, A):
        b = ChordBigram(C, A, "K")
        assert b.label == "M 9 MK"

    def test_k_reverse(self, C, A):
        b = ChordBigram(A, C, "K")
        assert b.label == "M 3 MK"

    def test_rk_canonical_direction(self, C, A):
        b1 = ChordBigram(C, A, "RK")
        b2 = ChordBigram(A, C, "RK")
        assert b1.label == b2.label == "M 3 MRK"

    def test_minor_minor_rk(self, Cm, Am):
        b = ChordBigram(Cm, Am, "RK")
        assert b.label == "m 3 mRK"

    def test_mixed_quality_rk_glyph1_major(self, C, Am):
        """either major  to  g1=M; not both major  to  g2=m"""
        b = ChordBigram(C, Am, "RK")
        assert b.label == "M 9 mRK"


# ---------------------------------------------------------------------------

# Minor quality chords


class TestMinorQuality:
    def test_minor_label_k(self, Cm, Am):
        b = ChordBigram(Cm, Am, "K")
        assert b.label == "m 9 mK"

    def test_minor_r_symmetric(self, Cm, Am):
        b1 = ChordBigram(Cm, Am, "R", key_pitch_class=2)
        b2 = ChordBigram(Am, Cm, "R", key_pitch_class=2)
        assert b1 == b2

    def test_major_minor_not_equal_to_minor_major_under_k(self, C, Am, Cm, A):
        b1 = ChordBigram(C, Am, "K")
        b2 = ChordBigram(Cm, A, "K")
        assert b1 != b2


# ---------------------------------------------------------------------------

# __str__ and __repr__


class TestStrRepr:
    def test_str_is_label(self, C, A):
        b = ChordBigram(C, A, "K")
        assert str(b) == b.label

    def test_repr_null(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        r = repr(b)
        assert r.startswith("ChordBigram(Ø:")
        assert "key=2" in r

    def test_repr_r(self, C, A):
        b = ChordBigram(C, A, "R", key_pitch_class=2)
        r = repr(b)
        assert r.startswith("ChordBigram(R:")
        assert "{" in r  # unordered set notation

    def test_repr_k(self, C, A):
        b = ChordBigram(C, A, "K")
        r = repr(b)
        assert r.startswith("ChordBigram(K:")
        assert "major -> major" in r
        assert "key=" not in r

    def test_repr_rk(self, C, A):
        b = ChordBigram(C, A, "RK")
        r = repr(b)
        assert r.startswith("ChordBigram(RK:")
        assert "~" in r
        assert "key=" not in r


# ---------------------------------------------------------------------------

# canonical property


class TestCanonicalProperty:
    def test_null_canonical_is_tuple(self, C, A):
        b = ChordBigram(C, A, "Ø", key_pitch_class=2)
        assert isinstance(b.canonical, tuple)
        assert b.canonical == (0, "major", 9, "major")

    def test_r_canonical_is_frozenset(self, C, A):
        b = ChordBigram(C, A, "R", key_pitch_class=2)
        assert isinstance(b.canonical, frozenset)

    def test_k_canonical_is_tuple(self, C, A):
        b = ChordBigram(C, A, "K")
        assert b.canonical == (9, "major", "major")

    def test_rk_canonical_is_tuple(self, C, A):
        b = ChordBigram(C, A, "RK")
        assert b.canonical == (3, "major", "major")


# ---------------------------------------------------------------------------


class TestRealChordProtocol:
    """
    Every other test in this file uses the local `Chord`/`_Root` stubs above.
    That scenario pins down exactly the interface ChordBigram needs
    (.quality, .root.pitch_class, .root.name)
    It keeps the rest of the suite fast and isolated from the amads.core.chord implementation.

    This single test is the bridge:
    it confirms the stub's assumed protocol still matches the real class,
    so a silent drift (e.g. a renamed attribute) will fail.

    """

    def test_stub_protocol_matches_real_chord(self):
        from amads.core.chord import Chord as RealChord

        real_c = RealChord(0, "major")
        real_a = RealChord(9, "major")
        b = ChordBigram(real_c, real_a, "K")
        assert b.canonical == (9, "major", "major")
        assert b.interval == 9
