import math

import pytest

from amads.core.basics import Score
from amads.melody.fantastic import (
    fantastic_count_mtypes,
    fantastic_huron_contour_features,
    fantastic_interpolation_contour_features,
    fantastic_mtype_summary_features,
    fantastic_parsons_contour_features,
    fantastic_pitch_features,
    fantastic_pitch_interval_features,
    fantastic_polynomial_contour_features,
    fantastic_step_contour_features,
)

__author__ = "David Whyatt"


def test_fantastic_count_mtypes():
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 65, 65, 63],
        durations=[0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.5],
    )

    types = fantastic_count_mtypes(
        melody, segment=False, phrase_gap=1.0, units="quarters"
    )
    # FANTASTIC supports n-grams of lengths 1-5, so we check that we have n-grams of lengths 1-5
    for i in range(1, 6):
        assert any(len(ngram) == i for ngram in types.ngram_counts.keys())


def test_fantastic_interpolation_contour_features():
    # Test with a melody that generally increases in pitch
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 65, 65, 63],
        durations=[0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.5],
    )
    features = fantastic_interpolation_contour_features(melody)
    assert features is not None

    # The melody tends to increase in pitch over time,
    # so we expect the global direction to be positive
    assert features["global_direction"] > 0

    # All of the changes in pitch are larger than a semitone
    assert features["mean_gradient"] > 1

    # The standard deviation of the gradient ought to be small
    # as we don't expect much variation
    assert features["gradient_std"] < 0.1

    # By virtue of how FANTASTIC identifies turning points,
    # the direction changes should be 0.0
    assert features["direction_changes"] == 0.0

    # The class label should be dddd
    # as the interpolated contour goes upwards across all four sampled steps
    assert features["class_label"] == "dddd"

    # Test with a descending melody
    descending = Score.from_melody(
        pitches=[67, 65, 64, 62, 60], durations=[1.0, 1.0, 1.0, 1.0, 1.0]
    )
    desc_features = fantastic_interpolation_contour_features(descending)

    # Should have negative global direction
    assert desc_features["global_direction"] < 0
    # Consistent downward motion means low gradient std
    assert desc_features["gradient_std"] < 0.1
    # No direction changes
    assert desc_features["direction_changes"] == 0.0
    # Contour is shallow, so it is classified as cccc
    assert desc_features["class_label"] == "cccc"

    # Test with a flat melody
    flat = Score.from_melody(
        pitches=[60, 60, 60, 60, 60], durations=[1.0, 1.0, 1.0, 1.0, 1.0]
    )
    flat_features = fantastic_interpolation_contour_features(flat)

    # A flat melody should have:
    assert flat_features["global_direction"] == 0  # No overall direction
    assert flat_features["mean_gradient"] == 0.0  # No gradient
    assert flat_features["gradient_std"] == 0.0  # No variation
    assert flat_features["direction_changes"] == 0.0  # No changes
    assert flat_features["class_label"] == "cccc"  # All same


def test_fantastic_step_contour_features():
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 65, 65, 63],
        durations=[0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.5],
    )

    features = fantastic_step_contour_features(melody)
    assert features is not None

    # The melody has several changes in direction
    # so we expect the global variation to be high
    assert features["global_variation"] > 1.0

    # The melody tends to increase in pitch over time,
    # so we expect the global direction to be positive
    assert features["global_direction"] > 0

    # The melody has several local changes in direction,
    # but not by large intervals, so we expect the local variation to be low
    assert features["local_variation"] < 0.5

    # Test with a simpler melody that only goes up
    simple_melody = Score.from_melody(
        pitches=[60, 62, 64, 65, 67], durations=[1.0, 1.0, 1.0, 1.0, 1.0]
    )

    simple_features = fantastic_step_contour_features(simple_melody)

    # A simple ascending melody should have:
    # Low global variation (consistent upward motion)
    assert simple_features["global_variation"] > 0.5
    # Positive global direction (ascending)
    assert simple_features["global_direction"] > 0
    # Low local variation (no direction changes)
    assert simple_features["local_variation"] < 0.5

    # Test with a melody that stays on same pitch
    flat_melody = Score.from_melody(
        pitches=[60, 60, 60, 60, 60], durations=[1.0, 1.0, 1.0, 1.0, 1.0]
    )

    flat_features = fantastic_step_contour_features(flat_melody)

    # A melody with no pitch changes should have:
    # Zero global variation
    assert flat_features["global_variation"] == 0
    # Zero global direction
    assert flat_features["global_direction"] == 0
    # Zero local variation
    assert flat_features["local_variation"] == 0


