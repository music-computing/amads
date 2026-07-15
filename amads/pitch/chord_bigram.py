"""
chord_bigram.py
---------------

Classifies a pair of chords (a bigram) under one of four equivalence regimes:
Ø  – exact ordered pair, roots as absolute pitch classes
I  - Inversion. For example, the minor [0, 3, 7] and major [0, 4, 7] triads are inversion equivalence.
R  – Retrograde-invariant (unordered pair)
K  – Key/transposition-invariant (directed interval replaces roots)
which can be combined to make another 4 (IR, IK, RK, IRK), for 8 in total.

Based on a classification scheme by Scott Murphy set out in publications including:

Scott Murphy. 2023.
"An Eightfold Taxonomy of Harmonic Progressions,
and Its Application to Triads Related by Major Third and Their Significance in Recent Screen Music"
Journal of Music Theory. 67 (1): 141–169.
https://doi.org/10.1215/00222909-10232093

Scott Murphy. 2024.
"Tracking Progressions of Heroic Chord Progressions in Recent Popular Screen Media"
in Lehman ed. "Film Music Analysis: Studying the Score"
DOI: 10.4324/9781003001171-3

Two ChordBigram objects are equal iff they share the same equivalence mode
and the same canonical form.

<small>**Author**: Mark Gotham</small>

"""

from __future__ import annotations

__author__ = "Mark Gotham"

from typing import Optional

from amads.core.chord import Chord

EQUIVALENCES = {"Ø", "I", "R", "K", "IR", "IK", "RK", "IRK"}


