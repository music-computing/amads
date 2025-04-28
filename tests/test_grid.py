"""
Basic tests of error raising in metrical grid module.
"""

__author__ = "Mark Gotham"

from collections import Counter

import pytest

from amads.time.meter import grid


def test_metrical_gcm_counter():
    with pytest.raises(ValueError):
        grid.metrical_gcm(starts=Counter({0: 4, 1.5: 2}))


def test_metrical_gcm_bins():
    with pytest.raises(ValueError):
        grid.metrical_gcm(starts=[0, 1, 2, 3], bins=1.6)


def test_metrical_gcm_distance_threshold():
    with pytest.raises(ValueError):
        grid.metrical_gcm(starts=[0, 1, 2, 3], distance_threshold=-1)


def test_metrical_gcm_proportion_threshold():
    with pytest.raises(ValueError):
        grid.metrical_gcm(
            starts=[0, 1, 2, 3],
            proportion_threshold=3,
        )
