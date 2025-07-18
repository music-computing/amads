"""
Basic tests of the rhythmic/metrical profiles provided and two syncopation metrics (Keith and WNBD).
"""

__author__ = "Mark Gotham"

from fractions import Fraction

from amads.time.meter import profiles, syncopation


def test_profile_16():
    """
    Test the 16-unit rhythms against a beat pattern every 4th element
    in any attempt to replicate the WNBD paper (which uses cut common time to notate all of these).
    """
    for rhythm, wnbd in [
        (profiles.WorldSample16.shiko, Fraction(6, 5)),  # Confirm, 1.2
        (profiles.WorldSample16.son, Fraction(14, 5)),  # Confirm, 2.8
        (profiles.WorldSample16.rumba, Fraction(18, 5)),  # Confirm, 3.6
        (
            profiles.WorldSample16.soukous,
            Fraction(14, 5),  # TODO divergence. Paper has 3.6 (18/5)
        ),
        (
            profiles.WorldSample16.gahu,
            Fraction(16, 5),  # TODO divergence. Paper has 3.6 (18/5)
        ),
        (
            profiles.WorldSample16.bossa_nova,
            Fraction(16, 5),  # TODO divergence. Paper has 4.
        ),
    ]:
        assert len(rhythm) == 16

        onset_beats = syncopation.vector_to_onset_beat(rhythm, beat_unit_length=4)
        sm = syncopation.SyncopationMetric()
        assert sm.weighted_note_to_beat_distance(onset_beats=onset_beats) == wnbd


def test_profile_12():
    """Test the 12-unit rhythm against a beat pattern every 3rd element."""
    for rhythm, wnbd in [
        (
            profiles.WorldSample12.soli,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.tambú,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.bembé,
            Fraction(18, 7),  # TODO divergence. Paper has 3 (21/7)
        ),
        (
            profiles.WorldSample12.bembé_2,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.yoruba,
            Fraction(18, 7),  # TODO divergence. Paper has 3 (21/7)
        ),
        (
            profiles.WorldSample12.tonada,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.asaadua,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.sorsonet,
            Fraction(18, 7),  # TODO divergence. Paper has 3 (21/7)
        ),
        (
            profiles.WorldSample12.bemba,
            Fraction(12, 7),  # TODO divergence. Paper has 2.142 (15/7, rounded down)
        ),
        (
            profiles.WorldSample12.ashanti,
            Fraction(18, 7),  # TODO divergence. Paper has 2 (14/7)
        ),
    ]:
        assert len(rhythm) == 12

        onset_beats = syncopation.vector_to_onset_beat(rhythm, beat_unit_length=3)
        sm = syncopation.SyncopationMetric()
        assert sm.weighted_note_to_beat_distance(onset_beats=onset_beats) == wnbd
