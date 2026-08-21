import pytest

from amads.harmony.tonnetze.g2 import (
    AUGMENTED_TRIADS,
    DIMINISHED_SEVENTHS,
    FLIP_PARTNER,
    G2Tonnetz,
    langlands_dual_chord,
)


def test_12_wedges_alternate_major_minor():
    tonnetz = G2Tonnetz()
    for wedge in range(12):
        assert tonnetz.major_not_minor(wedge) == (wedge % 2 == 0)


def test_all_12_chords_are_distinct():
    tonnetz = G2Tonnetz()
    chords = [tonnetz.chord(w) for w in range(12)]
    assert len(set(chords)) == 12


def test_roots_ascend_by_fifths():
    """Reading the wedges in order visits every pitch class, up a fifth each step."""
    tonnetz = G2Tonnetz()
    for wedge in range(12):
        this_root = tonnetz.root(wedge)
        next_root = tonnetz.root(tonnetz.rotate_clockwise(wedge))
        assert (next_root - this_root) % 12 == 7


def test_majors_on_one_whole_tone_scale_minors_on_the_other():
    tonnetz = G2Tonnetz()
    major_roots = {
        tonnetz.root(w) for w in range(12) if tonnetz.major_not_minor(w)
    }
    minor_roots = {
        tonnetz.root(w) for w in range(12) if not tonnetz.major_not_minor(w)
    }
    assert major_roots == {0, 2, 4, 6, 8, 10}
    assert minor_roots == {1, 3, 5, 7, 9, 11}


def test_d_major_is_wedge_0():
    tonnetz = G2Tonnetz()
    assert tonnetz.chord(0) == frozenset({2, 6, 9})
    assert tonnetz.major_not_minor(0)


def test_rotate_clockwise_and_anticlockwise_are_inverses():
    tonnetz = G2Tonnetz()
    for wedge in range(12):
        assert (
            tonnetz.rotate_anticlockwise(tonnetz.rotate_clockwise(wedge))
            == wedge
        )
        assert (
            tonnetz.rotate_clockwise(tonnetz.rotate_anticlockwise(wedge))
            == wedge
        )


def test_flip_is_an_involution():
    tonnetz = G2Tonnetz()
    for wedge in range(12):
        assert tonnetz.flip(tonnetz.flip(wedge)) == wedge


def test_flip_partner_is_a_perfect_matching():
    """Every wedge appears in exactly one flip pair, covering all 12 exactly once."""
    assert set(FLIP_PARTNER.keys()) == set(range(12))
    assert set(FLIP_PARTNER.values()) == set(range(12))
    for wedge, partner in FLIP_PARTNER.items():
        assert FLIP_PARTNER[partner] == wedge


def test_d_major_flips_to_e_flat_minor():
    """Confirmed directly against the figure's colour-coded gluing."""
    tonnetz = G2Tonnetz()
    flipped = tonnetz.flip(0)
    assert tonnetz.chord(flipped) == frozenset({3, 6, 10})
    assert not tonnetz.major_not_minor(flipped)


def test_every_wedge_has_exactly_3_distinct_neighbors():
    tonnetz = G2Tonnetz()
    for wedge in range(12):
        neighbors = {
            tonnetz.rotate_clockwise(wedge),
            tonnetz.rotate_anticlockwise(wedge),
            tonnetz.flip(wedge),
        }
        assert len(neighbors) == 3


def test_augmented_triads_partition_the_whole_tone_scale():
    """The 2 augmented triads together cover all 6 major roots, no overlap."""
    assert len(AUGMENTED_TRIADS) == 2
    assert AUGMENTED_TRIADS[0].isdisjoint(AUGMENTED_TRIADS[1])
    assert AUGMENTED_TRIADS[0] | AUGMENTED_TRIADS[1] == frozenset(
        {0, 2, 4, 6, 8, 10}
    )


def test_diminished_sevenths_partition_the_chromatic_scale():
    """The 3 diminished sevenths together cover all 12 pitch classes, no overlap."""
    assert len(DIMINISHED_SEVENTHS) == 3
    union = frozenset()
    for chord in DIMINISHED_SEVENTHS:
        assert union.isdisjoint(chord)
        union |= chord
    assert union == frozenset(range(12))


def test_vertex_valences_and_euler_characteristic():
    """
    Exhaustive structural check,
    reconstructing the underlying 6-vertex graph from the wedge/rotation/flip data,
    and confirming it matches Rietsch (2024), Section 4:
    a torus with 1 valence-12 vertex, 2 valence-6 vertices, and 3 valence-4 vertices.
    """
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent.get(x, x)
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for wedge in range(12):
        union((wedge, "R"), ((wedge + 1) % 12, "L"))
    for wedge, partner in FLIP_PARTNER.items():
        union((wedge, "L"), (partner, "R"))
        union((wedge, "R"), (partner, "L"))

    slots = [(w, side) for w in range(12) for side in ("L", "R")]
    classes = {}
    for slot in slots:
        classes.setdefault(find(slot), []).append(slot)

    valences = sorted(len(v) for v in classes.values())
    assert len(classes) == 5  # non-center vertices
    assert valences == [4, 4, 4, 6, 6]

    vertices = 1 + len(classes)  # + center
    edges = 12 + 6  # 12 spokes + 6 outer edges (see docstring in g2.py)
    faces = 12
    assert vertices - edges + faces == 0  # torus


@pytest.mark.parametrize("wedge", range(12))
def test_chord_root_and_quality_are_mutually_consistent(wedge):
    tonnetz = G2Tonnetz()
    chord = tonnetz.chord(wedge)
    root = tonnetz.root(wedge)
    assert root in chord
    third = (
        (root + 4) % 12 if tonnetz.major_not_minor(wedge) else (root + 3) % 12
    )
    fifth = (root + 7) % 12
    assert chord == frozenset({root, third, fifth})


def test_langlands_dual_chord_is_p_transform():
    """Same root, major<->minor swap: D major <-> D minor."""
    d_major = frozenset({2, 6, 9})
    d_minor = frozenset({2, 5, 9})
    assert langlands_dual_chord(d_major) == d_minor
    assert langlands_dual_chord(d_minor) == d_major


def test_langlands_dual_chord_is_an_involution():
    for root in range(12):
        major = frozenset({root, (root + 4) % 12, (root + 7) % 12})
        assert langlands_dual_chord(langlands_dual_chord(major)) == major


def test_langlands_dual_of_all_12_wedges_is_exactly_the_remaining_12_triads():
    """
    Applying Langlands duality to every triad in G2Tonnetz gives exactly the 12
    major/minor triads absent from it.
    """
    tonnetz = G2Tonnetz()
    this_tonnetz = {tonnetz.chord(w) for w in range(12)}
    dual = {langlands_dual_chord(c) for c in this_tonnetz}

    all_triads = set()
    for root in range(12):
        all_triads.add(frozenset({root, (root + 4) % 12, (root + 7) % 12}))
        all_triads.add(frozenset({root, (root + 3) % 12, (root + 7) % 12}))

    remaining = all_triads - this_tonnetz
    assert dual == remaining
    assert dual.isdisjoint(this_tonnetz)
    assert dual | this_tonnetz == all_triads
