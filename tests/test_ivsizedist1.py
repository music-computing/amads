from amads.core.basics import Score
from amads.pitch.ivsizedist1 import interval_size_distribution_1


def test_interval_size_distribution_1_has_13_bins():
    """
    Regression test: isd is built as a 13-element list
    (unison through octave inclusive),
    so dimensions/x_categories must say 13, not 12,
    or Distribution's shape validation (and any plotting) breaks.
    """
    score = Score.from_melody(pitches=[60, 64, 67, 72], durations=1.0, iois=1.0)
    dist = interval_size_distribution_1(score, weighted=False)
    assert dist.dimensions == [13]
    assert len(dist.data) == 13
    assert len(dist.x_categories) == 13
    assert dist.x_categories == [str(i) for i in range(13)]


def test_interval_size_distribution_1_empty_score_is_all_zero():
    score = Score.from_melody(pitches=[60], durations=1.0, iois=1.0)
    dist = interval_size_distribution_1(score, weighted=False)
    assert dist.dimensions == [13]
    assert dist.data == [0.0] * 13
