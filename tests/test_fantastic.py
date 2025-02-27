from amads.core.basics import Score
from amads.melody.fantastic import (
    fantastic_count_mtypes,
    fantastic_interpolation_contour_features,
    fantastic_step_contour_features,
)


def test_fantastic_count_mtypes():
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 64, 64, 63],
        durations=[0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.5],
    )

    types = fantastic_count_mtypes(
        melody, segment=False, phrase_gap=1.0, units="quarters"
    )
    # FANTASTIC supports n-grams of lengths 1-5, so we check that we have n-grams of lengths 1-5
    for i in range(1, 6):
        assert any(len(ngram) == i for ngram in types.keys())


def test_fantastic_interpolation_contour_features():
    # Test with a melody that generally increases in pitch
    melody = Score.from_melody(
        pitches=[56, 58, 61, 58, 64, 64, 63],
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
    # Should be classified as all down,
    # but the contour is not steep, so it is categorised into cccc
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
        pitches=[56, 58, 61, 58, 64, 64, 63],
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
