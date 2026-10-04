from amads.core.basics import Note, Score
from amads.melody.narmour import NarmourOption, narmour
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def obtain_annotation_values_sequence(
    annotated_score: Score, type: any, annotation_str: str
):
    """
    Helper function to obtain narmour annotation values.
    This function only works because successful calls to narmour implies that
    the input score is monophonic.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.
    annotation_str : str
        Label that was used to annotate all the notes in the score.

    Returns
    -------
    List
        List of values that was annotated under the label.
    """
    test_vals = []

    for note in annotated_score.find_all(type):
        test_val = note.get(annotation_str, None)
        test_vals.append(test_val)
    return test_vals


def test_edge_cases():
    empty_score = Score()
    for option in NarmourOption:
        assert narmour(empty_score, option) is None

    short_score = Score.from_melody([60, 64])
    assert narmour(short_score, NarmourOption.REGISTRAL_DIRECTION) is None


def test_simple_ascending_melody():
    score = Score.from_melody([60, 64, 67, 72])
    desired_results = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 0],
        [0, 4, 3, 5],
        [10, 7.25, 6.03, 8.03],
    ]
    for option, desired_result in zip(NarmourOption, desired_results):
        score, label = narmour(score, option)
        values = obtain_annotation_values_sequence(score, Note, label)
        assert all(
            desired == test for desired, test in zip(desired_result, values)
        )


def test_direction_changing_melody():
    score = Score.from_melody([60, 64, 62, 67, 65])
    desired_results = [
        [0, 0, 0, 0, 0],
        [0, 0, 1.5, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 1, 2],
        [0, 4, 2, 5, 2],
        [10, 7.25, 4.16, 8.03, 4.16],
    ]
    for option, desired_result in zip(NarmourOption, desired_results):
        score, label = narmour(score, option)
        values = obtain_annotation_values_sequence(score, Note, label)
        assert all(
            desired == test for desired, test in zip(desired_result, values)
        )


def test_matlab_sarabande():
    matlab_dict = load_json_results()
    matlab_results = [
        matlab_dict["narmour_rd"],
        matlab_dict["narmour_rr"],
        matlab_dict["narmour_id"],
        matlab_dict["narmour_cl"],
        matlab_dict["narmour_pr"],
        matlab_dict["narmour_co"],
    ]
    for option, matlab_result in zip(NarmourOption, matlab_results):
        test_score, label = narmour(matlab_sarabande_test_score, option)
        test_result = obtain_annotation_values_sequence(test_score, Note, label)
        assert all(
            desired == test for desired, test in zip(matlab_result, test_result)
        )


if __name__ == "__main__":
    test_edge_cases()
    test_simple_ascending_melody()
    test_matlab_sarabande()
    test_direction_changing_melody()
