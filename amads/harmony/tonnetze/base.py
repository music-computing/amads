""""
Much harmonic transformation functionality is described on a "Tonnetz" representation of tonal space.

The best known Tonnetz is that described by Euler [1]
and later adopted by Riemannian, "neo-Riemannian" scholars, and others.

This module and directory generalises and extends this to include more recent work
by Konstanze Rietsch [2]
and Boland & Hughston [3].

These extensions include
placement of pitches on edges rather than vertices
and tesselation based on pitch combinations other than major/minor triads.

This directory includes
core, shared files including:
- base.py which is a generic Tonnetz class for vertices/edges/faces, labelling, and transforms;
_pitch_io.py which is a shared adapter for taking a List/Chord/PitchCollection to an octave-preserving MIDI multiset.
and Tonnetz-specific modules including:
- euler
- b2, c2, g2 ... (after Rietsch)
- levi, ... (after Boland & Hughston).

See specific modules, classes etc. for more detail on each.

References
----------
[1] Euler, Leonhard (1739). Tentamen novae theoriae musicae ex certissismis harmoniae principiis
dilucide expositae. Saint Petersburg Academy.
[2] Konstanze Rietsch (2024) Generalizations of Euler's Tonnetz on triangulated surfaces,
Journal of Mathematics and Music, 18:3, 328-346, DOI: 10.1080/17459737.2024.2362132
https://doi.org/10.1080/17459737.2024.2362132
[3] Jeﬀrey R. Boland & Lane P. Hughston (2026):
Configurations, tessellations and tone networks,
Journal of Mathematics and Music, DOI: 10.1080/17459737.2026.2678317
https://doi.org/10.1080/17459737.2026.2678317

<small>**Author**: Mark Gotham</small>

"""

from typing import Dict, FrozenSet, Hashable, Iterable, List, Optional, Tuple

__author__ = "Mark Gotham"

Vertex = Hashable
Face = Tuple[Vertex, ...]
Edge = FrozenSet[Vertex]