def test_fantastic_parsons_contour_features():
    melody = Score.from_melody(pitches=[60, 62, 64, 65, 67, 72], durations=[1.0] * 6)
    features = fantastic_parsons_contour_features(melody)
    assert features is not None

    # The interval sequence should be [None, 2, 2, 1, 2, 5]
    assert features["interval_sequence"] == [None, 2, 2, 1, 2, 5]

    # As such, the sign sequence would be [None, +1, +1, +1, +1, +1]
    assert features["interval_sequence_sign"] == [None, 1, 1, 1, 1, 1]

    # The string representation should be "uuuuu"
    assert features["as_string"] == "uuuuu"

    # We can also use the initial asterisk option
    features = fantastic_parsons_contour_features(melody, initial_asterisk=True)

    # The string representation should be "*uuuuu"
    assert features["as_string"] == "*uuuuu"

    # We can also use a custom character dict
    features = fantastic_parsons_contour_features(
        melody, character_dict={1: "^", 0: "->", -1: "v"}
    )

    # The string representation should be "^^^^^"
    assert features["as_string"] == "^^^^^"


def test_fantastic_polynomial_contour_features():
    melody = Score.from_melody(pitches=[60, 62, 64, 65, 67, 72], durations=[1.0] * 6)
    features = fantastic_polynomial_contour_features(melody)
    assert features is not None

    # We would expect the linear term to be positive
    assert features["coefficients"][0] > 0

    # We would also expect this for the quadratic and cubic terms
    assert features["coefficients"][1] > 0
    assert features["coefficients"][2] > 0

    # Verify that melodies with a single note have 0.0 coefficients
    # for all 3 terms
    single_note = Score.from_melody(pitches=[60], durations=[1.0])
    single_note_features = fantastic_polynomial_contour_features(single_note)
    assert single_note_features["coefficients"] == [0.0, 0.0, 0.0]

    # Produce a melody with an arching contour
    arching = Score.from_melody(
        pitches=[60, 62, 64, 65, 67, 72, 67, 65, 64, 62, 60],
        durations=[1.0] * 11,
    )
    arching_features = fantastic_polynomial_contour_features(arching)

    # We expect that the quadratic term is greater in magnitude than the linear term
    assert abs(arching_features["coefficients"][1]) > abs(
        arching_features["coefficients"][0]
    )


def test_fantastic_huron_contour_features():
    melody = Score.from_melody(pitches=[60, 62, 64, 65, 67, 72], durations=[1.0] * 6)
    features = fantastic_huron_contour_features(melody)
    assert features is not None

    # The first pitch should be 60
    assert features["first_pitch"] == 60
    # The mean pitch should be 67
    assert features["mean_pitch"] == 67
    # The last pitch should be 72
    assert features["last_pitch"] == 72
    # The first to mean difference should be 7
    assert features["first_to_mean"] == 7
    # The mean to last difference should be 5
    assert features["mean_to_last"] == 5
    # The contour class should be "Ascending-Ascending"
    assert features["contour_class"] == "Ascending-Ascending"


def test_fantastic_mtype_summary_features():
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 65, 65, 63],
        durations=[0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.5],
    )

    # Test with no segmentation first
    features = fantastic_mtype_summary_features(
        melody, segment=False, phrase_gap=1.0, units="quarters"
    )

    # Verify all summary stats are present and have reasonable values
    assert 0 <= features["mean_entropy"] <= 1.0
    assert 0 <= features["mean_productivity"] <= 1.0
    assert features["yules_k"] >= 0
    assert 0 <= features["simpsons_d"] <= 1.0
    assert 0 <= features["sichels_s"] <= 1.0

    # Honore's H should be incalculable for this melody
    assert math.isnan(features["honores_h"])

    # Test with a longer melody that can be segmented
    long_melody = Score.from_melody(
        pitches=[
            60,
            62,
            64,
            60,  # First phrase
            67,
            67,
            65,
            64,  # Second phrase
            62,
            62,
            60,
            60,  # Third phrase
            64,
            64,
            62,
            60,  # Fourth phrase
        ],
        durations=[
            1.0,
            1.0,
            1.0,
            2.0,  # First phrase with longer final note
            1.0,
            1.0,
            1.0,
            2.0,  # Second phrase
            1.0,
            1.0,
            1.0,
            2.0,  # Third phrase
            1.0,
            1.0,
            1.0,
            2.0,  # Fourth phrase
        ],
    )

    # Test with segmentation
    segmented_features = fantastic_mtype_summary_features(
        long_melody, segment=True, phrase_gap=1.5, units="quarters"
    )

    # Features should still be in valid ranges
    assert 0 <= segmented_features["mean_entropy"] <= 1.0
    assert 0 <= segmented_features["mean_productivity"] <= 1.0
    assert segmented_features["yules_k"] >= 0
    assert 0 <= segmented_features["simpsons_d"] <= 1.0
    assert 0 <= segmented_features["sichels_s"] <= 1.0

    # Honore's H is calculable for this melody
    assert segmented_features["honores_h"] >= 0


