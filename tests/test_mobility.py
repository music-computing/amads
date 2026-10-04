import math

from score_test_utils import get_annotation_values_iterator

from amads.core.basics import Note, Score
from amads.melody.mobility import mobility
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def test_len_edge_cases():
    # Tests the edge cases where the score does not have enough length to run
    # mobility

    # Test case 2: Empty score
    empty_score = Score()
    assert mobility(empty_score) is None

    # Test case 3: Single note
    single_note_score = Score.from_melody([60])
    assert mobility(single_note_score) is None

    # Test case 4: Two notes
    two_note_score = Score.from_melody([60, 64])
    assert mobility(two_note_score) is None


def test_simple_melody():
    # Simple melody for sanity checking
    score = Score.from_melody(pitches=[60, 64, 62, 67, 65])

    annotated_score = mobility(score)
    desired_mobilities = [0, 0, 0, 2.4999999999999996, 0.5833333333333333]
    test_mobilities = get_annotation_values_iterator(
        annotated_score, Note, "mobility"
    )

    assert all(
        math.isclose(desired, test)
        for desired, test in zip(desired_mobilities, test_mobilities)
    )


def test_midi_sarabande():
    annotated_score = mobility(matlab_sarabande_test_score)
    desired_mobilities = load_json_results()["mobility"]
    test_mobilities = get_annotation_values_iterator(
        annotated_score, Note, "mobility"
    )
    assert all(
        math.isclose(desired, test)
        for desired, test in zip(desired_mobilities, test_mobilities)
    )


if __name__ == "__main__":
    test_len_edge_cases()
    test_simple_melody()
    test_midi_sarabande()
