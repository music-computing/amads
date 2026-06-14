"""
chord_bigram.py
---------------

Classifies a pair of chords (a bigram) under one of four equivalence regimes:
Ø  – exact ordered pair, roots as absolute pitch classes
R  – retrograde-invariant (unordered pair)
K  – key/transposition-invariant (directed interval replaces roots)
RK – both R and K

Based on a classification scheme by Scott Murphy set out in publications including:

[TODO REFERENCE]

Two ChordBigram objects are equal iff they share the same equivalence mode
and the same canonical form.
"""

from __future__ import annotations

from typing import Optional

from amads.core.chord import Chord

EQUIVALENCES = {"Ø", "R", "K", "RK"}


def _canonical_exact(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """Ø — ordered absolute pitch classes."""
    return (pc1, q1, pc2, q2)


def _canonical_retro(pc1: int, q1: str, pc2: int, q2: str) -> frozenset:
    """R — unordered pair of (pc, quality) atoms."""
    return frozenset({(pc1, q1), (pc2, q2)})


def _canonical_key(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """K — directed interval + ordered quality pair."""
    interval = (pc2 - pc1) % 12
    return (interval, q1, q2)


def _canonical_retro_key(pc1: int, q1: str, pc2: int, q2: str) -> tuple:
    """RK — collapse direction: pick lexicographic min of forward/backward."""
    forward = ((pc2 - pc1) % 12, q1, q2)
    backward = ((pc1 - pc2) % 12, q2, q1)
    return min(forward, backward)


class ChordBigram:
    """
    A directed pair of chords classified under a given equivalence regime.

    Parameters
    ----------
    chord1, chord2 : Chord
    equivalence    : one of "Ø", "R", "K", "RK" (as set out of the top of this module)
    key_pitch_class: 0-11, required for Ø and R; ignored for K and RK.

    Label conventions follow from this as shown in the examples.

    Examples
    --------
    >>> C = Chord(0, "major")   # C major
    >>> A = Chord(9, "major")   # A major

    Ø equivalence — key = D (pc 2)

    >>> ChordBigram(C, A, "Ø", key_pitch_class=2).latex_label
    '$M_{7}\\\\,3\\\\,M_{10}_{\\\\varnothing}$'

    # TODO '$M_{10}\\\\,9\\\\,M_{\\\\varnothing}$'  (reverse and suppress second subscript)

    >>> ChordBigram(A, C, "Ø", key_pitch_class=2).latex_label
    '$M_{7}\\\\,3\\\\,M_{10}_{\\\\varnothing}$'

    # TODO '$M_{7}\\\\,3\\\\,M_{\\\\varnothing}$'  (suppress second subscript)

    Ø equivalence — key = A (pc 9)
    >>> ChordBigram(C, A, "Ø", key_pitch_class=9).latex_label
    '$M\\\\,3\\\\,M_{3}_{\\\\varnothing}$'

    # TODO '$M\\\\,3\\\\,M_\\\\varnothing}$'  (reverse, suppress second subscript)

    >>> ChordBigram(A, C, "Ø", key_pitch_class=9).latex_label
    '$M\\\\,3\\\\,M_{3}_{\\\\varnothing}$'

    # TODO '$M\\\\,3\\\\,M_\\\\varnothing}$'  (suppress second subscript)

    Ø equivalence — key = E (pc 4)
    >>> ChordBigram(C, A, "Ø", key_pitch_class=4).latex_label
    '$M_{5}\\\\,3\\\\,M_{8}_{\\\\varnothing}$'

    # TODO '$M_{8}\\\\,9\\\\,M\\\\varnothing}$'  (reverse and suppress second subscript)

    >>> ChordBigram(A, C, "Ø", key_pitch_class=4).latex_label
    '$M_{5}\\\\,3\\\\,M_{8}_{\\\\varnothing}$'

    # TODO '$M_{5}\\\\,3\\\\,M_{\\\\varnothing}$'  (suppress second subscript)

    R equivalence (left/right pairs share label)
    Top:
    >>> ChordBigram(C, A, "R", key_pitch_class=2).latex_label
    '$M_{7}\\\\,3\\\\,M_{10}_{R}$'

    # TODO: suppress second subscript 10

    Mid:
    >>> ChordBigram(C, A, "R", key_pitch_class=9).latex_label
    '$M\\\\,3\\\\,M_{3}_{R}$'

    # TODO: suppress second subscript 3

    Lower:
    >>> ChordBigram(C, A, "R", key_pitch_class=4).latex_label
    '$M_{5}\\\\,3\\\\,M_{8}_{R}$'

    # TODO: suppress second subscript 8

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
        if equivalence in {"Ø", "R"} and key_pitch_class is None:
            raise ValueError(
                f"key_pitch_class is required for equivalence '{equivalence}'"
            )

        self.chord1 = chord1
        self.chord2 = chord2
        self.equivalence = equivalence
        self.key_pitch_class = key_pitch_class

        pc1, q1 = chord1.root.pitch_class, chord1.quality
        pc2, q2 = chord2.root.pitch_class, chord2.quality

        if equivalence == "Ø":
            self._canonical = _canonical_exact(pc1, q1, pc2, q2)
        elif equivalence == "R":
            self._canonical = _canonical_retro(pc1, q1, pc2, q2)
        elif equivalence == "K":
            self._canonical = _canonical_key(pc1, q1, pc2, q2)
        else:  # RK
            self._canonical = _canonical_retro_key(pc1, q1, pc2, q2)

    @property
    def interval(self) -> int:
        """Directed semitone interval from chord1 to chord2 (0-11)."""
        return (
            self.chord2.root.pitch_class - self.chord1.root.pitch_class
        ) % 12

    @property
    def canonical(self):
        """The canonical form used for equality and hashing."""
        return self._canonical

    _COARSEN_ORDER = {
        "Ø": ("Ø", "R", "K", "RK"),
        "R": ("R", "RK"),
        "K": ("K", "RK"),
        "RK": ("RK",),
    }

    def coarsen(self, equivalence: str) -> "ChordBigram":
        """
        Return a new ChordBigram of the same pair under a coarser equivalence.

        Valid coarsening directions:
          Ø  -> R, K
          R  -> RK
          K  -> RK
          RK -> (none further)

        `key_pitch_class` is forwarded for Ø/R targets; dropped for K/RK.
        """
        if equivalence not in EQUIVALENCES:
            raise ValueError(f"equivalence must be one of {EQUIVALENCES}")
        if equivalence not in self._COARSEN_ORDER[self.equivalence]:
            raise ValueError(
                f"Cannot coarsen '{self.equivalence}' to '{equivalence}': "
                f"not a valid coarsening"
            )
        kpc = self.key_pitch_class if equivalence in {"Ø", "R"} else None
        return ChordBigram(self.chord1, self.chord2, equivalence, kpc)

    @property
    def labels(self) -> dict:
        """
        Dict of labels under all equivalences reachable from self.equivalence.
        Keys are equivalence strings; values are label strings.
        """
        return {
            eq: self.coarsen(eq).label
            for eq in self._COARSEN_ORDER[self.equivalence]
        }

    # Label conventions

    @staticmethod
    def _q(quality: str) -> str:
        """
        Map quality string to M/m glyph.
        quality must be one of 'major', 'minor', (raises otherwise)
        """
        if quality == "major":
            return "M"
        elif quality == "minor":
            return "m"
        else:
            raise ValueError("quality must be one of 'major' or 'minor'.")

    @staticmethod
    def _sub(n: int) -> str:
        """
        Integer 0-11 -> unicode subscript string.
        Note:
            Iterates over str(n) digit by digit, so str(10) gives "10" → "₁" + "₀" = ₁₀.
        """
        digits = {
            "0": "\u2080",
            "1": "\u2081",
            "2": "\u2082",
            "3": "\u2083",
            "4": "\u2084",
            "5": "\u2085",
            "6": "\u2086",
            "7": "\u2087",
            "8": "\u2088",
            "9": "\u2089",
        }
        return "".join(digits[d] for d in str(n))

    # Core label computation — shared by label and latex_label

    def _compute_parts(self):
        """
        Return (g1_base, g1_sub, iv, g2_base, g2_sub, eq) where:
          g1_base / g2_base : 'M' or 'm'
          g1_sub  / g2_sub  : integer subscript value, or None if omitted
          iv                : interval integer
          eq                : equivalence string
        """
        eq = self.equivalence
        pc1 = self.chord1.root.pitch_class
        pc2 = self.chord2.root.pitch_class
        q1 = self.chord1.quality
        q2 = self.chord2.quality
        key = self.key_pitch_class

        if eq in {"Ø", "R"}:
            # Sort chords by ascending key-relative pitch class (near first).
            d1 = (pc1 - key) % 12
            d2 = (pc2 - key) % 12
            if d1 <= d2:
                near_pc, near_q = pc1, q1
                far_pc, far_q = pc2, q2
                near_d, far_d = d1, d2
            else:
                near_pc, near_q = pc2, q2
                far_pc, far_q = pc1, q1
                near_d, far_d = d2, d1

            iv = (far_pc - near_pc) % 12
            # Omit subscript when key-relative value is 0
            g1_base = self._q(near_q)
            g1_sub = near_d if near_d != 0 else None
            g2_base = self._q(far_q)
            g2_sub = far_d if far_d != 0 else None

        elif eq == "K":
            # Chronological order; no subscripts
            iv = (pc2 - pc1) % 12
            g1_base = self._q(q1)
            g1_sub = None
            g2_base = self._q(q2)
            g2_sub = None

        else:  # RK
            # Canonical (min) direction
            forward = ((pc2 - pc1) % 12, q1, q2)
            backward = ((pc1 - pc2) % 12, q2, q1)
            canon = min(forward, backward)
            iv = canon[0]
            either_major = q1 == "major" or q2 == "major"
            both_major = q1 == "major" and q2 == "major"
            g1_base = "M" if either_major else "m"
            g1_sub = None
            g2_base = "M" if both_major else "m"
            g2_sub = None

        return g1_base, g1_sub, iv, g2_base, g2_sub, eq

    @property
    def label(self):
        """label, unicode version"""
        g1_base, g1_sub, iv, g2_base, g2_sub, eq = self._compute_parts()
        g1 = g1_base + (self._sub(g1_sub) if g1_sub is not None else "")
        g2 = g2_base + (self._sub(g2_sub) if g2_sub is not None else "")
        return f"{g1} {iv} {g2}{eq}"

    @property
    def latex_label(self):
        """
        LaTeX label of the form  $g1\\,iv\\,g2_{eq}$
        where g1/g2 carry their own subscripts when non-zero,
        and the equivalence symbol is a subscript on the closing brace.
        """
        g1_base, g1_sub, iv, g2_base, g2_sub, eq = self._compute_parts()

        eq_tex = {"Ø": r"\varnothing", "R": "R", "K": "K", "RK": "RK"}[eq]

        # Build g1 latex: subscript only when non-None
        if g1_sub is not None:
            g1 = rf"{g1_base}_{{{g1_sub}}}"
        else:
            g1 = g1_base

        # Build g2 latex: subscript only when non-None
        if g2_sub is not None:
            g2 = rf"{g2_base}_{{{g2_sub}}}"
        else:
            g2 = g2_base

        return rf"${g1}\,{iv}\,{g2}_{{{eq_tex}}}$"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChordBigram):
            return NotImplemented
        return (
            self.equivalence == other.equivalence
            and self._canonical == other._canonical
        )

    def __hash__(self) -> int:
        return hash((self.equivalence, self._canonical))

    # Repr / str

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        c1 = f"{self.chord1.root.name}:{self.chord1.quality}"
        c2 = f"{self.chord2.root.name}:{self.chord2.quality}"
        if self.equivalence == "Ø":
            body = f"{c1} -> {c2}"
        elif self.equivalence == "R":
            body = f"{{{c1}, {c2}}}"
        elif self.equivalence == "K":
            body = f"[+{self.interval}] {self.chord1.quality} -> {self.chord2.quality}"
        else:  # RK
            forward = (self.interval, self.chord1.quality, self.chord2.quality)
            backward = (
                (12 - self.interval) % 12,
                self.chord2.quality,
                self.chord1.quality,
            )
            canon = min(forward, backward)
            body = f"[+-{canon[0]}] {canon[1]} ~ {canon[2]}"

        key_tag = (
            f" | key={self.key_pitch_class}"
            if self.key_pitch_class is not None
            else ""
        )
        return f"ChordBigram({self.equivalence}: {body}{key_tag})"


if __name__ == "__main__":
    import doctest

    doctest.testmod()
