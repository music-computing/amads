import math

from score_test_utils import get_annotation_values_iterator

from amads.core.basics import Note, Score
from amads.melody.tessitura import _RunningMedian, tessitura
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def test_internal_median_tracker():
    median_tracker = _RunningMedian()
    median_tracker.insert_integer(1)
    assert median_tracker.obtain_current_median() == 1
    median_tracker.insert_integer(2)
    assert median_tracker.obtain_current_median() == 1.5
    median_tracker.insert_integer(5)
    assert median_tracker.obtain_current_median() == 2
    median_tracker.insert_integer(4)
    assert median_tracker.obtain_current_median() == 3.0


def test_empty_score():
    empty_score = Score()
    assert tessitura(empty_score, True) is None
    assert tessitura(empty_score, False) is None


def test_singleton_score():
    singleton_score = Score.from_melody([60])
    annotated_score = tessitura(singleton_score, True)
    assert annotated_score is not None
    test_tessitura = get_annotation_values_iterator(
        annotated_score, Note, "tessitura_mtb"
    )
    assert list(test_tessitura) == [0]
    annotated_score = tessitura(singleton_score, False)
    assert annotated_score is not None
    test_tessitura = get_annotation_values_iterator(
        annotated_score, Note, "tessitura"
    )
    assert list(test_tessitura) == [0]


def test_toy_scores():
    double_score = Score.from_melody([60, 63])
    double_score = tessitura(double_score, True)
    assert double_score is not None
    double_test = get_annotation_values_iterator(
        double_score, Note, "tessitura_mtb"
    )
    desired_double = [0, 0]
    assert list(double_test) == desired_double
    another_toy_score = Score.from_melody([60, 63, 71, 31])
    another_toy_score = tessitura(another_toy_score, True)
    assert another_toy_score is not None
    another_toy_test = get_annotation_values_iterator(
        another_toy_score, Note, "tessitura_mtb"
    )
    another_toy_desired = [0, 0, 3.771236166328254, 7.034524581126592]
    assert all(
        math.isclose(desired, test)
        for desired, test in zip(another_toy_desired, another_toy_test)
    )


def test_midi_sarabande():
    annotated_score = tessitura(matlab_sarabande_test_score, True)
    test_tessitura = get_annotation_values_iterator(
        annotated_score, Note, "tessitura_mtb"
    )

    desired_tessitura = load_json_results()["tessitura"]

    assert all(
        math.isclose(desired, test)
        for desired, test in zip(desired_tessitura, test_tessitura)
    )


if __name__ == "__main__":
    test_internal_median_tracker()
    test_empty_score()
    test_singleton_score()
    test_toy_scores()
    test_midi_sarabande()
