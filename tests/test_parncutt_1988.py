import pytest

from amads.harmony.root_finding.parncutt import ParncuttRootAnalysis


def test_get_root_strength():
    """Test the get_root_strength method of ParncuttRootAnalysis."""
    analysis = ParncuttRootAnalysis([0, 4, 7], root_support_weights="v2")

    # Test with v2 weights
    assert (
        analysis.get_root_strength(0) == 10 + 3 + 5
    )  # Root + perfect fifth + major third
    assert analysis.get_root_strength(1) == 0  # No intervals from this pc
    assert analysis.get_root_strength(2) == 2 + 1  # Minor third + major second
    assert analysis.get_root_strength(4) == 10  # Root from perspective of this pc


def test_parn88_regression():
    """Test regression against known values from Parncutt (1988): Table 4"""

    # Helper function to test root ambiguity
    def test_ambiguity(expected, *chord, digits=1):
        analysis = ParncuttRootAnalysis(list(chord), root_support_weights="v1")
        assert round(analysis.root_ambiguity, digits) == expected

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
    """Test sanity checks for get_root finding and ambiguity"""
    # Test root finding
    analysis1 = ParncuttRootAnalysis([0, 4, 7])
    assert analysis1.root == 0

    analysis2 = ParncuttRootAnalysis([1, 4, 9])
    assert analysis2.root == 9

    # Test that diminished triad has higher ambiguity than major triad
    analysis3 = ParncuttRootAnalysis([0, 3, 6])
    analysis4 = ParncuttRootAnalysis([0, 4, 7])
    assert analysis3.root_ambiguity > analysis4.root_ambiguity


def test_root_support_versions():
    """Test different root support versions"""
    chord = [0, 4, 7, 10]  # Dominant seventh

    # Both should identify the same root
    analysis1 = ParncuttRootAnalysis(chord, root_support_weights="v1")
    analysis2 = ParncuttRootAnalysis(chord, root_support_weights="v2")
    assert analysis1.root == analysis2.root

    # But they should give different ambiguity values
    assert analysis1.root_ambiguity != analysis2.root_ambiguity


def test_available_root_support_weights():
    """Test the available root support weights"""
    # Test that both versions are available
    assert "v1" in ParncuttRootAnalysis.available_root_support_weights
    assert "v2" in ParncuttRootAnalysis.available_root_support_weights

    # Test that v1 has the expected values
    v1_weights = ParncuttRootAnalysis.available_root_support_weights["v1"]
    assert v1_weights[0] == 1.0
    assert v1_weights[7] == 1 / 2
    assert v1_weights[4] == 1 / 3

    # Test that v2 has the expected values
    v2_weights = ParncuttRootAnalysis.available_root_support_weights["v2"]
    assert v2_weights[0] == 10
    assert v2_weights[7] == 5
    assert v2_weights[4] == 3


def test_invalid_root_support_weights():
    """Test that invalid root support weights raise an error"""
    with pytest.raises(ValueError):
        ParncuttRootAnalysis([0, 4, 7], root_support_weights="invalid")


def test_empty_chord():
    """Test that an empty chord raises an error"""
    with pytest.raises(ValueError):
        ParncuttRootAnalysis([])