class Tonnetz:
    """
    A polygonal-surface tonnetz.

    Follows the abstraction of Rietsch (2024), Definition 2.1,
    and its polygonal generalization in Rietsch forthcoming, Definition 3.1.

    A tonnetz is a graph of vertices,
    tiled by polygonal faces,
    with a labelling of either the vertices or the edges by pitch classes.

    Each face represents a chord.
    In a vertex tonnetz, the chord is the pitch classes of the face's bounding vertices.
    In an edge tonnetz, the chord is the pitch classes of the face's bounding edges instead.

    Concrete examples include Euler's tonnetz (as an exmaple of the vertex tonnetz),
    and Rietsch's B2, C2 and G2 (examples of edge tonnetze).

    This class stores only combinatorial structure and labels.
    It has no notion of a particular geometric embedding or surface,
    and no notion of key or tonic.
    The Tonnetz assumes a closed, orientable, manifold surface
    (i.e., looping around a space like a torus):
    every edge must border exactly one other face, or `neighbors`/`transform` will
    raise a `ValueError`.

    Concrete tonnetze such as the Euler tonnetz
    are built by supplying a fixed set of faces and a labelling.

    Parameters
    ----------
    faces : Iterable[Tuple[Vertex, ...]]
        The faces of the tonnetz.
        Each face is a tuple of abstract vertex ids,
        given in cyclic order around the face.
        A face with 3 vertices is a triangle representing a chord.
    vertex_labels : Dict[Vertex, int], optional
        Maps each abstract vertex id to a pitch class in 0-11.
        If neither `vertex_labels` nor `edge_labels` is given,
        vertex ids are used directly as pitch classes,
        so vertex ids must then themselves be integers in 0-11.
    edge_labels : Dict[FrozenSet[Vertex], int], optional
        Maps each edge to a pitch class in 0-11.
        Every edge appearing in `faces` must have a label.
        Mutually exclusive with `vertex_labels`.

    Attributes
    ----------
    faces : Tuple[Tuple[Vertex, ...], ...]
        The faces, as given.
    vertices : FrozenSet[Vertex]
        All vertex ids appearing in any face.
    vertex_labels : Optional[Dict[Vertex, int]]
        If this is a vertex tonnetz,
        the vertex-to-pitch-class labeling,
        otherwise `None`.
    edge_labels : Optional[Dict[FrozenSet[Vertex], int]]
        If this is an edge tonnetz,
        the edge-to-pitch-class labeling,
        otherwise `None`.

    Examples
    --------
    A minimal vertex tonnetz: two triangles sharing an edge.

    >>> faces = [(0, 1, 2), (1, 2, 3)]
    >>> tonnetz = Tonnetz(faces)
    >>> tonnetz.vertices == frozenset({0, 1, 2, 3})
    True

    >>> tonnetz.face_pitch_classes((0, 1, 2))
    frozenset({0, 1, 2})

    >>> tonnetz.faces_containing({1, 2, 3})
    [(1, 2, 3)]

    Crossing the shared edge {1, 2} moves between the two faces.

    >>> tonnetz.transform((0, 1, 2), frozenset({1, 2}))
    (1, 2, 3)
    >>> tonnetz.transform((1, 2, 3), frozenset({1, 2}))
    (0, 1, 2)

    The same two faces, now as an edge tonnetz instead,
    with a pitch class on every edge rather than every vertex.

    >>> edge_labels = {
    ...     frozenset({0, 1}): 0, frozenset({1, 2}): 4, frozenset({0, 2}): 7,
    ...     frozenset({2, 3}): 9, frozenset({1, 3}): 2,
    ... }
    >>> edge_tonnetz = Tonnetz(faces, edge_labels=edge_labels)
    >>> edge_tonnetz.face_pitch_classes((0, 1, 2))
    frozenset({0, 4, 7})

    """

    def __init__(
        self,
        faces: Iterable[Face],
        vertex_labels: Optional[Dict[Vertex, int]] = None,
        edge_labels: Optional[Dict[Edge, int]] = None,
    ):
        if vertex_labels is not None and edge_labels is not None:
            raise ValueError(
                "Provide `vertex_labels` or `edge_labels`, not both."
            )

        self.faces: Tuple[Face, ...] = tuple(tuple(face) for face in faces)
        self.vertices: FrozenSet[Vertex] = frozenset(
            v for face in self.faces for v in face
        )
        all_edges: FrozenSet[Edge] = frozenset(
            edge for face in self.faces for edge in self.face_edges(face)
        )

        if edge_labels is not None:
            missing = all_edges - edge_labels.keys()
            if missing:
                raise ValueError(
                    f"No pitch-class label given for edges: {missing}."
                )
            invalid = {
                edge: label
                for edge, label in edge_labels.items()
                if edge in all_edges and not 0 <= label <= 11
            }
            if invalid:
                raise ValueError(
                    f"Edge labels must be pitch classes 0-11: {invalid}."
                )
            self.edge_labels: Optional[Dict[Edge, int]] = edge_labels
            self.vertex_labels: Optional[Dict[Vertex, int]] = None
        else:
            if vertex_labels is None:
                vertex_labels = {v: v for v in self.vertices}
            missing = self.vertices - vertex_labels.keys()
            if missing:
                raise ValueError(
                    f"No pitch-class label given for vertices: {sorted(missing, key=str)}."
                )
            invalid = {
                v: label
                for v, label in vertex_labels.items()
                if v in self.vertices and not 0 <= label <= 11
            }
            if invalid:
                raise ValueError(
                    f"Vertex labels must be pitch classes 0-11: {invalid}."
                )
            self.vertex_labels = vertex_labels
            self.edge_labels = None

        self._edge_to_faces = self._build_edge_to_faces()
        self._vertex_to_edges = self._build_vertex_to_edges(all_edges)

    def _build_edge_to_faces(self) -> Dict[Edge, List[Face]]:
        """
        Maps each edge to the faces that border it.
        An edge is a pair of vertices,
        adjacent within some face,
        taken cyclically around that face.
        """
        edge_to_faces: Dict[Edge, List[Face]] = {}
        for face in self.faces:
            for edge in self.face_edges(face):
                edge_to_faces.setdefault(edge, []).append(face)
        return edge_to_faces

    @staticmethod
    def _build_vertex_to_edges(
        edges: FrozenSet[Edge],
    ) -> Dict[Vertex, List[Edge]]:
        """
        Maps each vertex to the edges incident to it.
        """
        vertex_to_edges: Dict[Vertex, List[Edge]] = {}
        for edge in edges:
            for vertex in edge:
                vertex_to_edges.setdefault(vertex, []).append(edge)
        return vertex_to_edges

    @staticmethod
    def face_edges(face: Face) -> List[Edge]:
        """
        Returns the edges bounding a face,
        taken cyclically around the face.

        Examples
        --------
        >>> Tonnetz.face_edges((0, 1, 2))
        [frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})]
        """
        n = len(face)
        return [frozenset((face[i], face[(i + 1) % n])) for i in range(n)]

    def face_pitch_classes(self, face: Face) -> FrozenSet[int]:
        """
        Returns the pitch classes of a face's chord.
        In a vertex tonnetz, these are the pitch classes of the face's vertices.
        In an edge tonnetz, these are the pitch classes of the face's edges.
        """
        if self.edge_labels is not None:
            return frozenset(
                self.edge_labels[edge] for edge in self.face_edges(face)
            )
        return frozenset(self.vertex_labels[v] for v in face)

    def vertex_multiset(self, vertex: Vertex) -> Tuple[int, ...]:
        """
        Returns the multiset of pitch classes attached to a vertex.

        In an edge tonnetz,
        this is the pitch class of every edge incident to the vertex,
        following Rietsch (2024), Lemma 2.6(2),
        and can vary in content, not just multiplicity, from vertex to vertex.

        In a vertex tonnetz, this is the vertex's own single pitch class,
        repeated once per incident edge,
        following Lemma 2.6(1).

        Examples
        --------
        >>> edge_labels = {
        ...     frozenset({0, 1}): 0, frozenset({1, 2}): 4, frozenset({0, 2}): 7,
        ...     frozenset({2, 3}): 9, frozenset({1, 3}): 2,
        ... }
        >>> tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)], edge_labels=edge_labels)
        >>> sorted(tonnetz.vertex_multiset(2))
        [4, 7, 9]
        """
        incident_edges = self._vertex_to_edges.get(vertex, [])
        if self.edge_labels is not None:
            return tuple(self.edge_labels[edge] for edge in incident_edges)
        return tuple(self.vertex_labels[vertex] for _ in incident_edges)

    def faces_containing(self, pitch_classes: Iterable[int]) -> List[Face]:
        """
        Finds all faces whose pitch classes exactly match the given set.
        This is typically used to locate the face representing a given chord.

        Examples
        --------
        >>> tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
        >>> tonnetz.faces_containing([2, 3, 1])
        [(1, 2, 3)]
        """
        target = frozenset(pitch_classes)
        return [
            face
            for face in self.faces
            if self.face_pitch_classes(face) == target
        ]

    def neighbors(self, face: Face) -> Dict[Edge, Face]:
        """
        Finds the faces adjacent to a given face,
        keyed by the shared edge.

        On a closed surface with no boundary,
        every edge borders exactly one other face.

        Boundary edges, bordering no other face, are omitted.

        An edge bordering more than one other face raises an error,
        since that should not occur on a well-formed surface.

        Examples
        --------
        >>> tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
        >>> tonnetz.neighbors((0, 1, 2))
        {frozenset({1, 2}): (1, 2, 3)}
        """
        result = {}
        for edge in self.face_edges(face):
            others = [f for f in self._edge_to_faces[edge] if f != face]
            if len(others) == 0:
                continue
            if len(others) > 1:
                raise ValueError(
                    f"Edge {edge} borders more than one other face."
                )
            result[edge] = others[0]
        return result

    def transform(self, face: Face, edge: Edge) -> Face:
        """
        Crosses the given edge of a face,
        returning the neighboring face on the other side.
        This is the generic move underlying named transforms,
        such as the neo-Riemannian P, L and R transforms.

        Parameters
        ----------
        face : Tuple[Vertex, ...]
            The starting face.
        edge : FrozenSet[Vertex]
            One of the edges bounding `face`.

        Returns
        -------
        Tuple[Vertex, ...]
            The unique other face sharing that edge.

        Raises
        ------
        ValueError
            If `edge` does not border `face`,
            or does not border exactly one other face.

        Examples
        --------
        >>> tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
        >>> tonnetz.transform((0, 1, 2), frozenset({1, 2}))
        (1, 2, 3)
        """
        if edge not in self.face_edges(face):
            raise ValueError(f"Edge {edge} does not border face {face}.")
        others = [f for f in self._edge_to_faces[edge] if f != face]
        if len(others) != 1:
            raise ValueError(
                f"Edge {edge} does not border exactly one other face."
            )
        return others[0]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
