"""
Basic tests of error raising in metrical grid module.
"""

__author__ = "Mark Gotham"

from collections import Counter

import pytest

from amads.time.meter import grid


def test_metrical_gcd_counter():
    with pytest.raises(ValueError):
        grid.metrical_gcd(starts=Counter({0: 4, 1.5: 2}))


def test_metrical_gcd_bins():
    with pytest.raises(ValueError):
        grid.metrical_gcd(starts=[0, 1, 2, 3], bins=1.6)


def test_metrical_gcd_distance_threshold():
    with pytest.raises(ValueError):
        grid.metrical_gcd(starts=[0, 1, 2, 3], atol=-1)


def test_metrical_gcd_proportion_threshold():
    with pytest.raises(ValueError):
        grid.metrical_gcd(
            starts=[0, 1, 2, 3],
            proportion_threshold=3,
        )
