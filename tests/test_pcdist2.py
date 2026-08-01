from amads.core.basics import Score
from amads.pitch.pcdist2 import pitch_class_distribution_2


def test_pitch_class_distribution_2_weighted_does_not_crash():
    """
    Regression test:
    Previous, the `prev_dur` was only initialized inside the `weighted and prev_pc is not None` branch,
    so it stayed None through the first note and calling `prev_dur + dur` on the second note raised TypeError.
    Needs >= 2 notes with distinct onsets/durations to exercise the transition-weighting branch.
    """
    score = Score.from_melody(
        pitches=[60, 64, 67], durations=[1.0, 0.5, 1.5], iois=[1.0, 0.5]
    )
    dist = pitch_class_distribution_2(score, weighted=True)
    assert dist.dimensions == [12, 12]
    total = sum(v for row in dist.data for v in row)
    assert total == 1.0


def test_pitch_class_distribution_2_single_note_part_does_not_crash():
    """
    A part with exactly one note has no transitions at all;
    make sure that edge case
    (`prev_pc`/`prev_dur` never leave their initial None)
    is still handled cleanly.
    """
    score = Score.from_melody(pitches=[60], durations=1.0, iois=1.0)
    dist = pitch_class_distribution_2(score, weighted=True)
    assert dist.dimensions == [12, 12]
    assert sum(v for row in dist.data for v in row) == 0.0
