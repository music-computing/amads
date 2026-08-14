"""
B2 Tonnetz.
See main module notes at `tonnetze/base.py`

<small>**Author**: Mark Gotham</small>

"""

from typing import FrozenSet, Tuple

__author__ = "Mark Gotham"


ROOTS: Tuple[int, ...] = (11, 2, 2, 5, 5, 8, 8, 11)
"""
The root pitch class of each of the 8 wedges, wedge 0 being B.
Going around the cycle visits 4 distinct triads, each twice in a row
(e.g., B, D, D, F, F, Ab, Ab, B),
wrapping back to the start.
The 4 distinct roots, B, D, F, Ab, outline a diminished seventh chord.
"""

FLIP_PARTNER = {0: 5, 5: 0, 1: 4, 4: 1, 2: 7, 7: 2, 3: 6, 6: 3}
"""
The wedge reached by crossing a wedge's 3rd edge,
(the one not touching the center vertex).
"""

EIGHT_NOTE_SET: FrozenSet[int] = frozenset({0, 2, 3, 5, 6, 8, 9, 11})
"""
The pitch classes attached to each of the tonnetz's 2 eight-valent vertices.
Both eight-valent vertices carry this same set of 8 distinct notes.
"""

DIMINISHED_SEVENTH: FrozenSet[int] = frozenset({0, 3, 6, 9})
"""
The pitch classes attached to each of the tonnetz's 2 four-valent vertices.
Both four-valent vertices carry this same diminished seventh chord.
"""


class B2Tonnetz:
    """
    Rietsch's B2 edge tonnetz: an entirely major-triad tonnetz.

    8 triangular faces, arranged around a torus,
    encoding 4 distinct major triads.

    Each face is called a "wedge" here and identified by an index 0-7.
    Going around the cycle of wedges visits 4 distinct triads,
    each twice in a row:
    e.g., B, D, F and Ab major.
    See `ROOTS`.

    This is an edge tonnetz: single notes live on edges rather than vertices.
    The underlying graph has 4 vertices:
    2 of valence 8, both carrying the same 8 distinct notes,
    (`EIGHT_NOTE_SET`);
    and 2 of valence 4, both carrying the same diminished seventh chord,
    (`DIMINISHED_SEVENTH`).

    Because several of the edges touching one of the 8-valent vertices
    lead to the same other vertex, carrying different pitch classes,
    that underlying graph has parallel edges between some vertex pairs.

    Our `tonnetz.base.Tonnetz` cannot currently represent parallel edges,
    so this class is implemented here directly, in the wedge index,
    rather than as a `Tonnetz` subclass, (same approach as `tonnetz.g2.G2Tonnetz`).

    Every wedge has exactly 3 neighbours, reached by 3 transforms.
    2 of a wedge's 3 edges touch one particular 8-valent vertex
    (the centre of the wedge fan reconstructed here),
    and crossing either one steps to the next or previous wedge in the cycle above.

    The "3rd edge" does not touch that vertex, and crossing it reaches
    another wedge elsewhere in the same 8-wedge cycle, given by `FLIP_PARTNER`.

    Examples
    --------
    Wedge 0 is B major.

    >>> tonnetz = B2Tonnetz()
    >>> sorted(tonnetz.chord(0))
    [3, 6, 11]

    Rotating clockwise from wedge 1 repeats D major, then moves to F major.

    >>> tonnetz.root(tonnetz.rotate_clockwise(1)) == tonnetz.root(1)
    True
    >>> sorted(tonnetz.chord(tonnetz.rotate_clockwise(tonnetz.rotate_clockwise(1))))
    [0, 5, 9]

    Flipping from wedge 0 reaches Ab major.

    >>> flipped = tonnetz.flip(0)
    >>> sorted(tonnetz.chord(flipped))
    [0, 3, 8]

    Flipping is an involution.

    >>> tonnetz.flip(flipped) == 0
    True
    """

    def __init__(self):
        self._chords: Tuple[FrozenSet[int], ...] = tuple(
            self._wedge_chord(i) for i in range(8)
        )

    @staticmethod
    def _wedge_chord(wedge: int) -> FrozenSet[int]:
        root = ROOTS[wedge]
        return frozenset((root + interval) % 12 for interval in (0, 4, 7))

    def chord(self, wedge: int) -> FrozenSet[int]:
        """
        Returns the pitch classes of the major triad at the given wedge, 0-7.
        """
        return self._chords[wedge % 8]

    def root(self, wedge: int) -> int:
        """
        Returns the root pitch class of the triad at the given wedge, 0-7.
        """
        return ROOTS[wedge % 8]

    def rotate_clockwise(self, wedge: int) -> int:
        """
        Steps to the next wedge in the cycle.

        Crosses one of the 2 edges touching the wedge fan's center vertex.
        """
        return (wedge + 1) % 8

    def rotate_anticlockwise(self, wedge: int) -> int:
        """
        Steps to the previous wedge in the cycle.

        Crosses the other edge touching the wedge fan's center vertex.
        Undoes `rotate_clockwise`.
        """
        return (wedge - 1) % 8

    def flip(self, wedge: int) -> int:
        """
        Crosses the wedge's 3rd edge, the one not touching the wedge
        fan's center vertex.

        See `FLIP_PARTNER`.
        An involution: flipping twice returns to the starting wedge.
        """
        return FLIP_PARTNER[wedge % 8]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
