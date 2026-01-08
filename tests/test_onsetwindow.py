"""Tests for onset_window function.

Author: Tai Nakamura (2025)
"""

import pytest

from amads.algorithms.slice import onset_window
from amads.core.basics import Score
from amads.core.timemap import TimeMap


class TestOnsetWindow:
    """Test suite for onset_window function."""

    def test_basic_filtering_quarters(self):
        """Half-open: include onsets >=1.0 and <3.0 quarters."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65, 67],
            onsets=[0.0, 1.0, 2.0, 3.0, 4.0],
        )

        # Filter notes between 1.0 and 3.0 quarters
        filtered = onset_window(score, 1.0, 3.0, timetype="quarters")

        assert len(filtered) == 2
        assert [n.pitch.key_num for n in filtered] == [62, 64]

    def test_boundary_half_open(self):
        """Half-open boundary: include min, exclude max."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65],
            onsets=[0.0, 1.0, 2.0, 3.0],
        )

        # Test min boundary
        filtered = onset_window(score, 0.0, 1.5)
        assert len(filtered) == 2
        assert filtered[0].pitch.key_num == 60
        assert filtered[1].pitch.key_num == 62

        # Test max boundary
        filtered = onset_window(score, 1.5, 3.0)
        assert len(filtered) == 1
        assert filtered[0].pitch.key_num == 64

    def test_zero_duration_window(self):
        """Half-open with min_time == max_time returns empty."""
        score = Score.from_melody([60, 62, 64], onsets=[0.0, 1.0, 2.0])

        filtered = onset_window(score, 1.0, 1.0)
        assert len(filtered) == 0

    def test_with_seconds_time_type(self):
        """Test filtering with seconds time type."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65],
            onsets=[0.0, 1.0, 2.0, 3.0],
        )
        # Set tempo: 120 BPM means 1 quarter = 0.5 seconds
        score.time_map = TimeMap(qpm=120)

        # Filter between 0.5 and 1.5 seconds (1.0 and 3.0 quarters)
        filtered = onset_window(score, 0.5, 1.5, timetype="seconds")

        assert len(filtered) == 2
        assert [n.pitch.key_num for n in filtered] == [62, 64]

    def test_invalid_time_type(self):
        """Test that invalid timetype raises ValueError."""
        score = Score.from_melody([60, 62, 64])

        with pytest.raises(ValueError, match="Invalid timetype"):
            onset_window(score, 0.0, 1.0, timetype="invalid")
