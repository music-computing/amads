"""
Archimedean tonnetz.

Boland and Hughston (2026), Section 5
instroduces this as a second chord graph based on
the same twenty-four major and minor triads as the Euler tonnetz,
but with a different adjacency relation.

Given a major triad,
keep one tone fixed and alter the other two to give three kind of minor triads:
those a fifth above and below (preserving root / fifth),
and what's known in Riemannian circles as the "slide" transform (preserving third).
For `CM`, this gives
`Fm` (fifth "down"),
`Gm` (fifth "up"),
and `C#m` ("slide").

Note that the PLR transforms switch mode and preserve two tones,
these switch mode and preserve one.
Boland and Hughston (after Morris 1998)
call this set P', L' and R', the "obverse" of P, L and R:
CM -> Fm preserves C and is called L' (the obverse of L which preserves E and G);
CM -> C#m preserves E and is P', (the obverse of P preserving C, G);
and CM -> Gm preserves G and is R', (the obverse of R, preserving C and A).

Unlike the Euler tonnetz's Levi graph, this graph is not connected:
it splits into two components of twelve triads each,
six major and six minor, shown as the two halves of Figure 11.
It is also not a Levi graph in Boland and Hughston's sense, since it
has girth of only 4 (< 6) as demonstrated in
Section 5's `<Gm, F#M, C#m, CM>` tetracycle.

No new vertex set is needed for this tonnetz.
It reuses `EulerTonnetz`'s twenty-four faces,
exactly as `LeviGraph` does,
differing only in which pairs of triads count as adjacent.

See module notes at `tonnetze/base.py`.
<small>**Author**: Mark Gotham</small>

"""

from typing import Dict, FrozenSet, Iterable, Tuple

from amads.harmony.tonnetze.base import Face
from amads.harmony.tonnetze.euler import EulerTonnetz
from amads.harmony.tonnetze.graph import BipartiteGraph
from amads.harmony.tonnetze.levi import is_major_triad

__author__ = "Mark Gotham"


def shared_elements(
    a: Iterable,
    b: Iterable,
) -> int:
    """
    Basic shared function returning the number of shared elements in any pair of iterables
    `a` and `b`.

    Note: Currently, this returns the count.
    May change to return the shared element.
    May also move or be refactored.

    Examples
    --------
    `CM` and `Fm` share only the tone C.
    >>> shared_elements((0, 4, 7), (5, 8, 0))
    1

    `CM` and `Am` share two tones, C and E.

    >>> shared_elements((0, 4, 7), (9, 0, 4))
    2

    """
    return len(frozenset(a) & frozenset(b))


def shares_one_tone(face_a: Face, face_b: Face) -> bool:
    """
    Basic wrapped of `shared_elements`
    to check whether two Faces
    (assumed to be triads)
    share exactly one element
    (pitch class).

    Note: may move and/or be refactored

    Examples
    --------
    `CM` and `Fm` share only the tone C.

    >>> shares_one_tone((0, 4, 7), (5, 8, 0))
    True

    `CM` and `Am` share two tones, C and E, so this is false.

    >>> shares_one_tone((0, 4, 7), (9, 0, 4))
    False
    """
    return shared_elements(frozenset(face_a), frozenset(face_b)) == 1


def _archimedean_adjacency(
    faces: Tuple[Face, ...],
) -> Dict[Face, FrozenSet[Face]]:
    """
    Builds the two-tone-change adjacency over the given triads,
    restricted to major-minor pairs, following `shares_one_tone`.
    """
    adjacency: Dict[Face, FrozenSet[Face]] = {}
    for face_a in faces:
        neighbors = frozenset(
            face_b
            for face_b in faces
            if face_b != face_a
            and is_major_triad(face_a) != is_major_triad(face_b)
            and shares_one_tone(face_a, face_b)
        )
        adjacency[face_a] = neighbors
    return adjacency


class ArchimedeanTonnetz:
    """
    The Archimedean tonnetz,
    following Boland and Hughston (2026), Section 5.

    Wraps the two-tone-change graph on the same twenty-four triads as `EulerTonnetz`,
    split into its two connected components,
    each a `BipartiteGraph` of twelve major and minor triads.

    Attributes
    ----------
    components : Tuple[BipartiteGraph, BipartiteGraph]
        The tonnetz's two connected components, in a fixed order:
        `components[0]` is the one containing `CM`,
        matching Boland and Hughston's Figure 11.

    Examples
    --------
    Two components of twelve triads each, six major and six minor.

    >>> tonnetz = ArchimedeanTonnetz()
    >>> [len(c.vertices) for c in tonnetz.components]
    [12, 12]
    >>> [(len(c.part_true), len(c.part_false)) for c in tonnetz.components]
    [(6, 6), (6, 6)]

    Every vertex has degree three.

    >>> sorted({c.degree(v) for c in tonnetz.components for v in c.vertices})
    [3]

    `CM` is in the first component, following Figure 11.

    >>> (0, 4, 7) in tonnetz.components[0].vertices
    True

    Girth is four (so not a Levi graph, per Section 5):

    >>> tonnetz.components[0].girth
    4

    The tetracycle `<Gm, F#M, C#m, CM>` example from Section 5,
    regardless of which vertex the canonical form happens to start from.

    >>> named_cycle = frozenset({(7, 10, 2), (6, 10, 1), (1, 4, 8), (0, 4, 7)})
    >>> any(
    ...     frozenset(cycle) == named_cycle
    ...     for cycle in tonnetz.components[0].cycles_of_length(4)
    ... )
    True
    """

    def __init__(self):
        faces = EulerTonnetz().faces
        adjacency = _archimedean_adjacency(faces)
        whole_graph = BipartiteGraph(faces, adjacency, is_major_triad)
        raw_components = whole_graph.connected_components()

        def contains_c_major(component: FrozenSet[Face]) -> bool:
            return (0, 4, 7) in component

        ordered = sorted(raw_components, key=contains_c_major, reverse=True)
        self.components: Tuple[BipartiteGraph, BipartiteGraph] = tuple(
            BipartiteGraph(
                sorted(component, key=str),
                {face: adjacency[face] for face in component},
                is_major_triad,
            )
            for component in ordered
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
