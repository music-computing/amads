"""
Tests for `archimedean.py`,
reproducing Boland and Hughston (2026)'s Appendix:
the cycle-count table for the Archimedean tonnetz.

The Appendix table is for one component of the Archimedean tonnetz,
Figure 11: row totals 3, 20, 24, 48, 12 for lengths 4-12 (total of 107).

The two components are isomorphic, so either gives the same table;
`components[0]`, containing `CM`, is used throughout.
"""

import pytest

from amads.harmony.tonnetze.archimedean import (
    ArchimedeanTonnetz,
    shares_one_tone,
)


@pytest.fixture(scope="module")
def archimedean():
    return ArchimedeanTonnetz()


def test_two_isomorphic_components(archimedean):
    """
    Section 5: two components, each with 12 triads, 6 major and 6 minor.
    """
    assert len(archimedean.components) == 2
    for component in archimedean.components:
        assert len(component.vertices) == 12
        assert len(component.part_true) == 6
        assert len(component.part_false) == 6
        assert {component.degree(v) for v in component.vertices} == {3}


def test_c_major_in_first_component(archimedean):
    """
    Figure 11 shows `CM` in the first of the two Archimedean tonnetze.
    """
    assert (0, 4, 7) in archimedean.components[0].vertices
    assert (0, 4, 7) not in archimedean.components[1].vertices


def test_girth_four_not_a_levi_graph(archimedean):
    """
    Section 5: the Archimedean tonnetz has girth four,
    so it is not a Levi graph
    (unlike the Eulerian tonnetz which is a Levi graph).
    """
    assert archimedean.components[0].girth == 4
    assert archimedean.components[0].is_bipartite()
    assert archimedean.components[0].is_regular_within_parts()
    assert archimedean.components[0].is_simple()


def test_shares_one_tone():
    """
    Section 5: `CM` reaches `Fm`, `Gm` and `C#m`, each sharing exactly
    one tone with `CM`, and no others.
    """
    c_major = (0, 4, 7)
    f_minor = (5, 8, 0)
    g_minor = (7, 10, 2)
    c_sharp_minor = (1, 4, 8)
    a_minor = (9, 0, 4)
    assert shares_one_tone(c_major, f_minor)
    assert shares_one_tone(c_major, g_minor)
    assert shares_one_tone(c_major, c_sharp_minor)
    assert not shares_one_tone(c_major, a_minor)


def test_named_tetracycle(archimedean):
    """
    Section 5: the tetracycle `<Gm, F#M, C#m, CM>`.
    """
    named_cycle = frozenset({(7, 10, 2), (6, 10, 1), (1, 4, 8), (0, 4, 7)})
    cycles = archimedean.components[0].cycles_of_length(4)
    assert any(frozenset(cycle) == named_cycle for cycle in cycles)


def test_named_fanfare_hexacycle(archimedean):
    """
    Figure 13's "Fanfare for Kepler":
    the hexacycle `<CM, C#m, AbM, Am, EM, Fm, CM>`,
    each triad differing from its successor by exactly two tones.
    """
    named_cycle = frozenset(
        {
            (0, 4, 7),  # CM
            (1, 4, 8),  # C#m
            (8, 0, 3),  # AbM
            (9, 0, 4),  # Am
            (4, 8, 11),  # EM
            (5, 8, 0),  # Fm
        }
    )
    cycles = archimedean.components[0].cycles_of_length(6)
    assert any(frozenset(cycle) == named_cycle for cycle in cycles)


@pytest.mark.parametrize(
    "length, expected_total",
    [(4, 3), (6, 20), (8, 24), (10, 48), (12, 12)],
)
def test_cycle_count_by_length(archimedean, length, expected_total):
    """
    Row totals of the Appendix's Archimedean tonnetz table.
    """
    assert (
        len(archimedean.components[0].cycles_of_length(length))
        == expected_total
    )


def test_grand_total(archimedean):
    """
    Appendix: the Archimedean tonnetz admits 107 cycles in total.

    This sums row totals directly, rather than via `cycle_table`,
    since the Appendix's p-number columns for this tonnetz classify
    edges by Boland and Hughston's P', L', R' obverse relations.

    Note the p-number columns of this table are not reproduced,
    only the row and grand totals, which do not depend on it.
    """
    lengths = (4, 6, 8, 10, 12)
    grand_total = sum(
        len(archimedean.components[0].cycles_of_length(length))
        for length in lengths
    )
    assert grand_total == 107
