"""
Tests the 2 melcontour functions to ensure they work as advertised
"""

from amads.core.basics import Note, Score
from amads.melody.contour.melcontour import (
    melodySamplingContour,
    melodySamplingCorrelation,
)


def test_empty_melody():
    """
    Edge case: Verifies melodic contour extraction using an empty melody
    """
    melody = Score.from_melody([])
    result = melodySamplingContour(melody, 0.5)
    assert result is None
    return


def test_nonempty_melody_contour():
    """
    Sanity check: Verifies melodic contour extraction using a simple,
    hand-crafted melody.
    """
    pitches_in = list(range(56, 68, 2))
    melody = Score.from_melody(pitches=pitches_in)
    melody.time_shift(2.5)
    result = melodySamplingContour(melody, 1)
    desired_result = [
        Note(onset=2.500, duration=1.000, pitch=56),
        Note(onset=3.500, duration=1.000, pitch=58),
        Note(onset=4.500, duration=1.000, pitch=60),
        Note(onset=5.500, duration=1.000, pitch=62),
        Note(onset=6.500, duration=1.000, pitch=64),
        Note(onset=7.500, duration=1.000, pitch=66),
    ]
    assert all(
        (desired == obtained and desired is None)
        or (
            desired.onset == obtained.onset
            and desired.duration == obtained.duration
            and desired.pitch == obtained.pitch
        )
        for desired, obtained in zip(desired_result, result)
    )

    return


def test_nonempty_melody_correlation():
    """
    Sanity check: Verifies melodic contour correlation using a simple,
    hand-crafted melody.
    """
    pitches_in = list(range(56, 68, 2))
    melody = Score.from_melody(pitches=pitches_in)
    melody.time_shift(2.5)
    result = melodySamplingCorrelation(melody, 1)
    desired_result = [
        -0.3571428571428571,
        -0.4285714285714285,
        -0.2714285714285714,
        0.05714285714285715,
        0.49999999999999994,
        0.9999999999999999,
        0.49999999999999994,
        0.05714285714285715,
        -0.2714285714285714,
        -0.4285714285714285,
        -0.3571428571428571,
    ]
    assert result == desired_result

    return


if __name__ == "__main__":
    test_empty_melody()
    test_nonempty_melody_contour()
    test_nonempty_melody_correlation()