def test_fantastic_pitch_features():
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 65, 65, 63],
        durations=[0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.5],
    )

    features = fantastic_pitch_features(melody)
    assert features is not None

    # The melody has a range of 9
    assert features["pitch_range"] == 9
    # The standard deviation should be positive and reasonable given the pitch range
    assert features["pitch_std"] > 0
    assert features["pitch_std"] < features["pitch_range"]

    # Entropy should be between 0 and 1 since it's normalized by log2(24)
    assert 0 <= features["pitch_entropy"] <= 1.0

    # Test with a melody that has all the same pitch
    flat_melody = Score.from_melody(
        pitches=[60, 60, 60, 60, 60], durations=[1.0, 1.0, 1.0, 1.0, 1.0]
    )
    flat_features = fantastic_pitch_features(flat_melody)

    # A melody with all same pitches should have:
    assert flat_features["pitch_range"] == 0  # No range
    assert flat_features["pitch_std"] == 0  # No variation
    assert flat_features["pitch_entropy"] == 0  # Minimum entropy

    # Test with a chromatic scale
    chromatic = Score.from_melody(
        pitches=[60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71], durations=[1.0] * 12
    )
    chrom_features = fantastic_pitch_features(chromatic)

    # Chromatic scale should have:
    assert chrom_features["pitch_range"] == 11  # Range of 11 semitones
    assert chrom_features["pitch_std"] > 0  # Some variation
    # Relatively high entropy since all pitches occur equally often
    assert chrom_features["pitch_entropy"] > 0.5


def test_fantastic_pitch_interval_features():
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 65, 65, 63],
        durations=[0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.5],
    )

    features = fantastic_pitch_interval_features(melody)
    assert features is not None

    # The intervals in the melody are: [2, 3, -3, 7, 0, -2]
    # The absolute intervals are: [2, 3, 3, 7, 0, 2]
    assert features["absolute_interval_range"] == 7  # max(7) - min(0) = 7
    assert features["mean_absolute_interval"] == pytest.approx(2.833, rel=0.01)
    assert features["std_absolute_interval"] > 0
    assert features["modal_interval"] == 2  # 2 appears twice
    assert 0 <= features["interval_entropy"] <= 1.0  # Normalized by log2(23)

    # Test with a melody that has all the same intervals
    repeated_melody = Score.from_melody(
        pitches=[60, 62, 64, 66, 68, 70], durations=[1.0] * 6
    )
    repeated_features = fantastic_pitch_interval_features(repeated_melody)

    # All intervals are 2 semitones
    assert repeated_features["absolute_interval_range"] == 0  # max(2) - min(2) = 0
    assert repeated_features["mean_absolute_interval"] == 2.0
    assert repeated_features["std_absolute_interval"] == 0
    assert repeated_features["modal_interval"] == 2
    assert repeated_features["interval_entropy"] == 0  # Minimum entropy

    # Test with alternating up/down intervals
    zigzag = Score.from_melody(pitches=[60, 65, 60, 65, 60, 65], durations=[1.0] * 6)
    zigzag_features = fantastic_pitch_interval_features(zigzag)

    # All intervals are +5 or -5
    assert zigzag_features["absolute_interval_range"] == 0  # max(5) - min(5) = 0
    assert zigzag_features["mean_absolute_interval"] == 5.0
    assert zigzag_features["std_absolute_interval"] == 0
    assert zigzag_features["modal_interval"] == 5
    assert zigzag_features["interval_entropy"] == 0  # Only one interval size
