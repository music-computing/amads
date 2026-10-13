import pytest

from amads.core.basics import Score
from amads.time.meter.meter_autocorrelation import meter_autocorrelation
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)

# how would one potentially test meter?!
# I don't know...


def test_edge_cases():
    score = Score.from_melody([60, 61, 62, 63])
    invalid_option = "Blablabla"

    with pytest.raises(
        ValueError,
        match=f"invalid option {invalid_option}! Must be 'Optimal' or None!",
    ):
        meter_autocorrelation(score, invalid_option)


def test_basic_score():
    score = Score.from_melody(list(range(60, 69)))
    desired_result = (2, 3)
    default_result = meter_autocorrelation(score, None)

    optimal_result = meter_autocorrelation(score, "Optimal")
    assert (default_result, optimal_result) == desired_result


def test_midi_sarabande():
    matlab_dict = load_json_results()
    matlab_results = (
        matlab_dict["meter_default"],
        matlab_dict["meter_optimal"],
    )
    default_result = meter_autocorrelation(matlab_sarabande_test_score)
    optimal_result = meter_autocorrelation(
        matlab_sarabande_test_score, "Optimal"
    )
    assert matlab_results == (default_result, optimal_result)


if __name__ == "__main__":
    test_edge_cases()
    test_basic_score()
    test_midi_sarabande()
