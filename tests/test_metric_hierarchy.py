from amads.core.basics import Note, Score
from amads.time.meter.metric_hierarchy import metric_hierarchy
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)
from tests.score_test_utils import get_annotation_values_iterator


def test_empty_score():
    # empty score
    empty_score = Score()
    assert metric_hierarchy(empty_score) is None


def test_basic_scores():
    onsets = [i + 0.5 for i in range(10)]
    durations = [0.5 if i % 2 else 1.0 for i in range(10)]
    basic_score = Score.from_melody(
        list(range(10)), durations=durations, onsets=onsets
    )
    annotated_score = metric_hierarchy(basic_score, True)
    test_result_toolbox_compatible = list(
        get_annotation_values_iterator(
            annotated_score, Note, "metric_hierarchy"
        )
    )
    desired_toolbox_compatible = [5, 4, 5, 4, 5, 4, 5, 4, 5, 4]
    assert test_result_toolbox_compatible == desired_toolbox_compatible

    annotated_score = metric_hierarchy(basic_score, False)
    test_result = list(
        get_annotation_values_iterator(
            annotated_score, Note, "metric_hierarchy"
        )
    )
    desired_result = [5, 4, 5, 4, 5, 4, 5, 4, 5, 4]
    assert test_result == desired_result


def test_midi_sarabande():
    matlab_results = load_json_results()
    annotated_score = metric_hierarchy(matlab_sarabande_test_score, True)
    result_list = list(
        get_annotation_values_iterator(
            annotated_score, Note, "metric_hierarchy"
        )
    )
    assert result_list == matlab_results["metrichierarchy"]


if __name__ == "__main__":
    test_empty_score()
    test_basic_scores()
    test_midi_sarabande()
