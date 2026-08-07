"""Tests for onset_window function.

Author: Tai Nakamura (2026)
"""

from amads.algorithms.slice.onsetwindow import onset_window
from amads.core.basics import Note, Part, Score
from amads.core.timemap import TimeMap


class TestOnsetWindow:
    """Test suite for onset_window function."""

    def test_basic_filtering_quarters(self):
        """Half-open: include onsets >=1.0 and <3.0 quarters."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65, 67],
            onsets=[0.0, 1.0, 2.0, 3.0, 4.0],
        )

        filtered = onset_window(score, 1.0, 3.0)

        assert len(filtered) == 2
        assert [n.pitch.key_num for n in filtered] == [62, 64]

    def test_boundary_half_open(self):
        """Half-open boundary: include min, exclude max."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65],
            onsets=[0.0, 1.0, 2.0, 3.0],
        )

        filtered = onset_window(score, 0.0, 1.5)
        assert len(filtered) == 2
        assert filtered[0].pitch.key_num == 60
        assert filtered[1].pitch.key_num == 62

        filtered = onset_window(score, 1.5, 3.0)
        assert len(filtered) == 1
        assert filtered[0].pitch.key_num == 64

    def test_zero_duration_window(self):
        """Half-open with min_time == max_time returns empty."""
        score = Score.from_melody([60, 62, 64], onsets=[0.0, 1.0, 2.0])

        filtered = onset_window(score, 1.0, 1.0)
        assert len(filtered) == 0

    def test_with_seconds_after_convert(self):
        """Filter in seconds after converting the score."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65],
            onsets=[0.0, 1.0, 2.0, 3.0],
        )
        score.time_map = TimeMap(qpm=120)
        score.convert_to_seconds()

        filtered = onset_window(score, 0.5, 1.5)

        assert len(filtered) == 2
        assert [n.pitch.key_num for n in filtered] == [62, 64]

    def test_quarters_window_after_convert_to_quarters(self):
        """Filter in quarters after converting a seconds score."""
        score = Score()
        score.convert_to_seconds()
        score.time_map = TimeMap(qpm=120)
        part = Part(parent=score)
        Note(parent=part, onset=0.0, duration=0.5, pitch=60)
        Note(parent=part, onset=0.5, duration=0.5, pitch=62)
        Note(parent=part, onset=1.0, duration=0.5, pitch=64)
        Note(parent=part, onset=1.5, duration=0.5, pitch=65)

        score.convert_to_quarters()
        filtered = onset_window(score, 1.0, 3.0)

        assert len(filtered) == 2
        assert [n.pitch.key_num for n in filtered] == [62, 64]

    def test_iterable_passage(self):
        """Test Iterable[Note]."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65],
            onsets=[0.0, 1.0, 2.0, 3.0],
        )
        notes = score.get_sorted_notes()

        filtered = onset_window(notes, 1.0, 3.0)

        assert len(filtered) == 2
        assert [n.pitch.key_num for n in filtered] == [62, 64]

    def test_boundary_miditoolbox_compatible(self):
        """Closed interval includes onset at max_time."""
        score = Score.from_melody(
            pitches=[60, 62, 64, 65],
            onsets=[0.0, 1.0, 2.0, 3.0],
        )

        filtered = onset_window(score, 1.0, 3.0, miditoolbox_compatible=True)

        assert len(filtered) == 3
        assert [n.pitch.key_num for n in filtered] == [62, 64, 65]

    def test_miditoolbox_zero_duration_window(self):
        """Closed interval with min_time == max_time"""
        score = Score.from_melody([60, 62, 64], onsets=[0.0, 1.0, 2.0])

        filtered = onset_window(score, 1.0, 1.0, miditoolbox_compatible=True)

        assert len(filtered) == 1
        assert filtered[0].pitch.key_num == 62
