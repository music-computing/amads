"""
G2 Tonnetz (a kind of 12-triad wedge).

See module notes at `tonnetze/base.py`

<small>**Author**: Mark Gotham</small>

"""

from typing import FrozenSet, Tuple

__author__ = "Mark Gotham"


ROOTS: Tuple[int, ...] = (2, 9, 4, 11, 6, 1, 8, 3, 10, 5, 0, 7)

FLIP_PARTNER = {
    0: 7,
    7: 0,
    1: 6,
    6: 1,
    2: 9,
    9: 2,
    3: 8,
    8: 3,
    4: 11,
    11: 4,
    5: 10,
    10: 5,
}


AUGMENTED_TRIADS: Tuple[FrozenSet[int], ...] = (
    frozenset({2, 6, 10}),  # D, F#, A#
    frozenset({0, 4, 8}),  # C, E, G#
)

DIMINISHED_SEVENTHS: Tuple[FrozenSet[int], ...] = (
    frozenset({0, 3, 6, 9}),  # C, D#, F#, A
    frozenset({2, 5, 8, 11}),  # D, F, G#, B
    frozenset({1, 4, 7, 10}),  # C#, E, G, A#
)


class G2Tonnetz:
    """
    Rietsch's G2 edge tonnetz: the circle of fifths.
    See Rietsch (2024), Section 4 (figures 5ff).

    Broadly, G2 works as follows.
    There are 12 triads (sic, not 24) in a cycle; 6 major, 6 minor, alternating.
    Within this cycle, a triad (e.g., D major)
    is connection to triads of the opposite mode a fifth higher and lower
    (G minor with the D common, and A minor with the A common).
    The outer edge wraps around, torus style to a corresponding triad that preserves the third,
    so D major maps to Eb minor (Gb shared with the enharmonic F#)
    within the same 12-triad cycle (effectively "across").
    This last transform is equivalent to the "slide" in neo-Riemannian language.

    Each face is called a "wedge" (here, not in Rietsch) and identified by an index 0-11.
    (They are rendered by Rietsch as right-angle triangles.)
    Reading the wedges around one cycle in order gives the circle of fifths across the roots:
    D major, A minor,
    E major, B minor,
    and so on,
    up by a fifth each step (and swithing mode) as discussed above.
    See "langands duel" for the "other" (complementary) 12.

    It bears repeating that this is an edge tonnetz (unlikely Euler's),
    so single notes are positioned on edges rather than vertices,
    following Rietsch (2024), Definition 2.4.
    The underlying graph has 6 vertices:
    a single center vertex, of valence 12, with every pitch class attached to it;
    2 further vertices, of valence 6, each labeled by an augmented triad;
    and 3 more, of valence 4, each labeled by a diminished seventh chord.

    Because 3 of the 12 edges touching the center all lead to the same
    augmented-triad vertex, carrying different pitch classes,
    that underlying graph has parallel edges between some vertex pairs.

    Local implementation note:
    `amads.harmony.tonnetz.base.Tonnetz` cannot currently represent parallel edges,
    so this class is implemented directly,
    in the wedge index, rather than as a `Tonnetz` subclass.
    See `AUGMENTED_TRIADS` and `DIMINISHED_SEVENTHS` for that vertex data and note that
    AUGMENTED_TRIADS partition the whole-tone scale (2 groups of 3 = 6) and the
    DIMINISHED_SEVENTHS partition the total chromatic (3 groups of 4 = 12).
    This design may change.

    Every wedge has exactly 3 neighbours, reached by 3 transforms.
    2 of a wedge's 3 edges touch the centre vertex, and crossing either
    one steps to the next or previous wedge around the circle of fifths
    (as discussed above).
    The 3rd edge (which gives the third of the triad)
    does not touch the centre.
    Crossing that third edge reaches another wedge elsewhere in the same 12-wedge cycle
    (broadly "across"),
    given here by the `FLIP_PARTNER` pairings.

    Examples
    --------
    Wedge 0 is D major.

    >>> tonnetz = G2Tonnetz()
    >>> sorted(tonnetz.chord(0))
    [2, 6, 9]

    Rotating clockwise steps up a fifth, to A minor.

    >>> next_wedge = tonnetz.rotate_clockwise(0)
    >>> sorted(tonnetz.chord(next_wedge))
    [0, 4, 9]

    Rotating counterclockwise undoes it.

    >>> tonnetz.rotate_anticlockwise(next_wedge) == 0
    True

    Flipping from D major reaches E-flat minor.

    >>> flipped = tonnetz.flip(0)
    >>> sorted(tonnetz.chord(flipped))
    [3, 6, 10]

    Flipping is an involution.

    >>> tonnetz.flip(flipped) == 0
    True

    """

    def __init__(self):
        self._chords: Tuple[FrozenSet[int], ...] = tuple(
            self._wedge_chord(i) for i in range(12)
        )

    @staticmethod
    def _wedge_chord(wedge: int) -> FrozenSet[int]:
        root = ROOTS[wedge]
        intervals = (0, 4, 7) if wedge % 2 == 0 else (0, 3, 7)
        return frozenset((root + interval) % 12 for interval in intervals)

    def chord(self, wedge: int) -> FrozenSet[int]:
        """
        Returns the pitch classes of the triad at the given wedge, 0-11.
        """
        return self._chords[wedge % 12]

    def root(self, wedge: int) -> int:
        """
        Returns the root pitch class of the triad at the given wedge, 0-11.
        """
        return ROOTS[wedge % 12]

    def major_not_minor(self, wedge: int) -> bool:
        """
        True if the triad at the given wedge is major, False if minor.
        """
        return wedge % 2 == 0

    def rotate_clockwise(self, wedge: int) -> int:
        """
        Steps to the next wedge around the circle of fifths.

        Crosses one of the 2 edges touching the center vertex.
        """
        return (wedge + 1) % 12

    def rotate_anticlockwise(self, wedge: int) -> int:
        """
        Steps to the previous wedge around the circle of fifths.

        Crosses the other edge touching the center vertex.
        Undoes `rotate_clockwise`.
        """
        return (wedge - 1) % 12

    def flip(self, wedge: int) -> int:
        """
        Crosses the wedge's 3rd edge, the one not touching the center.

        See `FLIP_PARTNER`.
        An involution: flipping twice returns to the starting wedge.
        """
        return FLIP_PARTNER[wedge % 12]


