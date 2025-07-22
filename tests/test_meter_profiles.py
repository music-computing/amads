"""
Basic tests of rhythmic/metrical profiles and syncopation metrics
exactly as reported in Figure 8 and 11 of
Gomez et al. (the WNBD paper).
"""

__author__ = "Mark Gotham"

from fractions import Fraction

from amads.time.meter import profiles, syncopation
from amads.time.rhythm import off_beatness, vector_to_onset_beat


def test_profile_16():
    """
    Test the 16-unit rhythms against a beat pattern every 4th element
    against the table "Figure 8: Binary rhythms" in Gomez et al. (the WNBD paper)

    TODO attempt to resolve the divergences. Failing that:
    We include all of this information as part of our mission to make prior work accessible:
    readers navigating these papers should know about inconsistencies and errors.
    """
    for cycle, off_beat_metric, wnbd in [
        (
            profiles.WorldSample16.shiko,
            0,
            Fraction(6, 5),  # Confirm, 1.2
        ),
        (
            profiles.WorldSample16.son,
            1,
            Fraction(14, 5),  # Confirm, 2.8
        ),
        (
            profiles.WorldSample16.rumba,
            2,
            Fraction(18, 5),  # Confirm, 3.6
        ),
        (
            profiles.WorldSample16.soukous,
            2,
            Fraction(14, 5),  # TODO divergence. Paper has 3.6 (18/5)
        ),
        (
            profiles.WorldSample16.gahu,
            1,
            Fraction(16, 5),  # TODO divergence. Paper has 3.6 (18/5)
        ),
        (
            profiles.WorldSample16.bossa_nova,
            2,
            Fraction(16, 5),  # TODO divergence. Paper has 4.
        ),
    ]:
        assert cycle.count(1) == 5  # Onsets
        assert len(cycle) == 16  # Grid

        assert off_beat_metric == off_beatness(cycle)

        onset_beats = syncopation.vector_to_onset_beat(cycle, beat_unit_length=4)
        sm = syncopation.SyncopationMetric()
        assert sm.weighted_note_to_beat_distance(onset_beats=onset_beats) == wnbd


def test_profile_12():
    """
    Test the 12-unit cycle against a beat pattern every 3rd element
    against the table "Figure 11: Ternary rhythms" in Gomez et al. (the WNBD paper)

    TODO attempt to resolve the divergences. Failing that:
    We include all of this information as part of our mission to make prior work accessible:
    readers navigating these papers should know about inconsistencies and errors.
    """
    for cycle, off_beat_metric, wnbd in [
        (
            profiles.WorldSample12.soli,
            1,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.tambú,
            2,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.bembé,
            3,
            Fraction(18, 7),  # TODO divergence. Paper has 3 (21/7)
        ),
        (
            profiles.WorldSample12.bembé_2,
            2,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.yoruba,
            2,
            Fraction(18, 7),  # TODO divergence. Paper has 3 (21/7)
        ),
        (
            profiles.WorldSample12.tonada,
            1,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.asaadua,
            1,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.sorsonet,
            1,
            Fraction(18, 7),  # TODO divergence. Paper has 3 (21/7)
        ),
        (
            profiles.WorldSample12.bemba,
            2,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.ashanti,
            2,
            Fraction(18, 7),  # TODO divergence. Paper has 2 (14/7)
        ),
    ]:
        assert cycle.count(1) == 7  # Onsets
        assert len(cycle) == 12  # Grid

        assert off_beat_metric == off_beatness(cycle)

        onset_beats = vector_to_onset_beat(cycle, beat_unit_length=3)
        sm = syncopation.SyncopationMetric()
        assert sm.weighted_note_to_beat_distance(onset_beats=onset_beats) == wnbd
