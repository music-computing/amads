import math
import os

import pytest

from amads.core.basics import Score
from amads.melody.similarity.melsim import (
    check_r_packages_installed,
    get_similarities,
    get_similarity,
)


@pytest.fixture(scope="session")
def installed_melsim_dependencies():
    on_ci = os.environ.get("CI") is not None
    install_missing = on_ci
    check_r_packages_installed(install_missing=install_missing)


def test_melsim_import(installed_melsim_dependencies):
    """Test that melsim can be imported."""
    from amads.melody.similarity.melsim import get_similarity

    assert callable(get_similarity)


def test_example_usage():
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)
    similarity = get_similarity(mel_1, mel_2, "Jaccard", "pitch")
    assert similarity == 0.6


def test_transformation_usage():
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[62, 64, 66, 67], durations=1.0)
    # Melody 2 is a transposition of Melody 1 by 2 semitones
    similarity = get_similarity(mel_1, mel_2, "Jaccard", "pitch")
    # As a result, the similarity should not be 1.0
    assert similarity != 1.0

    # However, the similarity between the intervals should be 1.0
    similarity = get_similarity(mel_1, mel_2, "Jaccard", "int")
    assert similarity == 1.0


def test_melsim_measures_transformations():

    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)

    supported_measures = [
        "Jaccard",
        "Kulczynski2",
        "Russel",
        "Faith",
        "Tanimoto",
        "Dice",
        "Mozley",
        "Ochiai",
        "Simpson",
        "cosine",
        "angular",
        "correlation",
        "Tschuprow",
        "Cramer",
        "Gower",
        "Euclidean",
        "Manhattan",
        "supremum",
        "Canberra",
        "Chord",
        "Geodesic",
        "Bray",
        "Soergel",
        "Podani",
        "Whittaker",
        "eJaccard",
        "eDice",
        "Bhjattacharyya",
        "divergence",
        "Hellinger",
        "edit_sim_utf8",
        "edit_sim",
        "Levenshtein",
        "sim_NCD",
        "const",
        "sim_dtw",
    ]

    supported_transformations = [
        "pitch",
        "int",
        "fuzzy_int",
        "parsons",
        "pc",
        "ioi_class",
        "duration_class",
        "int_X_ioi_class",
        "implicit_harmonies",
    ]

    # Use batch processing to test all combinations efficiently
    results = get_similarities(
        {"melody1": mel_1, "melody2": mel_2},
        method=supported_measures,
        transformation=supported_transformations,
    )

    # Verify we got results for all combinations
    expected_combinations = len(supported_measures) * len(supported_transformations)
    assert (
        len(results) == expected_combinations
    ), f"Expected {expected_combinations} results, got {len(results)}"

    # Test each result matrix
    for (method, transformation), matrix in results.items():
        assert matrix is not None, f"Failed for {method} with {transformation}"
        assert isinstance(
            matrix, dict
        ), f"Result for {method} with {transformation} is not a dict"

        # Check matrix structure
        assert (
            "melody1" in matrix
        ), f"Missing melody1 in matrix for {method} with {transformation}"
        assert (
            "melody2" in matrix
        ), f"Missing melody2 in matrix for {method} with {transformation}"
        assert (
            "melody1" in matrix["melody2"]
        ), f"Missing melody1 in melody2 row for {method} with {transformation}"
        assert (
            "melody2" in matrix["melody1"]
        ), f"Missing melody2 in melody1 row for {method} with {transformation}"

        # Check diagonal values
        assert (
            matrix["melody1"]["melody1"] == 1.0
        ), f"Diagonal not 1.0 for {method} with {transformation}"
        assert (
            matrix["melody2"]["melody2"] == 1.0
        ), f"Diagonal not 1.0 for {method} with {transformation}"

        # Check symmetry and range
        similarity = matrix["melody1"]["melody2"]
        reverse_similarity = matrix["melody2"]["melody1"]

        # Check if both are NaN (NaN != NaN in Python, so we need special handling)
        both_nan = (
            isinstance(similarity, float)
            and math.isnan(similarity)
            and isinstance(reverse_similarity, float)
            and math.isnan(reverse_similarity)
        )

        # Assert symmetry (treating two NaN values as equal)
        assert (
            both_nan or similarity == reverse_similarity
        ), f"Matrix not symmetric for {method} with {transformation}"

        # Handle cases where similarity is NaN (invalid combinations)
        if not math.isnan(similarity):
            assert isinstance(
                similarity, float
            ), f"Result for {method} with {transformation} is not a float"
            assert (
                0.0 <= similarity <= 1.0
            ), f"Similarity out of range for {method} with {transformation}: {similarity}"


def test_batch_similarity():
    """Test batch similarity calculation."""
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)
    mel_3 = Score.from_melody(pitches=[67, 69, 71, 72], durations=1.0)

    scores = {"melody1": mel_1, "melody2": mel_2, "melody3": mel_3}

    # Test single method/transformation - should return a nested dictionary
    results = get_similarities(scores, method="Jaccard", transformation="pitch")

    # Should be a nested dictionary {melody_name: {melody_name: similarity}}
    assert isinstance(results, dict)
    assert "melody1" in results
    assert "melody2" in results["melody1"]
    assert "melody3" in results["melody1"]

    # Diagonal should be 1.0
    assert results["melody1"]["melody1"] == 1.0
    assert results["melody2"]["melody2"] == 1.0
    assert results["melody3"]["melody3"] == 1.0

    # Should be symmetric
    assert results["melody1"]["melody2"] == results["melody2"]["melody1"]
    assert results["melody1"]["melody3"] == results["melody3"]["melody1"]
    assert results["melody2"]["melody3"] == results["melody3"]["melody2"]

    # Test multiple methods/transformations - should return dict of matrices
    results_multi = get_similarities(
        scores, method=["Jaccard", "Dice"], transformation=["pitch", "int"]
    )

    # Should be a dictionary mapping (method, transformation) tuples to matrices
    assert isinstance(results_multi, dict)
    assert ("Jaccard", "pitch") in results_multi
    assert ("Jaccard", "int") in results_multi
    assert ("Dice", "pitch") in results_multi
    assert ("Dice", "int") in results_multi

    # Each matrix should be a nested dictionary
    jaccard_pitch_matrix = results_multi[("Jaccard", "pitch")]
    assert isinstance(jaccard_pitch_matrix, dict)
    assert "melody1" in jaccard_pitch_matrix
    assert "melody2" in jaccard_pitch_matrix["melody1"]

    # Diagonal should be 1.0
    assert jaccard_pitch_matrix["melody1"]["melody1"] == 1.0