def langlands_dual_chord(chord: FrozenSet[int]) -> FrozenSet[int]:
    """
    Returns the Langlands-dual partner of a major or minor triad.

    The Langlands duality carries a `G2Tonnetz` to a complmentary tonnetz containing
    those "other" 12 triads not in the initial `G2Tonnetz`.
    This has the effect of turning every major triad into the minor
    triad on the same root, and vice versa and so being equivalent to
    the neo-Riemannian P transform (see `amads.harmony.tonnetz.euler`).

    This function only reproduces that set-level fact,
    HOWEVER(!), it does not construct the companion tonnetz's own wedge structure,
    root ordering, or flip pairing, unlike `G2Tonnetz` itself, since
    those would need the same figure-level verification this module's
    other constants received, which has not been done.

    This behaviour may change.

    Examples
    --------
    D major's dual is D minor.

    >>> sorted(langlands_dual_chord(frozenset({2, 6, 9})))
    [2, 5, 9]

    Applying it to every one of `G2Tonnetz`'s 12 triads gives exactly
    the 12 major/minor triads absent from `G2Tonnetz`.

    >>> tonnetz = G2Tonnetz()
    >>> this_tonnetz = {tonnetz.chord(w) for w in range(12)}
    >>> dual = {langlands_dual_chord(c) for c in this_tonnetz}
    >>> all_triads = {
    ...     frozenset({r, (r + third) % 12, (r + 7) % 12})
    ...     for r in range(12) for third in (3, 4)
    ... }
    >>> dual == all_triads - this_tonnetz
    True
    """
    major_root = next(
        (p for p in chord if (p + 4) % 12 in chord and (p + 7) % 12 in chord),
        None,
    )
    if major_root is not None:
        return frozenset(
            {major_root, (major_root + 3) % 12, (major_root + 7) % 12}
        )
    minor_root = next(
        p for p in chord if (p + 3) % 12 in chord and (p + 7) % 12 in chord
    )
    return frozenset({minor_root, (minor_root + 4) % 12, (minor_root + 7) % 12})


if __name__ == "__main__":
    import doctest

    doctest.testmod()
