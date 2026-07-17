"""
Tests combcontour module
"""

import numpy as np

from amads.core.basics import Score
from amads.melody.contour.combcontour import get_pitch_comparison_contour_matrix


def test_empty_melody():
    """
    Edge case: Verifies melodic contour extraction using an empty melody
    """
    melody = Score.from_melody([])
    result = get_pitch_comparison_contour_matrix(melody)
    assert result is None
    return


def test_nonempty_combcontour():
    """
    Sanity check: Verifies melodic contour extraction using a simple,
    hand-crafted melody.
    """
    pitches_in = [55, 40, 60, 50]
    melody = Score.from_melody(pitches=pitches_in)
    melody.time_shift(2.5)
    result = get_pitch_comparison_contour_matrix(melody)
    desired_result = np.array(
        [
            [False, False, False, False],
            [True, False, False, False],
            [False, False, False, False],
            [True, False, True, False],
        ]
    )
    assert (result == desired_result).all()

    return


if __name__ == "__main__":
    test_empty_melody()
    test_nonempty_combcontour()
