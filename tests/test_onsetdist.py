"""
Tests for amads/time/onsetdist.py
"""

import pytest

from math import floor
from amads.time.onsetdist import *

__author__ = "Anirudh Subramanian"

def test_onsetdist_flooring():
    """Onsets that are between two divisions of a quarter note round down"""

    score = Score()

    m = Measure(parent=score, onset=0.0)
    n1 = Note(parent=m, onset=0.3, duration=1.0)
    n2 = Note(parent=m, onset=1.99, duration=1.0)

    n_divisions = 4
    result = onset_distribution(
        score,
        quarters_per_measure=4,
        divisions=n_divisions,
    )

    assert result.data[floor((n1.onset - m.onset) * n_divisions)] == 1
    assert result.data[floor((n2.onset - m.onset) * n_divisions)] == 1

def test_onsetdist_irregular_measures():
    """Tests that the distribution works when measures are of uneven lengths"""

    score = Score()

    m1 = Measure(parent=score, onset=1.0, duration=4.0)
    n1 = Note(parent=m1, onset=4.0, duration=1.0) # 3.0 quarters after start of measure

    m2 = Measure(parent=score, onset=6.0, duration=3.0)
    n2 = Note(parent=m2, onset=7.25, duration=1.5) # 1.25 quarters after start of measure

    m3 = Measure(parent=score, onset=10.0, duration=5.0)
    n3 = Note(parent=m3, onset=14.5, duration=0.5) # 4.5 quarters after start of measure

    n_divisions = 4
    result = onset_distribution(
        score,
        quarters_per_measure=max(m1.duration, m2.duration, m3.duration),
        divisions=n_divisions,
    )

    assert result.data[floor((n1.onset - m1.onset) * n_divisions)] == n1.duration
    assert result.data[floor((n2.onset - m2.onset) * n_divisions)] == n2.duration
    assert result.data[floor((n3.onset - m3.onset) * n_divisions)] == n3.duration

def test_onsetdist_tied():
    """Tests that tied notes are merged when calculating distribution"""

    score = Score()
    m = Measure(parent=score, onset=0.0)
    n1 = Note(parent=m, onset=0.0, duration=1.0)
    n2 = Note(parent=m, onset=0.0, duration=2.5)
    n3 = Note(parent=m, onset=1.0, duration=2.0)
    n1.tie = n3

    n_divisions = 4
    result = onset_distribution(
        score,
        quarters_per_measure=4,
        divisions=n_divisions,
    )

    assert result.data[round((n1.onset - m.onset) * n_divisions)] == n1.tied_duration + n2.duration
    assert result.data[round((n3.onset - m.onset) * n_divisions)] == 0