"""Test suite for functions in amads.time.variability"""

import pytest

from amads.time.variability import (
    isochrony_proportion,
    normalized_pairwise_calculation,
    normalized_pairwise_variability_index,
    pairwise_anisochronous_contrast_index,
    phrase_normalized_pairwise_variability_index,
)


def test_daniele_patel_2013_example_1():
    """Tests the first example given in the Appendix of Daniele & Patel (2013, p. 18)"""
    durations = [
        1.0,
        1 / 2,
        1 / 2,
        1.0,
        1 / 2,
        1 / 2,
        1 / 3,
        1 / 3,
        1 / 3,
        2.0,
        1 / 3,
        1 / 3,
        1 / 3,
        1 / 3,
        1 / 3,
        1 / 3,
        3 / 2,
        1.0,
        1 / 2,
    ]
    expected = 42.2
    actual = normalized_pairwise_variability_index(durations)
    assert pytest.approx(actual, abs=1e-1) == expected


def test_daniele_patel_2013_example_2():
    """Tests the second example given in the Appendix of Daniele & Patel (2013, p. 18)"""
    durations = [
        1.0,
        3 / 2,
        1 / 2,
        2 / 3,
        2 / 3,
        2 / 3,
        3 / 2,
        1 / 2,
        3 / 2,
        1 / 2,
        3 / 2,
        1 / 2,
        2 / 3,
        2 / 3,
        2 / 3,
        3 / 2,
        1 / 2,
        3 / 2,
        1 / 2,
        2 / 3,
        2 / 3,
        2 / 3,
        3 / 2,
    ]
    expected = 57.1
    actual = normalized_pairwise_variability_index(durations)
    assert pytest.approx(actual, abs=1e-1) == expected


def test_schultz_figure_1():
    """Tests all the examples given in Figure 1 of Condit-Schultz (2019, p. 301)"""
    all_durations = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1 / 2, 1 / 2, 1.0, 1 / 2, 1 / 2],
        [1.0, 1 / 2, 1.0, 1 / 2],
        [3 / 2, 1 / 2, 3 / 2, 1 / 2],
        [7 / 16, 1 / 16, 7 / 16, 1 / 16],
    ]
    expected_results = [0.0, 40.0, 66.7, 100.0, 150.0]
    for durations, expected in zip(all_durations, expected_results):
        actual = normalized_pairwise_variability_index(durations)
        assert pytest.approx(actual, abs=1e-1) == expected


def test_not_enough_durations():
    """Test we raise an error with not enough durations"""
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([2.0])
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([])


def test_non_positive_durations():
    """Test we raise an error with negative or non-positive durations"""
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([1.0, 0.0, 3.0, 2.0])
    with pytest.raises(ValueError):
        normalized_pairwise_variability_index([3.0, 3.0, -3.0, 2.0])


def test_npvi_is_mean_npc():
    """According to Condit-Schultz (2019), the nPVI is equivalent to the mean nPC"""
    all_durations = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1 / 2, 1 / 2, 1.0, 1 / 2, 1 / 2],
        [1.0, 1 / 2, 1.0, 1 / 2],
        [3 / 2, 1 / 2, 3 / 2, 1 / 2],
        [7 / 16, 1 / 16, 7 / 16, 1 / 16],
    ]
    for dur in all_durations:
        # calculate nPVI using the "original" equation
        x1 = normalized_pairwise_variability_index(dur)
        # calculate nPVI as the mean nPC
        x2 = normalized_pairwise_calculation(dur)
        x2 = sum(x2) / len(x2)
        # should be the same
        assert pytest.approx(x1) == pytest.approx(x2)


def test_isop():
    """Tests the isochrony proportion function"""
    all_durations = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1 / 2, 1 / 2, 1.0, 1 / 2, 1 / 2],
        [1.0, 1 / 2, 1.0, 1 / 2],
        [3 / 2, 1 / 2, 3 / 2, 1 / 2],
        [7 / 16, 1 / 16, 7 / 16, 1 / 16],
    ]
    expecteds = [1.0, 2 / 5, 0.0, 0.0, 0.0]
    for dur, expected in zip(all_durations, expecteds):
        actual = isochrony_proportion(dur)
        assert actual == expected


def test_paci():
    """Tests the pairwise anisochronous contrast index function"""
    # Test with a few example values that contain isochronous pairs: these will be skipped when calculating nPVI
    all_durations = [
        [
            1 / 1,
            1 / 2,
            1 / 2,
            1 / 1,
            1 / 2,
            1 / 2,
        ],  # (1.0, 0.5), (0.5, 1.0), (1.0, 0.5)
        [
            1 / 1,
            1 / 2,
            1 / 2,
            1 / 1,
            1 / 2,
            1 / 2,
            1 / 3,
            1 / 3,
            1 / 3,
        ],  # (1, 1/2), (1/2, 1), (1, 1/2), (1/2, 1/3)
    ]
    expecteds = [66.7, 60.0]
    for dur, expected in zip(all_durations, expecteds):
        npvi = normalized_pairwise_variability_index(dur)
        paci = pairwise_anisochronous_contrast_index(dur)
        # PACI should be equal to expected value
        assert pytest.approx(paci, abs=1e-1) == expected
        # PACI should not be equal to nPVI
        assert not pytest.approx(paci, abs=1e-1) == pytest.approx(npvi, abs=1e-1)

    # Test with examples that have no isochronous pairs, so should be identical to vanilla npvi
    vanillas = [
        [1.0, 1 / 2, 1.0, 1 / 2],
        [3 / 2, 1 / 2, 3 / 2, 1 / 2],
        [7 / 16, 1 / 16, 7 / 16, 1 / 16],
    ]
    expected_results = [66.7, 100.0, 150.0]
    for durs, expected in zip(vanillas, expected_results):
        # Calculate npvi and paci for these values
        npvi = normalized_pairwise_variability_index(durs)
        paci = pairwise_anisochronous_contrast_index(durs)
        # Should be identical
        assert (
            pytest.approx(npvi)
            == pytest.approx(paci)
            == pytest.approx(expected, abs=1e-1)
        )

    # Raise an error with all isochronous pairs
    errors = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    with pytest.raises(ValueError):
        _ = pairwise_anisochronous_contrast_index(errors)


def test_pnpvi():
    """Tests the phrase-normalized pairwise variability index function"""
    all_durations = [
        [1.0, 1 / 2, 1 / 2, 1.0, 1 / 2, 1 / 2],
        [1.0, 1 / 2, 1.0, 1 / 2],
        [3 / 2, 1 / 2, 3 / 2, 1 / 2],
        [7 / 16, 1 / 16, 7 / 16, 1 / 16],
    ]
    all_boundaries = [
        [1.9, 3.5],
        [1.4],
        [0.5],
        [1.0, 2.0],
    ]
    expecteds = [66.7, 66.7, 100.0, 150.0]
    for dur, pb, expected in zip(all_durations, all_boundaries, expecteds):
        # Calculate pnPVI
        pnpvi = phrase_normalized_pairwise_variability_index(dur, pb)
        # Should be the same as the expected answer
        assert pytest.approx(pnpvi, abs=1e-1) == pytest.approx(expected, abs=1e-1)
    # Raise an error when IOIs cross all phrase boundaries
    durs = [0.1, 0.6]
    phrase_boundaries = [0.5]
    with pytest.raises(ValueError):
        _ = phrase_normalized_pairwise_variability_index(durs, phrase_boundaries)
