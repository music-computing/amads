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


# Canonical-form helpers


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


# ChordBigram


class ChordBigram:
    """
    A directed pair of chords classified under a given equivalence regime.

    Parameters
    ----------
    chord1, chord2 : Chord
    equivalence    : one of "Ø", "R", "K", "RK"
    key_pitch_class: 0–11, required for Ø and R (non-key-invariant modes)
                     to anchor pitch-class meaning; ignored for K and RK.

    Examples
    --------

    Here is a set of exmaples based on Figure 3.2

    >>> from amads.core.pitch import Pitch

    >>> C = Chord(Pitch("C"), "major")
    >>> A = Chord(Pitch("A"), "major")

    >>> top_left = ChordBigram(C, A, equivalence="Ø", key_pitch_class=2) # D
    >>> top_left.latex_label
    '$M_{10}\\,9\\,M_{\\varnothing}$'

    >>> top_right = ChordBigram(A, C, equivalence="Ø", key_pitch_class=2)
    >>> top_right.latex_label
    '$M_{7}\\,3\\,M_{\\varnothing}$'

    >>> mid_left = ChordBigram(C, A, equivalence="Ø", key_pitch_class=9) # A
    >>> mid_left.latex_label
    '$M_{3}\\,9\\,M_{10}_{\\varnothing}$'

    >>> mid_right = ChordBigram(A, C, equivalence="Ø", key_pitch_class=9)
    >>> mid_right.latex_label
    '$M\\,3\\,M{\\varnothing}$'

    >>> low_left = ChordBigram(C, A, key_pitch_class=4) # E
    >>> low_left.latex_label
    '$M_{8}\\,9\\,M{\\varnothing}$'

    >>> low_right = ChordBigram(A, C key_pitch_class=4)
    >>> low_right.latex_label
    '$M_{5}\\,3\\,M{\\varnothing}$'


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

        # Derived properties

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

    # Coarsening and multi-label

    # Partial order of equivalences: each entry lists what it can coarsen to
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

    # Label (written convention: 4-6 chars)

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

    @property
    def label(self) -> str:
        """
        Short written label following the convention established by Murphy:

          [q1][sub1] [interval] [q2][sub2][equivalence]

        where:
          q1/q2    - M or m per the ordering/equivalence rules
          sub      - key-relative pitch class (omitted if no key)
          interval - directed semitones (canonical under RK)
          equivalence - Ø, R, K, or RK suffix

        See also `self.latex_label` for a LaTex compatible version.
        """
        eq = self.equivalence
        pc1 = self.chord1.root.pitch_class
        pc2 = self.chord2.root.pitch_class
        q1 = self.chord1.quality
        q2 = self.chord2.quality
        key = self.key_pitch_class

        if eq in {"Ø", "R"}:
            # Sort both chords by ascending distance from tonic
            d1 = (pc1 - key) % 12
            d2 = (pc2 - key) % 12
            if d1 <= d2:
                near_pc, near_q = pc1, q1
                far_pc, far_q = pc2, q2
            else:
                near_pc, near_q = pc2, q2
                far_pc, far_q = pc1, q1

            iv = (far_pc - near_pc) % 12

            near_sub = self._sub((near_pc - key) % 12)
            far_sub = self._sub((far_pc - key) % 12)

            glyph1 = self._q(near_q) + near_sub
            glyph2 = self._q(far_q) + far_sub

        elif eq == "K":
            # Chronological order; no subscripts
            iv = (pc2 - pc1) % 12
            glyph1 = self._q(q1)
            glyph2 = self._q(q2)

        else:  # RK
            # Canonical (min) direction
            forward = ((pc2 - pc1) % 12, q1, q2)
            backward = ((pc1 - pc2) % 12, q2, q1)
            canon = min(forward, backward)
            iv = canon[0]

            # RK quality rules:
            #   glyph1: M if at least one chord is major, else m
            #   glyph2: M if both chords are major, else m
            either_major = q1 == "major" or q2 == "major"
            both_major = q1 == "major" and q2 == "major"
            glyph1 = "M" if either_major else "m"
            glyph2 = "M" if both_major else "m"

        return f"{glyph1} {iv} {glyph2}{eq}"

    @property
    def latex_label(self) -> str:
        """
        LaTeX rendering of the label for use in matplotlib/notebook display.
        Subscripts use LaTeX syntax: $M_{0}$ etc.
        Suitable for ax.text(), ax.set_title(), legend entries.
        """
        eq = self.equivalence
        pc1 = self.chord1.root.pitch_class
        pc2 = self.chord2.root.pitch_class
        q1 = self.chord1.quality
        q2 = self.chord2.quality
        key = self.key_pitch_class

        eq_tex = {"Ø": r"\varnothing", "R": "R", "K": "K", "RK": "RK"}[eq]

        if eq in {"Ø", "R"}:
            d1 = (pc1 - key) % 12
            d2 = (pc2 - key) % 12
            if d1 <= d2:
                near_pc, near_q = pc1, q1
                far_pc, far_q = pc2, q2
            else:
                near_pc, near_q = pc2, q2
                far_pc, far_q = pc1, q1

            iv = (far_pc - near_pc) % 12
            ns = (near_pc - key) % 12
            fs = (far_pc - key) % 12
            g1 = f"{self._q(near_q)}_{{{ns}}}"
            g2 = f"{self._q(far_q)}_{{{fs}}}"

        elif eq == "K":
            iv = (pc2 - pc1) % 12
            g1 = self._q(q1)
            g2 = self._q(q2)

        else:  # RK
            forward = ((pc2 - pc1) % 12, q1, q2)
            backward = ((pc1 - pc2) % 12, q2, q1)
            canon = min(forward, backward)
            iv = canon[0]
            either_major = q1 == "major" or q2 == "major"
            both_major = q1 == "major" and q2 == "major"
            g1 = "M" if either_major else "m"
            g2 = "M" if both_major else "m"

        return rf"${g1}\,{iv}\,{g2}_{{{eq_tex}}}$"

    # Equality and hashing (canonical-form based)

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