def _canonical_exact(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """Ø — ordered absolute pitch classes."""
    return (pc1, q1, pc2, q2)


def _canonical_inversion(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """I — major/minor identified at same root; directed, ordered by pc1 first.

    Two pairs (pc1,q1,pc2,q2) are I-equivalent iff they share the same
    root pair (unaffected by quality swap at each root) in the same direction.
    We normalise each root to a single representative by ignoring quality,
    keeping the directed pair of pitch classes plus the 'same/different quality'
    flag.
    """
    same_quality = q1 == q2
    return (pc1, pc2, same_quality)


def _canonical_retro(pc1: int, q1: str, pc2: int, q2: str) -> frozenset:
    """R — unordered pair of (pc, quality) atoms."""
    return frozenset({(pc1, q1), (pc2, q2)})


def _canonical_key(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """K — directed interval + ordered quality pair."""
    interval = (pc2 - pc1) % 12
    return (interval, q1, q2)


def _canonical_inversion_retro(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """IR — I + R: unordered pair of pcs + same/different quality flag."""
    same_quality = q1 == q2
    iv_fwd = (pc2 - pc1) % 12
    iv_bwd = (pc1 - pc2) % 12
    # Canonical: pick smaller directed-interval representative
    canon_iv = min(iv_fwd, iv_bwd)
    return (canon_iv, same_quality)


def _canonical_inversion_key(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """IK — I + K: directed interval (normalised via I) + same/different quality."""
    same_quality = q1 == q2
    # Under I, the 'effective' root pair is (pc1, pc2) regardless of quality.
    # K identifies all transpositions, so only the interval matters.
    iv = (pc2 - pc1) % 12
    return (iv, same_quality)


def _canonical_retro_key(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """RK — R + K: collapse direction, pick min representative."""
    forward = ((pc2 - pc1) % 12, q1, q2)
    backward = ((pc1 - pc2) % 12, q2, q1)
    return min(forward, backward)


def _canonical_inversion_retro_key(
    pc1: int, q1: str, pc2: int, q2: str
) -> tuple:
    """IRK — I + R + K."""
    same_quality = q1 == q2
    iv_fwd = (pc2 - pc1) % 12
    iv_bwd = (pc1 - pc2) % 12
    canon_iv = min(iv_fwd, iv_bwd)
    return (canon_iv, same_quality)


_UNICODE_SUB = {str(d): chr(0x2080 + d) for d in range(10)}


def _sub(n: int) -> str:
    """Integer 0-11 to unicode subscript string."""
    return "".join(_UNICODE_SUB[d] for d in str(n))


def _q(quality: str) -> str:
    if quality == "major":
        return "M"
    elif quality == "minor":
        return "m"
    raise ValueError("quality must be 'major' or 'minor'.")


# ---------------------------------------------------------------------------

# Coarsening lattice


_COARSEN_ORDER: dict[str, tuple[str, ...]] = {
    "Ø": ("Ø", "I", "R", "K", "IR", "IK", "RK", "IRK"),
    "I": ("I", "IR", "IK", "IRK"),
    "R": ("R", "IR", "RK", "IRK"),
    "K": ("K", "IK", "RK", "IRK"),
    "IR": ("IR", "IRK"),
    "IK": ("IK", "IRK"),
    "RK": ("RK", "IRK"),
    "IRK": ("IRK",),
}

# Equivalences that require a key_pitch_class argument
_NEEDS_KEY = {"Ø", "I", "R", "IR"}


# ---------------------------------------------------------------------------

# ChordBigram


class ChordBigram:
    """
    A directed pair of chords classified under a given equivalence regime.

    Parameters
    ----------
    chord1, chord2    : Chord
    equivalence       : one of "Ø", "I", "R", "K", "IR", "IK", "RK", "IRK"
    key_pitch_class   : 0-11; required for Ø, I, R, IR; ignored otherwise.

    Equivalences
    ------------
    Ø   — exact ordered pair (absolute pcs, order, quality)
    I   — major/minor inversion equivalence (same root, different quality to same class)
    R   — retrograde (order) equivalence
    K   — transpositional equivalence
    IR  — I + R
    IK  — I + K
    RK  — R + K
    IRK — I + R + K

    Label conventions
    -----------------
    Ø   Chronological; g1 key-relative subscript (omitted if 0).
        First/last letters = respective qualities.
        Middle = directed semitone interval (chord1 to chord2).

    I   g1 = always 'M'; g2 = 'M' if same quality, 'm' if not.
        Tonicized triad = whichever chord is closer to the key root.
        Middle = opci from tonicized root to non-tonicized root;
                 if tonicized is minor, subtract from 12.
        g1 subscript = key-relative distance of tonicized triad (omitted if 0).

    R   Near/far sort by key-relative distance; g1 = near, g2 = far.
        First/last letters = respective qualities of near/far.
        Middle = directed semitone interval (near to far).
        g1 subscript = key-relative distance of near triad (omitted if 0).

    K   Chronological; no subscripts.
        First/last letters = respective qualities.
        Middle = directed semitone interval (chord1 to chord2).

    IR  g1 = always 'M'; g2 = 'M' if same quality, 'm' if not.
        Near/far sort by key-relative distance (as in R).
        Middle = opci from near root to far root;
                 if near triad is minor, subtract from 12.
        g1 subscript = key-relative distance of near triad (omitted if 0).

    IK  g1 = always 'M'; g2 = 'M' if same quality, 'm' if not.
        Chronological; no subscripts.
        Middle = opci from chord1 root to chord2 root;
                 if chord1 is minor, subtract from 12.

    RK  g1 = 'M' if at least one major, 'm' if both minor.
        g2 = 'M' if both major, 'm' if at least one minor.
        Middle = ic (interval class) between roots if modes match;
                 else opci from major root to minor root.
        No subscripts.

    IRK g1 = always 'M'; g2 = 'M' if same quality, 'm' if not.
        Middle = ic (smaller of fwd/bwd interval). No subscripts.

    Examples
    --------
    >>> C = Chord(0, "major")   # C major
    >>> A = Chord(9, "major")   # A major

    Ø equivalence — key = D (pc 2)

    >>> ChordBigram(C, A, "Ø", key_pitch_class=2).latex_label
    '$M_{10}\\\\,9\\\\,M_{\\\\varnothing}$'

    >>> ChordBigram(A, C, "Ø", key_pitch_class=2).latex_label
    '$M_{7}\\\\,3\\\\,M_{\\\\varnothing}$'

    Ø equivalence — key = A (pc 9)
    >>> ChordBigram(C, A, "Ø", key_pitch_class=9).latex_label
    '$M_{3}\\\\,9\\\\,M_{\\\\varnothing}$'
    >>> ChordBigram(A, C, "Ø", key_pitch_class=9).latex_label
    '$M\\\\,3\\\\,M_{\\\\varnothing}$'

    Ø equivalence — key = E (pc 4)
    >>> ChordBigram(C, A, "Ø", key_pitch_class=4).latex_label
    '$M_{8}\\\\,9\\\\,M_{\\\\varnothing}$'
    >>> ChordBigram(A, C, "Ø", key_pitch_class=4).latex_label
    '$M_{5}\\\\,3\\\\,M_{\\\\varnothing}$'

    R equivalence (left/right pairs share label)
    Top:
    >>> ChordBigram(C, A, "R", key_pitch_class=2).latex_label
    '$M_{7}\\\\,3\\\\,M_{R}$'

    Mid:
    >>> ChordBigram(C, A, "R", key_pitch_class=9).latex_label
    '$M\\\\,3\\\\,M_{R}$'

    Lower:
    >>> ChordBigram(C, A, "R", key_pitch_class=4).latex_label
    '$M_{5}\\\\,3\\\\,M_{R}$'

    K equivalence (all left-side bigrams share label)
    >>> ChordBigram(C, A, "K").latex_label
    '$M\\\\,9\\\\,M_{K}$'

    K equivalence (all right-side bigrams share label)
    >>> ChordBigram(A, C, "K").latex_label
    '$M\\\\,3\\\\,M_{K}$'

    RK equivalence (all six share label)
    >>> ChordBigram(C, A, "RK").latex_label
    '$M\\\\,3\\\\,M_{RK}$'

    >>> ChordBigram(A, C, "RK").latex_label
    '$M\\\\,3\\\\,M_{RK}$'

    To this can be added the `I` set (not present in the book chapter).
    I equivalence: Gm key, Ebm to Gm should be "M4MI"
    >>> Eb_m = Chord(3, "minor")
    >>> G_m  = Chord(7, "minor")
    >>> ChordBigram(Eb_m, G_m, "I", key_pitch_class=7).latex_label
    '$M\\\\,4\\\\,M_{I}$'

    K equivalence: Ebm to Gm is m4mK
    >>> ChordBigram(Eb_m, G_m, "K").latex_label
    '$m\\\\,4\\\\,m_{K}$'

    IK equivalence: Ebm to Gm is M8MIK
    >>> ChordBigram(Eb_m, G_m, "IK").latex_label
    '$M\\\\,8\\\\,M_{IK}$'

    IR equivalence: Gm key, Ebm to Gm is M4MIR
    >>> ChordBigram(Eb_m, G_m, "IR", key_pitch_class=7).latex_label
    '$M\\\\,4\\\\,M_{IR}$'

    RK equivalence: Ebm to Gm is m4mRK
    >>> ChordBigram(Eb_m, G_m, "RK").latex_label
    '$m\\\\,4\\\\,m_{RK}$'

    IRK equivalence: Ebm to Gm is M4MIRK
    >>> ChordBigram(Eb_m, G_m, "IRK").latex_label
    '$M\\\\,4\\\\,M_{IRK}$'
    """

    def __init__(
        self,
        chord1: Chord,
        chord2: Chord,
        equivalence: str,
        key_pitch_class: Optional[int] = None,
    ) -> None:
        if equivalence not in EQUIVALENCES:
            raise ValueError(f"equivalence must be one of {EQUIVALENCES}")
        if equivalence in _NEEDS_KEY and key_pitch_class is None:
            raise ValueError(
                f"key_pitch_class is required for equivalence '{equivalence}'"
            )

        self.chord1 = chord1
        self.chord2 = chord2
        self.equivalence = equivalence
        self.key_pitch_class = key_pitch_class

        pc1, q1 = chord1.root.pitch_class, chord1.quality
        pc2, q2 = chord2.root.pitch_class, chord2.quality

        dispatch = {
            "Ø": _canonical_exact,
            "I": _canonical_inversion,
            "R": _canonical_retro,
            "K": _canonical_key,
            "IR": _canonical_inversion_retro,
            "IK": _canonical_inversion_key,
            "RK": _canonical_retro_key,
            "IRK": _canonical_inversion_retro_key,
        }
        self._canonical = dispatch[equivalence](pc1, q1, pc2, q2)

    @property
    def interval(self) -> int:
        """Directed semitone interval from chord1 to chord2 (0-11)."""
        return (
            self.chord2.root.pitch_class - self.chord1.root.pitch_class
        ) % 12

    @property
    def canonical(self):
        return self._canonical

    def coarsen(self, equivalence: str) -> "ChordBigram":
        """
        Return a new ChordBigram under a coarser equivalence.

        Valid directions follow the lattice::

            Ø  to I, R, K, IR, IK, RK, IRK
            I  to IR, IK, IRK
            R  to IR, RK, IRK
            K  to IK, RK, IRK
            IR to IRK
            IK to IRK
            RK to IRK

        ``key_pitch_class`` is forwarded only for targets in {Ø, I, R, IR}.
        """
        if equivalence not in EQUIVALENCES:
            raise ValueError(f"equivalence must be one of {EQUIVALENCES}")
        if equivalence not in _COARSEN_ORDER[self.equivalence]:
            raise ValueError(
                f"Cannot coarsen '{self.equivalence}' to '{equivalence}': "
                "not a valid coarsening"
            )
        kpc = self.key_pitch_class if equivalence in _NEEDS_KEY else None
        return ChordBigram(self.chord1, self.chord2, equivalence, kpc)

    @property
    def labels(self) -> dict:
        """Dict of labels under all equivalences reachable from self.equivalence."""
        return {
            eq: self.coarsen(eq).label
            for eq in _COARSEN_ORDER[self.equivalence]
        }

    # ------------------------------------------------------------------

    # Label

    def _compute_parts(self):  # noqa: C901
        """
        Return (g1_base, g1_sub, iv, g2_base, eq).

        g1_base : 'M' or 'm'
        g1_sub  : integer subscript value, or None if omitted
        iv      : interval integer (0-11)
        g2_base : 'M' or 'm'
        eq      : equivalence string
        """
        eq = self.equivalence
        pc1 = self.chord1.root.pitch_class
        pc2 = self.chord2.root.pitch_class
        q1 = self.chord1.quality
        q2 = self.chord2.quality
        key = self.key_pitch_class

        # ---- Ø: chronological, g1 key-relative subscript ----
        if eq == "Ø":
            iv = (pc2 - pc1) % 12
            d1 = (pc1 - key) % 12
            g1_base = _q(q1)
            g1_sub = d1 if d1 != 0 else None
            g2_base = _q(q2)

        # ---- I: tonicized-first logic; always M as g1 ----
        elif eq == "I":
            d1 = (pc1 - key) % 12
            d2 = (pc2 - key) % 12
            # Tonicized = closer to key root (ties favour chord1)
            if d1 <= d2:
                tonic_pc, tonic_q, tonic_d = pc1, q1, d1
                nontonic_pc = pc2
            else:
                tonic_pc, tonic_q, tonic_d = pc2, q2, d2
                nontonic_pc = pc1
            iv_raw = (nontonic_pc - tonic_pc) % 12
            iv = (12 - iv_raw) % 12 if tonic_q == "minor" else iv_raw
            g1_base = "M"
            g1_sub = tonic_d if tonic_d != 0 else None
            g2_base = "M" if q1 == q2 else "m"

        # ---- R: near/far by key distance ----
        elif eq == "R":
            d1 = (pc1 - key) % 12
            d2 = (pc2 - key) % 12
            if d1 <= d2:
                near_pc, near_q, near_d = pc1, q1, d1
                far_pc, far_q = pc2, q2
            else:
                near_pc, near_q, near_d = pc2, q2, d2
                far_pc, far_q = pc1, q1
            iv = (far_pc - near_pc) % 12
            g1_base = _q(near_q)
            g1_sub = near_d if near_d != 0 else None
            g2_base = _q(far_q)

        # ---- K: chronological, no subscripts ----
        elif eq == "K":
            iv = (pc2 - pc1) % 12
            g1_base = _q(q1)
            g1_sub = None
            g2_base = _q(q2)

        # ---- IR: near/far + I-normalisation; always M as g1 ----
        elif eq == "IR":
            d1 = (pc1 - key) % 12
            d2 = (pc2 - key) % 12
            if d1 <= d2:
                near_pc, near_q, near_d = pc1, q1, d1
                far_pc = pc2
            else:
                near_pc, near_q, near_d = pc2, q2, d2
                far_pc = pc1
            iv_raw = (far_pc - near_pc) % 12
            iv = (12 - iv_raw) % 12 if near_q == "minor" else iv_raw
            g1_base = "M"
            g1_sub = near_d if near_d != 0 else None
            g2_base = "M" if q1 == q2 else "m"

        # ---- IK: chronological + I-normalisation; always M as g1 ----
        elif eq == "IK":
            iv_raw = (pc2 - pc1) % 12
            iv = (12 - iv_raw) % 12 if q1 == "minor" else iv_raw
            g1_base = "M"
            g1_sub = None
            g2_base = "M" if q1 == q2 else "m"

        # ---- RK: collapse direction; quality-based glyph rules ----
        elif eq == "RK":
            either_major = q1 == "major" or q2 == "major"
            both_major = q1 == "major" and q2 == "major"
            g1_base = "M" if either_major else "m"
            g2_base = "M" if both_major else "m"
            g1_sub = None
            if q1 == q2:
                # Same modes: use interval class
                iv_fwd = (pc2 - pc1) % 12
                iv_bwd = (pc1 - pc2) % 12
                iv = min(iv_fwd, iv_bwd)
            else:
                # Mixed: opci from major root to minor root
                major_pc = pc1 if q1 == "major" else pc2
                minor_pc = pc2 if q1 == "major" else pc1
                iv = (minor_pc - major_pc) % 12

        # ---- IRK: I + R + K ----
        else:
            same = q1 == q2
            g1_base = "M"
            g2_base = "M" if same else "m"
            g1_sub = None
            iv_fwd = (pc2 - pc1) % 12
            iv_bwd = (pc1 - pc2) % 12
            iv = min(iv_fwd, iv_bwd)

        return g1_base, g1_sub, iv, g2_base, eq

    @property
    def label(self) -> str:
        """Short written label (unicode subscripts)."""
        g1_base, g1_sub, iv, g2_base, eq = self._compute_parts()
        g1 = g1_base + (_sub(g1_sub) if g1_sub is not None else "")
        return f"{g1} {iv} {g2_base}{eq}"

    @property
    def latex_label(self) -> str:
        r"""LaTeX label: $g1\,iv\,g2_{eq}$"""
        g1_base, g1_sub, iv, g2_base, eq = self._compute_parts()
        g1 = f"{g1_base}_{{{g1_sub}}}" if g1_sub is not None else g1_base
        eq_tex = {
            "Ø": r"\varnothing",
            "I": "I",
            "R": "R",
            "K": "K",
            "IR": "IR",
            "IK": "IK",
            "RK": "RK",
            "IRK": "IRK",
        }[eq]
        return rf"${g1}\,{iv}\,{g2_base}_{{{eq_tex}}}$"

    # ------------------------------------------------------------------

    # Equality / hashing

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChordBigram):
            return NotImplemented
        return (
            self.equivalence == other.equivalence
            and self._canonical == other._canonical
        )

    def __hash__(self) -> int:
        return hash((self.equivalence, self._canonical))

    # ------------------------------------------------------------------
    # Repr / str

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        pc1, q1 = self.chord1.root.pitch_class, self.chord1.quality
        pc2, q2 = self.chord2.root.pitch_class, self.chord2.quality
        c1 = f"{self.chord1.root.name}:{q1}"
        c2 = f"{self.chord2.root.name}:{q2}"
        eq = self.equivalence

        if eq == "Ø":
            body = f"{c1} -> {c2}"
        elif eq == "I":
            body = f"{c1} ~I {c2}"
        elif eq == "R":
            body = f"{{{c1}, {c2}}}"
        elif eq == "K":
            body = f"[+{self.interval}] {q1} -> {q2}"
        elif eq == "IR":
            body = f"{{{c1}, {c2}}} ~I"
        elif eq == "IK":
            iv_raw = (pc2 - pc1) % 12
            iv_i = (12 - iv_raw) % 12 if q1 == "minor" else iv_raw
            body = f"[I+{iv_i}] {q1} -> {q2}"
        elif eq == "RK":
            forward = ((pc2 - pc1) % 12, q1, q2)
            backward = ((pc1 - pc2) % 12, q2, q1)
            canon = min(forward, backward)
            body = f"[+-{canon[0]}] {canon[1]} ~ {canon[2]}"
        else:  # IRK
            iv_fwd = (pc2 - pc1) % 12
            iv_bwd = (pc1 - pc2) % 12
            iv = min(iv_fwd, iv_bwd)
            same = q1 == q2
            body = f"[ic{iv}] {'same' if same else 'mixed'} quality"

        key_tag = (
            f" | key={self.key_pitch_class}"
            if self.key_pitch_class is not None
            else ""
        )
        return f"ChordBigram({eq}: {body}{key_tag})"


if __name__ == "__main__":
    import doctest

    doctest.testmod()
