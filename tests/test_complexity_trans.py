import math

from amads.core.basics import Score
from amads.melody.complexity_trans import complexity_trans


def test_empty_score():
    # Test case 2: Empty score
    empty_score = Score()
    assert complexity_trans(empty_score) is None


def test_singleton_score():
    # Test case 2: Empty score
    singleton_score = Score.from_melody([60])
    assert complexity_trans(singleton_score) is None


def test_melody_snippets():
    pitch_sequence_list = [
        [60, 64, 67, 72],
        [60, 64],
        [60, 61, 62, 63, 64],
        [60, 66, 61, 71],
    ]
    transition_complexities = [3.899386666666667, 5.84908, 6.98116, 10.00004]
    for pitch_sequence, desired_complexity in zip(
        pitch_sequence_list, transition_complexities
    ):
        score = Score.from_melody(pitch_sequence)
        obtained_complexity = complexity_trans(score)
        # target_transition_complexity = 0
        assert math.isclose(desired_complexity, obtained_complexity)


if __name__ == "__main__":
    test_empty_score()
    test_singleton_score()
    test_melody_snippets()
