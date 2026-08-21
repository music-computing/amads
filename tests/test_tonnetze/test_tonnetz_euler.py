import pytest

from amads.harmony.tonnetze.euler import EulerTonnetz, EulerTriad


def all_24_triads():
    """The 12 major and 12 minor triads, as pitch-class lists."""
    for root in range(12):
        yield [root, (root + 4) % 12, (root + 7) % 12]  # major
        yield [root, (root + 3) % 12, (root + 7) % 12]  # minor


def test_euler_tonnetz_has_12_vertices_and_24_faces():
    """One vertex per pitch class, one face per major or minor triad."""
    tonnetz = EulerTonnetz()
    assert tonnetz.vertices == frozenset(range(12))
    assert len(tonnetz.faces) == 24


def test_euler_tonnetz_is_a_closed_surface():
    """Every edge borders exactly 2 faces, as required on a torus."""
    tonnetz = EulerTonnetz()
    edge_counts = {}
    for face in tonnetz.faces:
        for edge in tonnetz.face_edges(face):
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    assert set(edge_counts.values()) == {2}


def test_euler_tonnetz_neighbors_of_c_major():
    """C major's 3 neighbors are exactly its P, L and R transforms."""
    tonnetz = EulerTonnetz()
    neighbor_pcs = {
        tuple(sorted(tonnetz.face_pitch_classes(face)))
        for face in tonnetz.neighbors((0, 4, 7)).values()
    }
    assert neighbor_pcs == {
        (0, 3, 7),  # P: c minor
        (4, 7, 11),  # L: e minor
        (0, 4, 9),  # R: a minor
    }


def test_c_major_root_and_quality():
    """A basic sanity check on root-finding and quality detection."""
    triad = EulerTriad([0, 4, 7])
    assert triad.root == 0
    assert triad.major_not_minor is True


def test_c_minor_root_and_quality():
    triad = EulerTriad([0, 3, 7])
    assert triad.root == 0
    assert triad.major_not_minor is False


def test_non_triad_raises():
    """A 4-note chord is not a major or minor triad."""
    with pytest.raises(ValueError):
        EulerTriad([0, 4, 7, 10])


def test_non_major_minor_triad_raises():
    """A diminished triad is not major or minor."""
    with pytest.raises(ValueError):
        EulerTriad([0, 3, 6])


@pytest.mark.parametrize(
    "transform_name, expected_pcs",
    [
        ("parallel", {0, 3, 7}),
        ("leading_tone_exchange", {4, 7, 11}),
        ("relative", {0, 4, 9}),
    ],
)
def test_c_major_named_transforms(transform_name, expected_pcs):
    """P, L and R from C major land on c minor, e minor and a minor respectively."""
    triad = EulerTriad([0, 4, 7])
    getattr(triad, transform_name)()
    attribute = {
        "parallel": "p_transform",
        "leading_tone_exchange": "l_transform",
        "relative": "r_transform",
    }[transform_name]
    result = getattr(triad, attribute)
    assert set(p % 12 for p in result) == expected_pcs


@pytest.mark.parametrize(
    "transform_name", ["parallel", "leading_tone_exchange", "relative"]
)
def test_transforms_preserve_octave_and_duplicates(transform_name):
    """Octave placement and duplicate pitches survive a transform."""
    triad = EulerTriad([60, 60, 64, 67])  # doubled root
    getattr(triad, transform_name)()
    attribute = {
        "parallel": "p_transform",
        "leading_tone_exchange": "l_transform",
        "relative": "r_transform",
    }[transform_name]
    result = getattr(triad, attribute)
    assert len(result) == 4
    assert all(
        p >= 12 for p in result
    )  # still real key numbers, not bare pitch classes


@pytest.mark.parametrize(
    "transform_name", ["parallel", "leading_tone_exchange", "relative"]
)
def test_transforms_are_involutions(transform_name):
    """Applying the same named transform twice returns to the starting chord."""
    for pcs in all_24_triads():
        triad = EulerTriad(pcs)
        getattr(triad, transform_name)()
        attribute = {
            "parallel": "p_transform",
            "leading_tone_exchange": "l_transform",
            "relative": "r_transform",
        }[transform_name]
        once = getattr(triad, attribute)

        triad_again = EulerTriad(list(once))
        getattr(triad_again, transform_name)()
        twice = getattr(triad_again, attribute)

        assert set(twice) == set(pcs)


def test_arithmetic_plr_matches_generic_graph_traversal_for_all_24_triads():
    """
    The arithmetic P, L, R transforms in EulerTriad must exactly match
    the generic edge-crossing neighbors computed by EulerTonnetz's graph,
    for every one of the 24 major and minor triads.
    This is the cross-check between the arithmetic and generic implementations
    agreed on when EulerTonnetz was designed.
    """
    graph = EulerTonnetz()
    for pcs in all_24_triads():
        triad = EulerTriad(pcs)
        triad.parallel()
        triad.leading_tone_exchange()
        triad.relative()

        arithmetic_neighbors = {
            frozenset(p % 12 for p in triad.p_transform),
            frozenset(p % 12 for p in triad.l_transform),
            frozenset(p % 12 for p in triad.r_transform),
        }

        (face,) = graph.faces_containing(pcs)
        graph_neighbors = {
            graph.face_pitch_classes(neighbor)
            for neighbor in graph.neighbors(face).values()
        }

        assert arithmetic_neighbors == graph_neighbors
