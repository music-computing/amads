"""
Test suite for pcdist1
"""

import math

from amads.core.basics import Score
from amads.pitch.pcdist1 import pitch_class_distribution_1
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def test_empty_melody():
    score = Score.from_melody([])
    val = pitch_class_distribution_1(score)
    test = [0] * 12
    assert val.data == test


def test_sarabande():
    json_data = load_json_results()
    # This desired data result is obtained from matlab testing
    desired_data = json_data["pcdist1"]

    pcd = pitch_class_distribution_1(
        matlab_sarabande_test_score, weighted=True, miditoolbox_compatible=True
    )

    assert all(
        math.isclose(desired, pcd_datum)
        for desired, pcd_datum in zip(desired_data, pcd.data)
    )


if __name__ == "__main__":
    test_empty_melody()
    test_sarabande()
