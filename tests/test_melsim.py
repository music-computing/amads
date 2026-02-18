import math
import os
from unittest.mock import Mock

import pytest

from amads.core.basics import Score
from amads.melody.similarity.melsim import (
    _convert_strings_to_tuples,
    check_python_package_installed,
    check_r_packages_installed,
    get_similarities,
    get_similarity,
    install_dependencies,
    install_r_package,
    score_to_arrays,
    validate_method,
    validate_transformation,
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


def test_validate_method():
    """Test method validation."""
    # Valid methods should not raise errors
    validate_method("Jaccard")
    validate_method("cosine")
    validate_method("Euclidean")

    # Invalid methods should raise ValueError
    with pytest.raises(ValueError, match="Invalid method"):
        validate_method("InvalidMethod")

    with pytest.raises(ValueError, match="Invalid method"):
        validate_method("random_method")


def test_validate_transformation():
    """Test transformation validation."""
    # Valid transformations should not raise errors
    validate_transformation("pitch")
    validate_transformation("int")
    validate_transformation("parsons")

    # Invalid transformations should raise ValueError
    with pytest.raises(ValueError, match="Invalid transformation"):
        validate_transformation("InvalidTransformation")

    with pytest.raises(ValueError, match="Invalid transformation"):
        validate_transformation("random_transform")


def test_check_python_package_installed():
    """Test Python package checking."""
    # Valid package should not raise error
    check_python_package_installed("os")
    check_python_package_installed("sys")

    # Invalid package should raise ImportError
    with pytest.raises(
        ImportError, match="Package 'nonexistent_package' is required"
    ):
        check_python_package_installed("nonexistent_package")


def test_score_to_arrays():
    """Test score to arrays conversion."""
    mel = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    pitches, starts, ends = score_to_arrays(mel)

    assert len(pitches) == 4
    assert len(starts) == 4
    assert len(ends) == 4
    assert pitches == [60, 62, 64, 65]
    assert all(isinstance(p, int) for p in pitches)
    assert all(isinstance(s, float) for s in starts)
    assert all(isinstance(e, float) for e in ends)


def test_convert_strings_to_tuples():
    """Test string to tuple conversion utility."""
    # Test with regular dict
    input_dict = {"key1": "value1", "key2": "value2"}
    result = _convert_strings_to_tuples(input_dict)
    assert result == input_dict

    # Test with nested dict
    input_dict = {"outer": {"inner": "value"}}
    result = _convert_strings_to_tuples(input_dict)
    assert result == {"outer": {"inner": "value"}}

    # The function currently doesn't convert string keys to tuples
    # It just preserves the dictionary structure


def test_get_similarity_error_handling():
    """Test error handling in get_similarity."""
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)

    # Test invalid method
    with pytest.raises(ValueError, match="Invalid method"):
        get_similarity(mel_1, mel_2, "InvalidMethod", "pitch")

    # Test invalid transformation
    with pytest.raises(ValueError, match="Invalid transformation"):
        get_similarity(mel_1, mel_2, "Jaccard", "InvalidTransformation")


def test_install_r_package_cran(monkeypatch):
    """Test R package installation for CRAN packages."""
    mock_run = Mock()
    monkeypatch.setattr("subprocess.run", mock_run)

    # Test CRAN package installation
    install_r_package("jsonlite")

    # Should have called subprocess.run with Rscript
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0].endswith("Rscript")
    assert "jsonlite" in call_args[2]


def test_install_r_package_github(monkeypatch):
    """Test R package installation for GitHub packages."""
    mock_run = Mock()
    monkeypatch.setattr("subprocess.run", mock_run)

    # Test GitHub package installation
    install_r_package("melsim")

    # Should have called subprocess.run with Rscript
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0].endswith("Rscript")
    assert "remotes::install_github" in call_args[2]


def test_install_r_package_invalid():
    """Test error handling for invalid R packages."""
    with pytest.raises(ValueError, match="Unknown package type"):
        install_r_package("nonexistent_package")


def test_install_dependencies_success(monkeypatch):
    """Test successful dependency installation."""
    # Mock successful package checks (no missing packages)
    mock_run = Mock(return_value=Mock(stdout="", returncode=0))
    monkeypatch.setattr("subprocess.run", mock_run)

    # Should not raise any errors
    install_dependencies()

    # Should have called subprocess.run multiple times for checking packages
    assert mock_run.call_count >= 2  # At least CRAN and GitHub checks


def test_install_dependencies_with_missing_packages(monkeypatch):
    """Test dependency installation with missing packages."""
    # Mock missing packages on first call, then success
    mock_run = Mock(
        side_effect=[
            Mock(stdout='"jsonlite","dplyr"', returncode=0),  # Missing CRAN
            Mock(stdout="", returncode=0),  # Install success
            Mock(stdout='"melsim"', returncode=0),  # Missing GitHub
            Mock(stdout="", returncode=0),  # Install success
        ]
    )
    monkeypatch.setattr("subprocess.run", mock_run)

    install_dependencies()

    # Should have called subprocess.run multiple times
    assert mock_run.call_count == 4


def test_get_similarities_output_formats():
    """Test different output formats for get_similarities."""
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)
    mel_3 = Score.from_melody(pitches=[67, 69, 71, 72], durations=1.0)

    scores = {"melody1": mel_1, "melody2": mel_2, "melody3": mel_3}

    # Test multiple methods, single transformation
    results = get_similarities(
        scores, method=["Jaccard", "Dice"], transformation="pitch"
    )
    assert isinstance(results, dict)
    assert ("Jaccard", "pitch") in results
    assert ("Dice", "pitch") in results

    # Test single method, multiple transformations
    results = get_similarities(
        scores, method="Jaccard", transformation=["pitch", "int"]
    )
    assert isinstance(results, dict)
    assert ("Jaccard", "pitch") in results
    assert ("Jaccard", "int") in results

    # Test multiple methods and transformations
    results = get_similarities(
        scores, method=["Jaccard", "Dice"], transformation=["pitch", "int"]
    )
    assert isinstance(results, dict)
    assert ("Jaccard", "pitch") in results
    assert ("Jaccard", "int") in results
    assert ("Dice", "pitch") in results
    assert ("Dice", "int") in results


def test_get_similarities_batch_processing():
    """Test batch processing parameters."""
    mel_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    mel_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)

    scores = {"melody1": mel_1, "melody2": mel_2}

    # Test with different batch sizes
    results1 = get_similarities(
        scores, method="Jaccard", transformation="pitch", batch_size=1
    )
    results2 = get_similarities(
        scores, method="Jaccard", transformation="pitch", batch_size=10
    )

    # Results should be the same regardless of batch size
    assert results1["melody1"]["melody2"] == results2["melody1"]["melody2"]

    # Test with different n_cores
    results3 = get_similarities(
        scores, method="Jaccard", transformation="pitch", n_cores=1
    )
    assert results3["melody1"]["melody2"] == results1["melody1"]["melody2"]


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
    expected_combinations = len(supported_measures) * len(
        supported_transformations
    )
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
