import math

from amads.core.basics import Note, Score
from amads.melody.melodic_attraction import melodic_attraction
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def _get_value_list_from_notes(score: Score, annotation_str: str) -> list:
    value_list = []
    for note in score.find_all(Note):
        value_list.append(note.get(annotation_str, None))
    return value_list


def test_simple_score_sequences():
    # Test case 1: Simple scale fragment
    test_melodies = [[60, 62, 64, 65], [62, 64, 65, 67, 69, 71, 72, 60]]
    desired_results = [
        [0.0, 0.2, 0.475, 0.4],
        [
            0.0,
            0.1375,
            0.37777777777777777,
            0.4,
            0.4,
            0.30277777777777776,
            0.4,
            0.0,
        ],
    ]

    for test_melody, desired_list in zip(test_melodies, desired_results):
        test_score = Score.from_melody(test_melody)
        transposed_score = melodic_attraction(test_score)
        value_list = _get_value_list_from_notes(
            transposed_score, "melodic_attraction"
        )
        assert all(
            math.isclose(value, desired)
            for value, desired in zip(value_list, desired_list)
        )


def test_edge_cases():
    empty_score = Score()
    assert melodic_attraction(empty_score) is None
    single_note_score = Score.from_melody([60])
    transposed_score = melodic_attraction(single_note_score)
    value_list = _get_value_list_from_notes(
        transposed_score, "melodic_attraction"
    )
    assert value_list == [0.0]


def test_matlab_sarabande():
    transposed_score = melodic_attraction(matlab_sarabande_test_score)
    value_list = _get_value_list_from_notes(
        transposed_score, "melodic_attraction"
    )
    desired_list = load_json_results()["melattraction"]
    assert all(
        math.isclose(value, desired)
        for value, desired in zip(value_list, desired_list)
    )


if __name__ == "__main__":
    test_simple_score_sequences()
    test_edge_cases()
    test_matlab_sarabande()
