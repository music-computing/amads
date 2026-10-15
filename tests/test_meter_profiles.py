"""
Basic tests of rhythmic/metrical profiles and syncopation metrics
exactly as reported in named Figures of
Gomez et al. (the WNBD paper)
and
Toussaint 2013.

We keep these tests separate for ease of cross-reference with the source,
preserving even the source order and broad structure.

"""

__author__ = "Mark Gotham"

from fractions import Fraction

from amads.core.vector_transforms_checks import (
    indicator_to_interval,
    is_maximally_even,
)
from amads.time.meter import profiles, syncopation
from amads.time.rhythm import (
    has_deep_property,
    has_oddity_property,
    keith_via_toussaint,
    off_beatness,
    vector_to_onset_beat,
)
from amads.time.variability import normalized_pairwise_variability_index

# 16
SHIKO = profiles.WorldSample16.shiko
SON = profiles.WorldSample16.son
SOUKOUS = profiles.WorldSample16.soukous
RUMBA = profiles.WorldSample16.rumba
BOSSA = profiles.WorldSample16.bossa_nova
GAHU = profiles.WorldSample16.gahu

# 12
SOLI = profiles.WorldSample12.soli
TAMBU = profiles.WorldSample12.tambú
BEMBE = profiles.WorldSample12.bembé
BEMBE_2 = profiles.WorldSample12.bembé_2
YORUBA = profiles.WorldSample12.yoruba
TONADA = profiles.WorldSample12.tonada
ASAADUA = profiles.WorldSample12.asaadua
SORSONET = profiles.WorldSample12.sorsonet
BEMBA = profiles.WorldSample12.bemba
ASHANTI = profiles.WorldSample12.ashanti


def count_non_zero(data):
    return sum(1 for element in data if element != 0)


def test_profile_basics():
    for profile in (SHIKO, SON, SOUKOUS, RUMBA, BOSSA, GAHU):
        assert profile.count(1) == 5  # Onsets
        assert len(profile) == 16  # Grid


def test_toussaint_17_13():
    """
    Test the 16-unit rhythms with a beat pattern every 4th element
    against "Figure" 17.13 (p.120) in Toussaint 2013 (partial, work in progress)
    """
    tested_profile_order = (
        SHIKO,
        SON,
        SOUKOUS,
        RUMBA,
        GAHU,
        BOSSA,
    )  # sic GAHU, BOSSA

    # TODO Pressing, Lempel-Ziv, Entropy, "Metric", etc.

    # Distinct Distances
    assert [
        count_non_zero(indicator_to_interval(profile, adjacent_not_all=False))
        for profile in tested_profile_order
    ] == [4, 5, 7, 6, 7, 4]

    # nPVI
    assert [
        round(
            normalized_pairwise_variability_index(
                indicator_to_interval(profile)
            ),
            1,
        )
        for profile in tested_profile_order
    ] == [66.7, 40.5, 70.5, 41.0, 23.8, 14.3]


def test_toussaint_37_11():
    """
    Test the 16-unit rhythms with a beat pattern every 4th element
    against "Figure" 37.11 (p.290) in Toussaint 2013.
    TODO currently partial, work in progress, though note: several from the table covered elsewhere in the module:
    - 'Off-beatness'
    - Distinct durations
    """
    tested_profile_order = (
        SHIKO,
        SON,
        SOUKOUS,
        RUMBA,
        BOSSA,
        GAHU,
    )  # sic BOSSA, GAHU

    assert [is_maximally_even(profile) for profile in tested_profile_order] == [
        False,
        False,
        False,
        False,
        True,
        False,
    ]

    assert [
        has_oddity_property(profile) for profile in tested_profile_order
    ] == [
        False,
        True,
        False,
        True,
        True,
        False,
    ]

    # Distinct _adjacent_ distances. Note: _all_ distinct distances already tested above.
    assert [
        count_non_zero(
            indicator_to_interval(
                profile, adjacent_not_all=True, sequence_not_vector=False
            )
        )
        for profile in tested_profile_order
    ] == [2, 3, 4, 3, 2, 3]

    assert [has_deep_property(profile) for profile in tested_profile_order] == [
        True,
        False,
        False,
        False,
        True,
        False,
    ]


def test_wnbd_16():
    """
    Test the 16-unit rhythms with a beat pattern every 4th element
    against "Figure 8: Binary rhythms" in Gomez et al. (the WNBD paper)
    """
    for (
        cycle,
        keith_value,
        off_beat_metric,
        wnbd,
    ) in [  # Paper's fractional values confirmed in in-line comments
        (SHIKO, 1, 0, Fraction(6, 5)),  # 1.2 (6/5)
        (SON, 2, 1, Fraction(14, 5)),  # 2.8 (14/5)
        (RUMBA, 2, 2, Fraction(18, 5)),  # 3.6 (18/5)
        (SOUKOUS, 3, 2, Fraction(18, 5)),  # 3.6 (18/5)
        (GAHU, 3, 1, Fraction(18, 5)),  # 3.6 (18/5)
        (BOSSA, 3, 2, Fraction(4, 1)),  # 4
    ]:

        assert keith_via_toussaint(cycle) == keith_value

        assert off_beat_metric == off_beatness(cycle)

        onset_beats = syncopation.vector_to_onset_beat(
            cycle, beat_unit_length=4
        )
        sm = syncopation.SyncopationMetric()
        cycle_length = Fraction(len(cycle), 4)
        assert (
            sm.weighted_note_to_beat_distance(
                onset_beats=onset_beats, cycle_length=cycle_length
            )
            == wnbd
        )


def test_wnbd_12():
    """
    Test the 12-unit cycle with a beat pattern every 3rd element
    against the table "Figure 11: Ternary rhythms" in Gomez et al. (the WNBD paper)
    """
    for (
        cycle,
        off_beat_metric,
        wnbd,
    ) in [  # Paper's fractional values confirmed in in-line comments
        (SOLI, 1, Fraction(15, 7)),  # 2.142
        (TAMBU, 2, Fraction(15, 7)),  # 2.142
        (BEMBE, 3, Fraction(3, 1)),  # 3
        (BEMBE_2, 2, Fraction(15, 7)),  # 2.142
        (YORUBA, 2, Fraction(3, 1)),  # 3
        (TONADA, 1, Fraction(15, 7)),  # 2.142
        (ASAADUA, 1, Fraction(15, 7)),  # 2.142
        (SORSONET, 1, Fraction(3, 1)),  # 3
        (BEMBA, 2, Fraction(15, 7)),  # 2.142
        (ASHANTI, 2, Fraction(3, 1)),  # 3
    ]:
        assert cycle.count(1) == 7  # Onsets
        assert len(cycle) == 12  # Grid

        assert off_beat_metric == off_beatness(cycle)

        onset_beats = vector_to_onset_beat(cycle, beat_unit_length=3)
        sm = syncopation.SyncopationMetric()
        cycle_length = Fraction(len(cycle), 3)
        assert (
            sm.weighted_note_to_beat_distance(
                onset_beats=onset_beats,
                cycle_length=cycle_length,  # Note no issue here: same results with 3, 4, and 12.
            )
            == wnbd
        )


def test_oddity_12():
    tested_profile_order = [
        SOLI,
        TAMBU,
        BEMBE,
        BEMBE_2,
        YORUBA,
        TONADA,
        ASAADUA,
        SORSONET,
        BEMBA,
        ASHANTI,
    ]
    assert [
        has_oddity_property(profile) for profile in tested_profile_order
    ] == [False] * 10
