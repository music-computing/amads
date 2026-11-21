import math

from amads.core.basics import Score
from amads.melody.gradus import gradus
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def test_edge_cases():
    # Empty score
    empty_score = Score()
    assert gradus(empty_score) is None

    # Single note
    single_note_score = Score.from_melody([60])
    assert gradus(single_note_score) is None


def test_toy_scores():
    # C major triad (C-E-G)
    score = Score.from_melody([60, 64, 67])
    assert gradus(score) == 7.5

    # Chromatic sequence
    chromatic_score = Score.from_melody([60, 61, 62, 63, 64])
    assert gradus(chromatic_score) == 11.0


def test_gradus_sarabande():
    assert math.isclose(
        gradus(matlab_sarabande_test_score), load_json_results()["gradus"]
    )


if __name__ == "__main__":
    test_edge_cases()
    test_toy_scores()
    test_gradus_sarabande()
