import pytest

from amads.harmony.tonnetze.base import Tonnetz


def test_vertices_and_faces():
    """A tonnetz collects all vertices appearing in any face."""
    tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
    assert tonnetz.faces == ((0, 1, 2), (1, 2, 3))
    assert tonnetz.vertices == frozenset({0, 1, 2, 3})


def test_default_labels_are_identity():
    """With no labels given, vertex ids are used directly as pitch classes."""
    tonnetz = Tonnetz([(0, 1, 2)])
    assert tonnetz.vertex_labels == {0: 0, 1: 1, 2: 2}
    assert tonnetz.edge_labels is None


def test_custom_vertex_labels():
    """Abstract vertex ids can be labeled by pitch classes independently of their id."""
    tonnetz = Tonnetz([("a", "b", "c")], vertex_labels={"a": 0, "b": 4, "c": 7})
    assert tonnetz.face_pitch_classes(("a", "b", "c")) == frozenset({0, 4, 7})


def test_missing_vertex_label_raises():
    """Every vertex appearing in a face must have a label."""
    with pytest.raises(ValueError):
        Tonnetz([("a", "b", "c")], vertex_labels={"a": 0, "b": 4})


def test_edge_tonnetz_face_pitch_classes_come_from_edges_not_vertices():
    """In an edge tonnetz, a face's chord is read off its edges, not its vertices."""
    edge_labels = {
        frozenset({0, 1}): 0,
        frozenset({1, 2}): 4,
        frozenset({0, 2}): 7,
    }
    tonnetz = Tonnetz([(0, 1, 2)], edge_labels=edge_labels)
    assert tonnetz.vertex_labels is None
    assert tonnetz.face_pitch_classes((0, 1, 2)) == frozenset({0, 4, 7})


def test_missing_edge_label_raises():
    """Every edge appearing in a face must have a label, in an edge tonnetz."""
    edge_labels = {frozenset({0, 1}): 0, frozenset({1, 2}): 4}
    with pytest.raises(ValueError):
        Tonnetz([(0, 1, 2)], edge_labels=edge_labels)


def test_vertex_labels_and_edge_labels_are_mutually_exclusive():
    with pytest.raises(ValueError):
        Tonnetz([(0, 1, 2)], vertex_labels={0: 0, 1: 1, 2: 2}, edge_labels={})


def test_vertex_multiset_in_a_vertex_tonnetz_repeats_the_single_label():
    """In a vertex tonnetz, a vertex's multiset is its own label, once per incident edge."""
    tonnetz = Tonnetz(
        [(0, 1, 2)]
    )  # vertex 0 has 2 incident edges: {0,1} and {0,2}
    assert tonnetz.vertex_multiset(0) == (0, 0)


def test_vertex_multiset_in_an_edge_tonnetz_can_vary():
    """In an edge tonnetz, a vertex's multiset is the labels of its incident edges."""
    edge_labels = {
        frozenset({0, 1}): 0,
        frozenset({1, 2}): 4,
        frozenset({0, 2}): 7,
        frozenset({2, 3}): 9,
        frozenset({1, 3}): 2,
    }
    tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)], edge_labels=edge_labels)
    assert sorted(tonnetz.vertex_multiset(2)) == [4, 7, 9]
    assert sorted(tonnetz.vertex_multiset(1)) == [0, 2, 4]


def test_face_edges_triangle():
    """A triangle's edges are all 3 pairs of its vertices."""
    edges = Tonnetz.face_edges((0, 1, 2))
    assert set(edges) == {
        frozenset({0, 1}),
        frozenset({1, 2}),
        frozenset({0, 2}),
    }


def test_face_edges_square_are_cyclic_not_all_pairs():
    """A 4-gon's edges are only the 4 cyclically consecutive pairs, not all 6."""
    edges = Tonnetz.face_edges((0, 1, 2, 3))
    assert set(edges) == {
        frozenset({0, 1}),
        frozenset({1, 2}),
        frozenset({2, 3}),
        frozenset({0, 3}),
    }
    assert frozenset({0, 2}) not in edges


def test_face_pitch_classes():
    """A face's pitch classes are its vertices' labels."""
    tonnetz = Tonnetz([(0, 4, 7), (0, 3, 7)])
    assert tonnetz.face_pitch_classes((0, 4, 7)) == frozenset({0, 4, 7})


def test_faces_containing_finds_matching_chord():
    """faces_containing locates the face whose pitch classes match a given chord."""
    tonnetz = Tonnetz([(0, 4, 7), (0, 3, 7)])
    assert tonnetz.faces_containing([7, 0, 4]) == [(0, 4, 7)]


def test_faces_containing_no_match_returns_empty():
    """A pitch-class set matching no face returns an empty list, not an error."""
    tonnetz = Tonnetz([(0, 4, 7)])
    assert tonnetz.faces_containing([1, 2, 3]) == []


def test_neighbors_two_triangles_sharing_an_edge():
    """Two triangles sharing an edge are each other's only neighbor, via that edge."""
    tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
    assert tonnetz.neighbors((0, 1, 2)) == {frozenset({1, 2}): (1, 2, 3)}
    assert tonnetz.neighbors((1, 2, 3)) == {frozenset({1, 2}): (0, 1, 2)}


def test_neighbors_boundary_edges_are_omitted():
    """An edge bordering no other face is simply absent, not an error."""
    tonnetz = Tonnetz([(0, 1, 2)])
    assert tonnetz.neighbors((0, 1, 2)) == {}


def test_neighbors_raises_if_edge_borders_more_than_one_other_face():
    """A malformed, non-surface-like tonnetz raises rather than silently picking one face."""
    tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3), (1, 2, 4)])
    with pytest.raises(ValueError):
        tonnetz.neighbors((0, 1, 2))


def test_transform_crosses_the_given_edge():
    """transform is the generic move: cross an edge, land on the neighboring face."""
    tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
    assert tonnetz.transform((0, 1, 2), frozenset({1, 2})) == (1, 2, 3)
    assert tonnetz.transform((1, 2, 3), frozenset({1, 2})) == (0, 1, 2)


def test_transform_is_involutive():
    """Crossing back over the same edge returns to the starting face."""
    tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
    edge = frozenset({1, 2})
    start = (0, 1, 2)
    there = tonnetz.transform(start, edge)
    back = tonnetz.transform(there, edge)
    assert back == start


def test_transform_raises_for_edge_not_on_face():
    """The given edge must actually border the given face."""
    tonnetz = Tonnetz([(0, 1, 2), (1, 2, 3)])
    with pytest.raises(ValueError):
        tonnetz.transform((0, 1, 2), frozenset({2, 3}))


def test_transform_raises_at_a_boundary():
    """Crossing an edge with no other face on the far side is an error, not None."""
    tonnetz = Tonnetz([(0, 1, 2)])
    with pytest.raises(ValueError):
        tonnetz.transform((0, 1, 2), frozenset({0, 1}))
