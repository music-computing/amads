import pytest

from amads.harmony.root_finding.parncutt_1988 import (
    ROOT_SUPPORT_WEIGHTS,
    encode_pc_set,
    parn88,
    pc_weight,
    root,
    root_ambiguity,
)


def test_empty_chord():
    with pytest.raises(ValueError):
        root([])


def test_encode_pc_set():
    assert encode_pc_set([0, 4, 7]) == [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]
    assert encode_pc_set([0]) == [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert encode_pc_set([]) == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def test_pc_weight():
    weights = ROOT_SUPPORT_WEIGHTS["v2"]
    pc_set = encode_pc_set([0, 4, 7])

    assert pc_weight(0, pc_set, weights) == 10 + 3 + 5
    assert pc_weight(1, pc_set, weights) == 0
    assert pc_weight(2, pc_set, weights) == 2 + 1
    assert pc_weight(4, pc_set, weights) == 10


def test_parn88_regression():
    """Test regression against known values from Parncutt (1988): Table 4"""

    # Helper function to test root ambiguity
    def test_ambiguity(expected, *chord, digits=1):
        result = root_ambiguity(list(chord), root_support="v1")
        assert round(result, digits) == expected

    # Dyads
    test_ambiguity(2.2, 0, 1)
    test_ambiguity(2.0, 0, 2)
    test_ambiguity(2.1, 0, 3)
    test_ambiguity(1.9, 0, 4)
    test_ambiguity(1.8, 0, 5)
    test_ambiguity(2.2, 0, 6)

    # Triads
    test_ambiguity(2.0, 0, 4, 7)
    test_ambiguity(2.1, 0, 3, 7)
    test_ambiguity(2.3, 0, 4, 8)
    test_ambiguity(2.5, 0, 3, 6)

    # Sevenths
    test_ambiguity(2.1, 0, 4, 7, 10)
    test_ambiguity(2.3, 0, 3, 7, 10)
    test_ambiguity(2.3, 0, 4, 7, 11)
    test_ambiguity(2.4, 0, 3, 6, 10)
    test_ambiguity(2.9, 0, 3, 6, 9)


def test_sanity_checks():
    """Test sanity checks for root finding and ambiguity"""
    assert root([0, 4, 7]) == 0
    assert root([1, 4, 9]) == 9

    # Test that diminished triad has higher ambiguity than major triad
    assert root_ambiguity([0, 3, 6]) > root_ambiguity([0, 4, 7])


def test_root_support_versions():
    """Test different root support versions"""
    chord = [0, 4, 7, 10]  # Dominant seventh

    # Both should identify the same root
    assert root(chord, root_support="v1") == root(chord, root_support="v2")

    # But they should give different ambiguity values
    assert root_ambiguity(chord, root_support="v1") != root_ambiguity(
        chord, root_support="v2"
    )


def test_custom_root_support():
    """Test with custom root support weights"""
    custom_weights = {0: 1.0, 7: 0.5, 4: 0.3}
    chord = [0, 4, 7]

    result = parn88(chord, root_support=custom_weights)
    assert result["root"] == 0
    assert result["root_ambiguity"] > 0
    assert len(result["pc_weight"]) == 12
