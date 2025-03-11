"""
Tests for basic normalization routines (norm module).
"""

import pytest

from amads.algorithms.norm import (
    euclidean_distance,
    manhattan_distance,
    normalize,
    shared_length,
)


def test_norm_raises():
    with pytest.raises(ValueError):
        normalize([0, 1, 2, 3], method="unrecognised string")


def test_shared_length_fails():
    profile_1 = [0, 1, 2, 3]
    profile_2 = [1, 2, 3, 4, 5]
    with pytest.raises(ValueError):
        shared_length(profile_1, profile_2)
    with pytest.raises(ValueError):
        manhattan_distance(profile_1, profile_2)
    with pytest.raises(ValueError):
        euclidean_distance(profile_1, profile_2)
