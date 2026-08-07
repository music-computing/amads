"""
chord_ngram.py
---------------

In `chord_bigram.ChordBigram`
we set out chord *pairs*,
staying as close as possible to a taxonomy of equivalence by Murphy.

Here, we extend that logic to chord *successions* of any length n >= 2.

The main difference is that Murphy's
bigrams have only one order relation: "R" (retrograde).
 With three or more chords, there are more kinds of "order" equivalences:

Order equivalences
-------------------
Order equivalences are the divergence from Murphy.

Ø Identity.
No reordering permitted; successions match only if identical,
chord for chord, in the given order.

R Retrograde.
ABC ~ CBA (read `~` as "is equivalent to.").
Group size: 2.
An involution: applying R twice returns to the original.

C Rotation (cyclic).
ABC ~ BCA ~ CAB.
Group size: n (cyclic group).
Up to n distinct rotations of an n-chord succession;
fewer if the succession is periodic
(e.g., ABAB has only 2 distinct rotations, not 4).

D Dihedral (rotation and retrograde combined).
Group size: 2n.
The rotations of the succession *and* the rotations of its retrograde.
R and C are both subgroups of D.

P Permutation.
Group size: n! (symmetric group).
Any re-ordering of the n chords
("linear permutation" in the sense of reordering the succession).
Note that this does not concern the internal (unordered) contents of each individual chord.
Up to n! orderings, or
n! / (m_1! * m_2! * ...) if some chords are repeated m_i times.
D is a subgroup of P for n >= 3.


Content equivalences
--------------------

Content equivalences are the same as for ChordBigram,
simply applied to successions of any length n >= 2.

"" None:
Chords compared as exact (root pitch-class, quality) pairs.

I Inversion:
Every chord in the succession has its quality flipped (major<>minor, same root)
without changing the class.
Inversion is perhaps the most ambiguous equivalence,
but for parity we match Murphy exactly.

K Key/transposition:
the whole succession may be transposed by any number of semitones
(the same transposition applied to every chord).

IK I and K combined.


Order and content equivalences combined
---------------------------------------

Order and content equivalences are independent axes and combine freely.
This gives 5 x 4 = 20 named equivalence regimes:

Ø   R   C   D   P
I   IR  IC  ID  IP
K   KR  KC  KD  KP
IK  IKR IKC IKD IKP

For n = 2, C, D, and P all coincide with R.
With only two chords reversal, rotation, and permutation all amount to
only and exactly tw0 options.

Two ChordNgram objects are equal iff they share the same equivalence
regime and the same canonical form.

<small>**Author**: Mark Gotham</small>

"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence

from amads.core.chord import Chord

__author__ = "Mark Gotham"


# ---------------------------------------------------------------------------

# Equivalence regime names

_CONTENT_CODES = ("", "I", "K", "IK")
_ORDER_CODES = ("Ø", "R", "C", "D", "P")
_ORDER_SUFFIX = {"Ø": "", "R": "R", "C": "C", "D": "D", "P": "P"}


def _make_equivalence_table() -> dict:
    table = {}
    for content in _CONTENT_CODES:
        for order in _ORDER_CODES:
            label = content + _ORDER_SUFFIX[order]
            if label == "":
                label = "Ø"
            table[label] = (content, order)
    return table


_EQUIVALENCE_TABLE = _make_equivalence_table()
EQUIVALENCES = set(_EQUIVALENCE_TABLE)  # the 20 valid regime labels

# Content lattice: "" < I, "" < K, I < IK, K < IK.
_CONTENT_LEQ = {
    "": {"", "I", "K", "IK"},
    "I": {"I", "IK"},
    "K": {"K", "IK"},
    "IK": {"IK"},
}

# Order lattice: Ø < R, Ø < C, R < D, C < D, D < P.
_ORDER_LEQ = {
    "Ø": {"Ø", "R", "C", "D", "P"},
    "R": {"R", "D", "P"},
    "C": {"C", "D", "P"},
    "D": {"D", "P"},
    "P": {"P"},
}


# ---------------------------------------------------------------------------

# Order-equivalence groups.


def _order_group_identity(n: int) -> list:
    """
    Returns a list of index-permutations (tuples of length n).
    Applying permutation p to a sequence `seq` means: tuple(seq[i] for i in p).
    """
    return [tuple(range(n))]


def _order_group_retrograde(n: int) -> list:
    """See note at `_order_group_identity()`"""
    idx = tuple(range(n))
    return [idx, idx[::-1]]


def _order_group_rotation(n: int) -> list:
    """See note at `_order_group_identity()`"""
    idx = tuple(range(n))
    return [idx[i:] + idx[:i] for i in range(n)]


def _order_group_dihedral(n: int) -> list:
    """See note at `_order_group_identity()`"""
    rotations = _order_group_rotation(n)
    reversed_idx = tuple(range(n))[::-1]
    reversed_rotations = [reversed_idx[i:] + reversed_idx[:i] for i in range(n)]
    seen = []
    for p in rotations + reversed_rotations:
        if p not in seen:
            seen.append(p)
    return seen


_MAX_PERMUTATION_N = 8
# Set for now (may change).
# 8! = 40320 which is quite enough to be testing full enumerations on.
# For what it's worth, there are also not so many > 8 chord loops.


def _order_group_permutation(n: int) -> list:
    """See note at `_order_group_identity()`"""
    if n > _MAX_PERMUTATION_N:
        raise ValueError(
            f"'P' equivalence enumerates n! orderings; "
            f"n={n} is too large (limit {_MAX_PERMUTATION_N})."
        )
    return list(permutations(range(n)))


_ORDER_GROUPS = {
    "Ø": _order_group_identity,
    "R": _order_group_retrograde,
    "C": _order_group_rotation,
    "D": _order_group_dihedral,
    "P": _order_group_permutation,
}


# ---------------------------------------------------------------------------

# Content-equivalence groups.


def _flip(quality: str) -> str:
    """
    Takes a sequence of (pitch_class, quality) atoms
    (in some fixed order) and
    returns a list of "content-equivalent" sequences of atoms,
    in that *same* order
    (content transforms act pointwise/globally and never touch position).
    """
    if quality == "major":
        return "minor"
    elif quality == "minor":
        return "major"
    raise ValueError("quality must be 'major' or 'minor'.")


def _content_group_none(seq: tuple) -> list:
    """See note at `_flip()`"""
    return [seq]


def _content_group_inversion(seq: tuple) -> list:
    """See note at `_flip()`"""
    flipped = tuple((pc, _flip(q)) for pc, q in seq)
    return [seq, flipped]


def _content_group_key(seq: tuple) -> list:
    """See note at `_flip()`"""
    return [tuple(((pc + k) % 12, q) for pc, q in seq) for k in range(12)]


def _content_group_inversion_key(seq: tuple) -> list:
    """See note at `_flip()`"""
    out = []
    for variant in _content_group_inversion(seq):
        out.extend(_content_group_key(variant))
    return out


_CONTENT_GROUPS = {
    "": _content_group_none,
    "I": _content_group_inversion,
    "K": _content_group_key,
    "IK": _content_group_inversion_key,
}


# ---------------------------------------------------------------------------

# Canonical forms


def _canonical_ngram(seq: tuple, content: str, order: str) -> tuple:
    """
    Lexicographically-minimal representative
    of the orbit of `seq`
    under the (order x content)
    group for this equivalence regime.

    Order and content transforms commute
    (order permutes chord *positions*;
    content transforms act the same way regardless of position),
    so the orbit is simply every content-transform of every
    order-permutation of `seq`.
    """
    order_group = _ORDER_GROUPS[order](len(seq))
    content_group_fn = _CONTENT_GROUPS[content]

    best = None
    for perm in order_group:
        reordered = tuple(seq[i] for i in perm)
        for variant in content_group_fn(reordered):
            if best is None or variant < best:
                best = variant
    return best


def _q(quality: str) -> str:
    if quality == "major":
        return "M"
    elif quality == "minor":
        return "m"
    raise ValueError("quality must be 'major' or 'minor'.")


# ---------------------------------------------------------------------------

# ChordNgram


class ChordNgram:
    """
    A succession of n >= 2 chords classified under a given equivalence
    regime, combining a *content* axis ("", I, K, IK -- as in
    ChordBigram) with an *order* axis (Ø, R, C, D, P -- see module
    docstring) into one of 20 named regimes.

    Parameters
    ----------
    chords      : sequence of >= 2 Chord objects, in performance order
    equivalence : one of the 20 labels in `EQUIVALENCES`:
                  "Ø", "R", "C", "D", "P" (content-exact, varying order)
                  "I", "IR", "IC", "ID", "IP" (+ inversion)
                  "K", "KR", "KC", "KD", "KP" (+ transposition)
                  "IK", "IKR", "IKC", "IKD", "IKP" (+ both)

    Examples
    --------
    >>> C = Chord(0, "major")
    >>> E = Chord(4, "major")
    >>> G = Chord(7, "major")

    Plain order axis: rotation-equivalent successions match under
    "C" (cyclic rotation) ...

    >>> ChordNgram([C, E, G], "C") == ChordNgram([E, G, C], "C")
    True

    ... but a non-cyclic reordering does not:

    >>> ChordNgram([C, E, G], "C") == ChordNgram([C, G, E], "C")
    False

    Permutation ("P") equivalence is order-blind altogether.
    Demo on the same case as was False above:

    >>> ChordNgram([C, E, G], "P") == ChordNgram([C, G, E], "P")
    True

    Retrograde ("R") only relates a succession to its exact reversal:

    >>> ChordNgram([C, E, G], "R") == ChordNgram([G, E, C], "R")
    True
    >>> ChordNgram([C, E, G], "R") == ChordNgram([E, G, C], "R")
    False

    Dihedral ("D") accepts rotations of the retrograde too:

    >>> ChordNgram([C, E, G], "D") == ChordNgram([G, C, E], "D")
    True

    With only two chords, R, C, D, and P all coincide
    (same canonical form;
    equality also requires matching regime labels,
    so compare ``.canonical`` directly here):

    >>> a, b, c, d = (ChordNgram([C, E], eq) for eq in ("R", "C", "D", "P"))
    >>> a.canonical == b.canonical == c.canonical == d.canonical
    True
    >>> ChordNgram([C, E], "R") == ChordNgram([E, C], "R")
    True

    Key/transposition ("K") equivalence, order held exact:

    >>> A = Chord(9, "major")
    >>> Cis = Chord(1, "major")
    >>> ChordNgram([C, E, G], "K") == ChordNgram([A, Cis, E], "K")
    True

    Inversion ("I") equivalence flips *all* qualities together:

    >>> Cm, Em, Gm = Chord(0, "minor"), Chord(4, "minor"), Chord(7, "minor")
    >>> ChordNgram([C, E, G], "I") == ChordNgram([Cm, Em, Gm], "I")
    True

    Flipping only *some* qualities is not I-equivalent:

    >>> ChordNgram([C, E, G], "I") == ChordNgram([Cm, E, G], "I")
    False

    Combined regime (IKP):
    transposition + inversion + any reordering.
    E.g., C-E-G major transposed up a perfect 4th (-> F-A-C major),
    with every quality flipped (-> Fm-Am-Cm),
    and reordered (-> Am-Cm-Fm):

    >>> Fm, Am, Cm = Chord(5, "minor"), Chord(9, "minor"), Chord(0, "minor")
    >>> ChordNgram([C, E, G], "IKP") == ChordNgram([Am, Cm, Fm], "IKP")
    True

    Counting distinct orderings (accounting for repeats), matching the
    combinatorics described in the module docstring:

    >>> ChordNgram([C, E, G], "P").order_group_size  # 3! = 6, all distinct
    6
    >>> A2 = Chord(9, "major")
    >>> ChordNgram([C, A2, C, A2], "P").order_group_size  # ABAB: 4!/(2!2!) = 6
    6
    >>> ChordNgram([C, A2, C, A2], "C").order_group_size  # ABAB: only 2 distinct rotations
    2
    """

    def __init__(
        self,
        chords: Sequence[Chord],
        equivalence: str = "Ø",
    ) -> None:
        if len(chords) < 2:
            raise ValueError("ChordNgram requires at least 2 chords.")
        if equivalence not in EQUIVALENCES:
            raise ValueError(f"equivalence must be one of {EQUIVALENCES}")

        self.chords = list(chords)
        self.equivalence = equivalence
        self._content, self._order = _EQUIVALENCE_TABLE[equivalence]

        self._raw_seq = tuple(
            (c.root.pitch_class, c.quality) for c in self.chords
        )
        self._canonical = _canonical_ngram(
            self._raw_seq, self._content, self._order
        )

    @property
    def n(self) -> int:
        """Number of chords in the succession."""
        return len(self.chords)

    @property
    def canonical(self) -> tuple:
        return self._canonical

    @property
    def order_group_size(self) -> int:
        """
        Number of *distinct* orderings of this succession's chords
        that are reachable under this regime's order-equivalence group alone
        (with content held exact).
        Reduced automatically for repeated chords (periodic successions),
        e.g., ABAB has
        2 distinct rotations (not 4) and
        6 distinct permutations (not 24).
        """
        perms = _ORDER_GROUPS[self._order](self.n)
        seq = self._raw_seq
        return len({tuple(seq[i] for i in p) for p in perms})

    def coarsen(self, equivalence: str) -> "ChordNgram":
        """
        Return a new ChordNgram under a coarser (or equal) equivalence regime,
        i.e., one reachable by moving up in both the content
        lattice ("" -> I, K -> IK) and the order lattice
        (Ø -> R, C -> D -> P) independently.

        TODO this behaviour may change.
        """
        if equivalence not in EQUIVALENCES:
            raise ValueError(f"equivalence must be one of {EQUIVALENCES}")
        target_content, target_order = _EQUIVALENCE_TABLE[equivalence]
        if target_content not in _CONTENT_LEQ[self._content]:
            raise ValueError(
                f"Cannot coarsen content '{self._content}' to "
                f"'{target_content}': not a valid coarsening"
            )
        if target_order not in _ORDER_LEQ[self._order]:
            raise ValueError(
                f"Cannot coarsen order '{self._order}' to "
                f"'{target_order}': not a valid coarsening"
            )
        return ChordNgram(self.chords, equivalence)

    @property
    def labels(self) -> dict:
        """
        Dict of labels under every equivalence regime reachable
        (by coarsening) from self.equivalence.
        """
        reachable = [
            content + _ORDER_SUFFIX[order] or "Ø"
            for content in _CONTENT_LEQ[self._content]
            for order in _ORDER_LEQ[self._order]
        ]
        return {eq: self.coarsen(eq).label for eq in reachable}

    # ------------------------------------------------------------------

    # Label

    @property
    def label(self) -> str:
        """
        Short descriptive label with
        chord root and qualities in the given order,
        and the equivalence regime, e.g., 'CM-Em-GM |P'.

        Unlike ChordBigram.label,
        this does not attempt to reproduce Murphy's near/far glyph conventions
        (those are specific to the 2-chord case);
        it is a plain, order-preserving,
        human-readable rendering of the succession as given,
        alongside the regime under which it is being compared.
        """
        chord_strs = [f"{c.root.name}{_q(c.quality)}" for c in self.chords]
        return f"{'-'.join(chord_strs)} |{self.equivalence}"

    # ------------------------------------------------------------------

    # Equality / hashing

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChordNgram):
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
        chord_strs = [f"{c.root.name}:{c.quality}" for c in self.chords]
        return f"ChordNgram({self.equivalence}: " f"{' -> '.join(chord_strs)})"


if __name__ == "__main__":
    import doctest

    doctest.testmod()
