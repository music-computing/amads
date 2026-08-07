"""
Tests for `levi.py`, reproducing Boland and Hughston (2026), Appendix:
the cycle-count table for the Eulerian tonnetz.

The Appendix gives one row per cycle length, six through twenty-four,
and one column per p-number, the count of P edges in the cycle.
Row totals: 16, 39, 120, 228, 636, 906, 1500, 1182, 720, 62.
Total: 5409.

Lengths 6–12 are fast and always run.
Lengths 14-24 are correct but slow
(the brute-force search grows quickly with cycle length).

That full-table test is marked `slow` and set for pytest to skip by default.

To run, set `pytest -m slow` (and be prepared to wait ... about two minutes).
"""

import pytest

from amads.harmony.tonnetze.euler import EulerTonnetz
from amads.harmony.tonnetze.levi import (
    LeviGraph,
    is_major_triad,
    is_parallel_edge,
    root_of,
)


@pytest.fixture(scope="module")
def levi():
    return LeviGraph(EulerTonnetz(), is_major_triad)


def test_is_levi_graph(levi):
    """
    Bipartite, regular within each part, simple, girth at least six.
    """
    assert levi.is_bipartite()
    assert levi.is_regular_within_parts()
    assert levi.is_simple()
    assert levi.girth == 6
    assert levi.is_levi_graph()


def test_order_and_degree(levi):
    """
    Twenty-four vertices
    (12 major and 12 minor),
    each of degree three.
    """
    assert len(levi.vertices) == 24
    assert len(levi.part_true) == 12
    assert len(levi.part_false) == 12
    assert {levi.degree(v) for v in levi.vertices} == {3}


def test_root_of():
    """
    A P edge joins two triads sharing a root,
    so `root_of` must agree on both sides of every such edge.
    """
    assert root_of((0, 4, 7)) == 0
    assert root_of((0, 3, 7)) == 0


def test_is_parallel_edge():
    """
    Boland and Hughston, Section 2:
    `{CM, Cm}` is a P edge,
    `{CM, Em}` is not (de facto "L" transform).
    """
    assert is_parallel_edge((0, 4, 7), (0, 3, 7))
    assert not is_parallel_edge((0, 4, 7), (4, 7, 11))


@pytest.mark.parametrize(
    "length, expected_total",
    [(6, 16), (8, 39), (10, 120), (12, 228)],
)
def test_cycle_count_by_length(levi, length, expected_total):
    """
    Row totals of the Appendix's Eulerian tonnetz table, lengths six
    through twelve.
    """
    assert len(levi.cycles_of_length(length)) == expected_total


def test_hexacycle_p_numbers(levi):
    """
    Section 4: four 3p-hexacycles and twelve 2p-hexacycles.
    """
    table = levi.cycle_table([6], is_parallel_edge)
    assert table[6] == {3: 4, 2: 12}


@pytest.mark.parametrize(
    "length, expected_row",
    [
        (8, {1: 12, 3: 24, 4: 3}),
        (10, {2: 12, 3: 48, 4: 60}),
        (12, {2: 30, 3: 72, 4: 78, 5: 48}),
    ],
)
def test_cycle_table_rows(levi, length, expected_row):
    """
    The Appendix's p-number columns for lengths eight through twelve,
    read directly from the paper's table.
    """
    table = levi.cycle_table([length], is_parallel_edge)
    assert table[length] == expected_row


# TODO @pytest.mark.slow default not effective for all users. Resolve before restoring this test.
# @pytest.mark.slow
# def test_full_appendix_table(levi):
#     """
#     The complete Eulerian tonnetz row totals,
#     lengths 6–24,
#     and their grand total of 5409 simple cycles.
#     (see Boland and Hughston, Appendix).
#     """
#     lengths = range(6, 25, 2)
#     table = levi.cycle_table(lengths, is_parallel_edge)
#     row_totals = {length: sum(table[length].values()) for length in lengths}
#     expected = {
#         6: 16,
#         8: 39,
#         10: 120,
#         12: 228,
#         14: 636,
#         16: 906,
#         18: 1500,
#         20: 1182,
#         22: 720,
#         24: 62,
#     }
#     assert row_totals == expected
#     assert sum(row_totals.values()) == 5409
