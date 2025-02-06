import os

import pytest

from amads.core.basics import Score
from amads.melody.similarity.melsim import check_r_packages_installed, get_similarity


@pytest.fixture(scope="session")
def installed_melsim_dependencies():
    on_ci = os.environ.get("CI") is not None
    install_missing = on_ci
    check_r_packages_installed(install_missing=install_missing)


def test_melsim_import(installed_melsim_dependencies):
    """Test that melsim can be imported."""
    from amads.melody.similarity.melsim import get_similarity

    assert callable(get_similarity)


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
    # Test each combination of measure and transformation
    for measure in supported_measures:
        for transformation in supported_transformations:
            similarity = get_similarity(mel_1, mel_2, measure, transformation)
            assert similarity is not None, f"Failed for {measure} with {transformation}"
            assert isinstance(
                similarity, float
            ), f"Result for {measure} with {transformation} is not a float"
