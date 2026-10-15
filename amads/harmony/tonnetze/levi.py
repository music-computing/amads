"""
Levi graph of a tonnetz.

Following Boland and Hughston (2026, Section 2),
a tonnetz can be viewed as a bipartite graph on its chords.

One part of the bipartition holds one type of chord,
the other part holds the other type.
An edge joins two chords whenever they are reachable from one another
by crossing a single shared edge of the tonnetz.

For the Euler tonnetz this is as
Boland and Hughston's Proposition 2.1 and Figure 3:
a regular bipartite graph of degree 3 on the 24 major and minor triads.

We build this directly on the tonnetz structure.
For each face of a Tonnetz, our `Tonnetz.neighbors`
gives the faces reachable by crossing each of its edges (i.e., the neighbour).
A `LeviGraph` simply collects that info across every face
and checks it against the four defining properties of a Levi graph
(Boland and Hughston, Section 2):
bipartite, regular within each part, simple, and of girth at least six.

Boland and Hughston's Section 2
further classifies the tonnetz's edges into three sets of twelve based on the
familiar P (parallel), R (relative), and L (Leittonwechsel) transformations.

A cycle's "p-number" is the count of its P edges
as per the Appendix's cycle-count tables,
whose rows are cycle length and whose columns are p-number.
The `root_of` and `is_parallel_edge` attributes
classify Euler tonnetz edges this way
and the `LeviGraph.cycle_table` (inherited from `graph.BipartiteGraph`),
reproduces the Appendix layout for any chosen set of cycle lengths.

The core cycle-counting machinery lives in `graph.py`,
a set-up that supports reuse it for other chord graphs
both within Boland and Hughston's formulation and otherwise.
For example, the Archimedean tonnetz is not built from crossing edges of a `Tonnetz`.

See module notes at `tonnetze/base.py`.

<small>**Author**: Mark Gotham</small>
"""

from typing import Dict, FrozenSet, Hashable

from amads.harmony.tonnetze.base import Face, Tonnetz
from amads.harmony.tonnetze.graph import BipartiteGraph

__author__ = "Mark Gotham"


class LeviGraph(BipartiteGraph):
    """
    The Levi graph of a tonnetz,
    following Boland and Hughston (2026), Section 2.

    Vertices are the tonnetz's faces.
    Two faces are joined by an edge whenever `Tonnetz.neighbors` reaches
    one from the other, i.e. whenever they share an edge of the tonnetz.
    The `bipartition` function splits the faces into two parts, such as
    major and minor triads for the Euler tonnetz.

    Boland and Hughston, Section 2,
    give four properties that characterise a Levi graph among bipartite graphs:
    bipartite,
    simple,
    girth is at least six,
    and each part is internally regular
    (of some degree r for one part, k for the other).
    These are checked at construction time and reported by `is_levi_graph`.

    Parameters
    ----------
    tonnetz : Tonnetz
        The tonnetz whose faces become this graph's vertices.
    bipartition : Callable[[Face], bool]
        Splits the faces into two parts.
        For the Euler tonnetz, `True` for major triads and `False` for
        minor triads, following `is_major_triad`.

    Examples
    --------
    The Euler tonnetz gives Boland and Hughston's Figure 3:
    a regular bipartite graph of degree three on twenty-four vertices.

    >>> from amads.harmony.tonnetze.euler import EulerTonnetz
    >>> levi = LeviGraph(EulerTonnetz(), is_major_triad)
    >>> len(levi.vertices)
    24
    >>> len(levi.part_true), len(levi.part_false)
    (12, 12)
    >>> sorted({levi.degree(v) for v in levi.vertices})
    [3]

    This is exactly Proposition 2.1.

    >>> levi.is_levi_graph()
    True

    Boland and Hughston, Section 4:
    sixteen hexacycles altogether, four 3p-hexacycles and twelve 2p-hexacycles.

    >>> table = levi.cycle_table([6], is_parallel_edge)
    >>> table[6]
    {3: 4, 2: 12}
    """

    def __init__(self, tonnetz: Tonnetz, bipartition):
        adjacency: Dict[Face, FrozenSet[Face]] = {
            face: frozenset(tonnetz.neighbors(face).values())
            for face in tonnetz.faces
        }
        super().__init__(tonnetz.faces, adjacency, bipartition)

    def is_levi_graph(self) -> bool:
        """
        Checks all four of Boland and Hughston's defining properties
        for a Levi graph, Section 2:
        - bipartite,
        - regular within each part,
        - simple, and
        - girth of at least six.
        """
        return (
            self.is_bipartite()
            and self.is_regular_within_parts()
            and self.is_simple()
            and self.girth >= 6
        )


def is_major_triad(face: Face) -> bool:
    """
    Checks whether a triad is a major triad.

    Used as the `bipartition` for `LeviGraph` applied to `EulerTonnetz`.
    Specficially, this splits the faces into
    major triads -> `True`,
    and minor triads -> `False`,
    as per Boland and Hughston (2026), Figure 3.

    Also used for the Archimedean tonnetz, (Section 5),
    whose vertices are the same twenty-four triads.

    Note: may be refactored.

    Examples
    --------

    C major
    >>> is_major_triad((0, 4, 7))
    True

    C minor
    >>> is_major_triad((0, 3, 7))
    False

    C#/Db major
    >>> is_major_triad((1, 5, 8))
    True
    """
    pitch_classes = frozenset(face)
    return any(
        (p + 4) % 12 in pitch_classes and (p + 7) % 12 in pitch_classes
        for p in pitch_classes
    )


def root_of(face: Face) -> Hashable:
    """
    Returns a triad's root pitch class.

    Works for either a major or minor triad,
    using `is_major_triad` to decide which interval pattern to look for.

    Note: limited to major/minor and may be refactored.

    Examples
    --------
    >>> root_of((0, 4, 7))
    0

    >>> root_of((0, 3, 7))
    0

    >>> is_major_triad((1, 5, 8))
    1
    """
    pitch_classes = frozenset(face)
    third_interval = 4 if is_major_triad(face) else 3
    return next(
        p
        for p in pitch_classes
        if (p + third_interval) % 12 in pitch_classes
        and (p + 7) % 12 in pitch_classes
    )


def is_parallel_edge(face_a: Face, face_b: Face) -> bool:
    """
    Checks whether two adjacent triads are joined by a P (parallel) transform.

    Following Boland and Hughston, Section 2:
    a P edge joins a major triad to the minor triad on the same root,
    (e.g., `{CM, Cm}` in their syntax where M is a major triad and m is minor).

    Examples
    --------
    C major and C minor share a root: a P edge.

    >>> is_parallel_edge((0, 4, 7), (0, 3, 7))
    True

    C major and E minor do not: an L edge instead.

    >>> is_parallel_edge((0, 4, 7), (4, 7, 11))
    False
    """
    return root_of(face_a) == root_of(face_b)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
