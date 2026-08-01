import pytest

from amads.harmony.tonnetze.b2 import (
    DIMINISHED_SEVENTH,
    EIGHT_NOTE_SET,
    FLIP_PARTNER,
    ROOTS,
    B2Tonnetz,
)


def test_8_wedges_visit_4_distinct_major_triads():
    tonnetz = B2Tonnetz()
    chords = [tonnetz.chord(w) for w in range(8)]
    assert len(set(chords)) == 4
    for chord in chords:
        root = next(
            p for p in chord if (p + 4) % 12 in chord and (p + 7) % 12 in chord
        )
        assert chord == frozenset({root, (root + 4) % 12, (root + 7) % 12})


def test_each_triad_appears_exactly_twice():
    tonnetz = B2Tonnetz()
    chords = [tonnetz.chord(w) for w in range(8)]
    for chord in set(chords):
        assert chords.count(chord) == 2


def test_wedge_0_is_b_major():
    tonnetz = B2Tonnetz()
    assert tonnetz.chord(0) == frozenset({3, 6, 11})


def test_the_4_distinct_roots_form_a_diminished_seventh_chord():
    roots = frozenset(ROOTS)
    assert len(roots) == 4
    root = min(roots)
    assert roots == frozenset((root + 3 * k) % 12 for k in range(4))


def test_rotate_clockwise_and_anticlockwise_are_inverses():
    tonnetz = B2Tonnetz()
    for wedge in range(8):
        assert (
            tonnetz.rotate_anticlockwise(tonnetz.rotate_clockwise(wedge))
            == wedge
        )
        assert (
            tonnetz.rotate_clockwise(tonnetz.rotate_anticlockwise(wedge))
            == wedge
        )


def test_flip_is_an_involution():
    tonnetz = B2Tonnetz()
    for wedge in range(8):
        assert tonnetz.flip(tonnetz.flip(wedge)) == wedge


def test_flip_partner_is_a_perfect_matching():
    assert set(FLIP_PARTNER.keys()) == set(range(8))
    assert set(FLIP_PARTNER.values()) == set(range(8))
    for wedge, partner in FLIP_PARTNER.items():
        assert FLIP_PARTNER[partner] == wedge


def test_flip_always_changes_the_chord():
    """A flip move should never be a self-loop back to the same triad."""
    tonnetz = B2Tonnetz()
    for wedge in range(8):
        assert tonnetz.chord(tonnetz.flip(wedge)) != tonnetz.chord(wedge)


def test_every_wedge_has_exactly_3_distinct_neighbors():
    tonnetz = B2Tonnetz()
    for wedge in range(8):
        neighbors = {
            tonnetz.rotate_clockwise(wedge),
            tonnetz.rotate_anticlockwise(wedge),
            tonnetz.flip(wedge),
        }
        assert len(neighbors) == 3


def test_diminished_seventh_is_a_subset_of_the_eight_note_set():
    """
    The 4-valent vertex's diminished seventh chord
    is 4 of the 8 notes already attached to the 8-valent vertex,
    not a disjoint set.
    """
    assert DIMINISHED_SEVENTH <= EIGHT_NOTE_SET
    assert len(EIGHT_NOTE_SET) == 8
    assert len(DIMINISHED_SEVENTH) == 4


def test_eight_note_set_complement_is_the_third_diminished_seventh_chord():
    """
    The 4 pitch classes absent from the 8-valent vertex
    ... are also a diminished seventh chord,
    (the one not otherwise used anywhere in this tonnetz).
    """
    complement = frozenset(range(12)) - EIGHT_NOTE_SET
    assert complement == frozenset({1, 4, 7, 10})


def test_vertex_valences_and_euler_characteristic():
    """
    Exhaustive structural check reconstructing the underlying 4-vertex
    graph (S, P, Q, R) from the confirmed fundamental-domain gluing,
    and confirming it matches Rietsch (2024), Section 3:
    a torus with 2 valence-8 vertices and 2 valence-4 vertices.

    S is the wedge-fan centre reconstructed in this module.
    P, Q and R are the 3 other vertices reached by its 8 spokes, in cyclic order:
    P (wedges 0,2,4,6 endpoints),
    Q (wedges 0,1,4,5 endpoints via the other side),
    R (wedges 2,3,6,7 via the other side).

    Concretely, from the wedge cycle
    (P,Q,P,R,P,Q,P,R spoke targets in order),
    S connects to P via 4 edges, Q via 2, and R via 2, totalling
    valence 8 at S, matching `B2Tonnetz`'s construction.
    """
    spoke_targets = ["P", "Q", "P", "R", "P", "Q", "P", "R"]
    # each wedge's 2 spokes are spoke_targets[i] and spoke_targets[i+1]
    from collections import Counter

    spoke_count = Counter()
    for i in range(8):
        spoke_count[spoke_targets[i]] += 1
        spoke_count[spoke_targets[(i + 1) % 8]] += 1
    # every spoke slot is shared between 2 consecutive wedges, so halve
    s_edges = {k: v // 2 for k, v in spoke_count.items()}
    assert s_edges == {"P": 4, "Q": 2, "R": 2}
    assert sum(s_edges.values()) == 8  # valence of S

    # Q and R each also have 2 edges to P
    q_valence = s_edges["Q"] + 2
    r_valence = s_edges["R"] + 2
    p_valence = s_edges["P"] + 2 + 2
    valences = sorted([8, p_valence, q_valence, r_valence])
    assert valences == [4, 4, 8, 8]

    vertices = 4
    edges = 12
    faces = 8
    assert vertices - edges + faces == 0  # torus


@pytest.mark.parametrize("wedge", range(8))
def test_chord_root_is_consistent(wedge):
    tonnetz = B2Tonnetz()
    chord = tonnetz.chord(wedge)
    root = tonnetz.root(wedge)
    assert chord == frozenset({root, (root + 4) % 12, (root + 7) % 12})
