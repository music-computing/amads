import os

import numpy as np
import pytest

from amads.core.basics import Score
from amads.melody.similarity.melsim import (
    check_r_packages_installed,
    get_similarity_batch,
    get_similarity_from_scores,
)


@pytest.fixture(scope="session")
def installed_melsim_dependencies():
    on_ci = os.environ.get("CI") is not None
    install_missing = on_ci
    check_r_packages_installed(install_missing=install_missing)


def test_melsim_import(installed_melsim_dependencies):
    """Test that melsim can be imported."""
    from amads.melody.similarity.melsim import get_similarity_from_scores

    assert callable(get_similarity_from_scores)


def test_example_usage():
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)
    similarity = get_similarity_from_scores(mel_1, mel_2, "Jaccard", "pitch")
    assert similarity == 0.6


def test_transformation_usage():
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[62, 64, 66, 67], durations=1.0)
    # Melody 2 is a transposition of Melody 1 by 2 semitones
    similarity = get_similarity_from_scores(mel_1, mel_2, "Jaccard", "pitch")
    # As a result, the similarity should not be 1.0
    assert similarity != 1.0

    # However, the similarity between the intervals should be 1.0
    similarity = get_similarity_from_scores(mel_1, mel_2, "Jaccard", "int")
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
    print("Testing all measures and transformations using batch processing...")
    results = get_similarity_batch(
        {"melody1": mel_1, "melody2": mel_2},
        method=supported_measures,
        transformation=supported_transformations,
    )

    # Verify we got results for all combinations
    expected_combinations = len(supported_measures) * len(supported_transformations)
    assert (
        len(results) == expected_combinations
    ), f"Expected {expected_combinations} results, got {len(results)}"

    # Test each result
    for (name1, name2, method, transformation), similarity in results.items():
        assert similarity is not None, f"Failed for {method} with {transformation}"
        # Handle cases where similarity is NaN (invalid combinations)
        if not np.isnan(similarity):
            assert isinstance(
                similarity, float
            ), f"Result for {method} with {transformation} is not a float"
            assert (
                0.0 <= similarity <= 1.0
            ), f"Similarity out of range for {method} with {transformation}: {similarity}"


def test_batch_similarity():
    """Test batch similarity computation with multiple Score objects."""
    # Create a small collection of test melodies
    scores = {
        "melody1": Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0),
        "melody2": Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0),
        "melody3": Score.from_melody(pitches=[62, 64, 66, 67], durations=1.0),
    }

    # Test with single method and transformation
    results = get_similarity_batch(scores, method="Jaccard", transformation="pitch")

    # Should have 3 pairwise comparisons: (1,2), (1,3), (2,3)
    assert len(results) == 3

    # All results should be tuples of (name1, name2, method, transformation) -> float
    for key, value in results.items():
        assert len(key) == 4  # (name1, name2, method, transformation)
        assert isinstance(key[0], str)  # melody name 1
        assert isinstance(key[1], str)  # melody name 2
        assert key[2] == "Jaccard"  # method
        assert key[3] == "pitch"  # transformation
        assert isinstance(value, float)  # similarity value
        assert 0.0 <= value <= 1.0  # similarity should be in valid range

    # Test with multiple methods and transformations
    results_multi = get_similarity_batch(
        scores, method=["Jaccard", "Dice"], transformation=["pitch", "int"]
    )

    # Should have 3 pairs × 2 methods × 2 transformations = 12 results
    assert len(results_multi) == 12
