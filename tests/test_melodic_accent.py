import math

from score_test_utils import get_annotation_values_iterator

from amads.core.basics import Note, Score
from amads.melody.melodic_accent import melodic_accent
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def test_empty_melody():
    """
    Test empty melody
    """
    empty_score = Score()
    assert melodic_accent(empty_score) is None


def test_melodic_peak():
    """
    Test accent values for a melody with a local peak pitch-change pattern
    """
    # Create a test score
    score = Score.from_melody([60, 64, 62])

    annotated_score = melodic_accent(score)
    desired_accents = [1, 0.83, 0.17]
    property = "melodic_accent"
    annotated_iter = get_annotation_values_iterator(
        annotated_score, Note, property
    )
    assert all(
        math.isclose(test_val, desired)
        for test_val, desired in zip(annotated_iter, desired_accents)
    )


def test_melodic_valley():
    """
    Test accent values for a melody with a local valley pitch-change pattern
    """
    score = Score.from_melody([64, 60, 65])

    annotated_score = melodic_accent(score)
    desired_accents = [1, 0.71, 0.29]
    property = "melodic_accent"
    annotated_iter = get_annotation_values_iterator(
        annotated_score, Note, property
    )
    assert all(
        math.isclose(test_val, desired)
        for test_val, desired in zip(annotated_iter, desired_accents)
    )


def test_midi_sarabande():
    annotated_score = melodic_accent(matlab_sarabande_test_score)
    value_list = get_annotation_values_iterator(
        annotated_score, Note, "melodic_accent"
    )
    desired_list = load_json_results()["melaccent"]
    assert all(
        math.isclose(value, desired)
        for value, desired in zip(value_list, desired_list)
    )


if __name__ == "__main__":
    test_empty_melody()
    test_melodic_peak()
    test_melodic_valley()
    test_midi_sarabande()
