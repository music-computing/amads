import math

from amads.core.basics import Score
from amads.time.meter.meter_accent import meter_accent
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)


def test_score_size_edge_cases():
    empty_score = Score()
    assert meter_accent(empty_score) is None

    single_note_score = Score.from_melody(pitches=[60], durations=[1.0])
    assert meter_accent(single_note_score) is None

    two_note_score = Score.from_melody(pitches=[60, 61])
    assert meter_accent(two_note_score) is None


def test_normal_scores():
    regular_score = Score.from_melody(
        pitches=[60, 64, 67], durations=[1.0, 0.5, 1.0]
    )
    regular_result = meter_accent(regular_score)
    desired_regular_result = -1.10080924747657
    assert math.isclose(regular_result, desired_regular_result)

    syncopated_score = Score.from_melody(
        pitches=[60, 64, 67, 65], durations=[0.5, 1.0, 0.5, 1.0]
    )
    syncopated_result = meter_accent(syncopated_score)
    desired_syncopated_result = -0.5639996078945401
    assert math.isclose(syncopated_result, desired_syncopated_result)

    large_interval_score = Score.from_melody(
        pitches=[60, 72, 65, 69], durations=[1.0, 0.25, 0.75, 0.5]
    )
    large_interval_result = meter_accent(large_interval_score)
    desired_large_interval_result = -0.7612146190811371
    assert math.isclose(large_interval_result, desired_large_interval_result)


def test_midi_sarabande():
    python_result = meter_accent(matlab_sarabande_test_score)
    matlab_result = load_json_results()["meteraccent"]
    assert math.isclose(python_result, matlab_result)


if __name__ == "__main__":
    test_score_size_edge_cases()
    test_normal_scores()
    test_midi_sarabande()
