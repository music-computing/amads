import math
from itertools import pairwise

import pytest

from amads.core.basics import Score
from amads.melody.melodic_distance import (
    combcontour_repr,
    distribution_repr,
    melcontour_repr,
    melodic_distance,
)
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def test_edge_cases():
    scores = (Score(), Score())
    for repr in distribution_repr:
        assert melodic_distance(*scores, repr) == 0.0
    assert melodic_distance(*scores, combcontour_repr) is None
    assert melodic_distance(*scores, melcontour_repr) is None
    score1 = Score.from_melody([61, 62, 63])
    score2 = Score.from_melody([62, 61, 63, 64])
    with pytest.raises(ValueError):
        melodic_distance(score1, score2, "melcontour", samples=-1)
    with pytest.raises(ValueError):
        melodic_distance(score1, score2, "foobar")
    with pytest.raises(ValueError):
        melodic_distance(score1, score2, metric="foobar")


def test_simple_melodies():
    score1 = Score.from_melody([61, 62, 63])
    score2 = Score.from_melody([62, 61, 63, 64])
    comb_result = melodic_distance(score1, score2, combcontour_repr)
    desired_comb_result = 0.16666666666666666
    assert math.isclose(comb_result, desired_comb_result)

    melcontour_result = melodic_distance(score1, score2, melcontour_repr)
    desired_melcontour_result = 3.0
    assert math.isclose(melcontour_result, desired_melcontour_result)

    desired_dist_results = [
        1.3333333333333333,
        2.0,
        0.4999999999999999,
        2.0,
        0.0,
        0.0,
    ]
    for dist_repr, desired_dist_result in zip(
        distribution_repr, desired_dist_results
    ):
        dist_result = melodic_distance(score1, score2, dist_repr)
        assert math.isclose(dist_result, desired_dist_result)


def test_different_distances():
    score1 = Score.from_melody([61, 62, 63])
    score2 = Score.from_melody([62, 61, 63, 64, 68])
    # The cosine version is bugged...
    norms = ["taxi", "euc", "cosine"]
    desired_results = [
        [0.16666666666666666, 13.0, 1.5, 2.0, 0.8, 2.0, 0.0, 0.0],
        [
            0.16666666666666666,
            5.385164807134504,
            0.8660254037844386,
            1.1547005383792517,
            0.3651483716701107,
            0.8660254037844388,
            0.0,
            0.0,
        ],
        [
            0.16666666666666666,
            110.7126966450998,
            0.5000000000000001,
            0.0,
            0.7745966692414832,
            0.0,
            1.0,
            1.0,
        ],
    ]
    for norm, desired_result_list in zip(norms, desired_results):
        comb_result = melodic_distance(score1, score2, combcontour_repr, norm)
        assert math.isclose(desired_result_list[0], comb_result)

        melcontour_result = melodic_distance(
            score1, score2, melcontour_repr, norm
        )
        assert math.isclose(desired_result_list[1], melcontour_result)
        for i, dist_repr in enumerate(distribution_repr):
            dist_result = melodic_distance(score1, score2, dist_repr, norm)
            assert math.isclose(desired_result_list[i + 2], dist_result)


def test_midi_sarabande():
    sliced_scores = []
    # apply onset windows [0, 2.5] and [2.5, 5.0] of the test score.
    for i, j in pairwise(range(3)):
        start_time = i * 2.5
        end_time = j * 2.5

        sliced_score = matlab_sarabande_test_score.slice(
            start_time, end_time, units="seconds"
        )
        sliced_score.convert_to_quarters()
        sliced_scores.append(sliced_score)

    result_dict = load_json_results()
    result_dist_labels = ["meldistance"]
    desired_dist_results = [result_dict[label] for label in result_dist_labels]
    for repr, desired_result in zip(["pcdist1"], desired_dist_results):
        result = melodic_distance(
            *sliced_scores, repr, miditoolbox_compatible=True
        )
        assert math.isclose(result, desired_result)


if __name__ == "__main__":
    test_edge_cases()
    test_simple_melodies()
    test_different_distances()
    test_midi_sarabande()
