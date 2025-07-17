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
