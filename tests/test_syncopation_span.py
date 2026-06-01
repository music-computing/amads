"""
Pytest suite for the `syncopation_span` module.

Complements the inline doctests with broader behavioural and edge-case
coverage, plus a smoke-test for the matplotlib plot function.

"""

from __future__ import annotations

import pytest

from amads.time.meter.representations import PulseLengths, StartTimeHierarchy
from amads.time.meter.syncopation_span import (
    PairSyncopation,
    SyncopationAnalysis,
    _build_weight_map,
    _positions_in_span,
    analyse,
    default_decay,
    syncopation_for_pair,
    transition_heatmap,
    weight_at_position,
)

# ---------------------------------------------------------------------------


@pytest.fixture
def simple_4_4():
    """
    4/4 hierarchy: pulse lengths [4, 2, 1], cycle length 4.
    Weights at quarter-note grid:
      0.0 -> 3 (downbeat)
      1.0 -> 1
      2.0 -> 2 (half-bar)
      3.0 -> 1
    """
    pl = PulseLengths([4, 2, 1], cycle_length=4)
    sh = StartTimeHierarchy(pl.to_start_hierarchy())
    return sh


@pytest.fixture
def weight_map_4_4(simple_4_4):
    return _build_weight_map(simple_4_4, granular_pulse=1.0)


# ---------------------------------------------------------------------------


class TestBuildWeightMap:
    def test_keys_cover_cycle(self, simple_4_4):
        wm = _build_weight_map(simple_4_4, granular_pulse=1.0)
        assert set(wm.keys()) == {0.0, 1.0, 2.0, 3.0}

    def test_downbeat_is_highest(self, weight_map_4_4):
        assert weight_map_4_4[0.0] > weight_map_4_4[2.0] > weight_map_4_4[1.0]

    def test_eighth_note_grid_doubles_entries(self, simple_4_4):
        wm = _build_weight_map(simple_4_4, granular_pulse=0.5)
        assert len(wm) == 8

    def test_all_weights_positive(self, weight_map_4_4):
        assert all(v > 0 for v in weight_map_4_4.values())


# ---------------------------------------------------------------------------


class TestWeightAtPosition:
    def test_downbeat(self, simple_4_4, weight_map_4_4):
        assert weight_at_position(0.0, simple_4_4, weight_map_4_4) == 3

    def test_half_bar(self, simple_4_4, weight_map_4_4):
        assert weight_at_position(2.0, simple_4_4, weight_map_4_4) == 2

    def test_weak_beat(self, simple_4_4, weight_map_4_4):
        assert weight_at_position(1.0, simple_4_4, weight_map_4_4) == 1

    def test_off_grid_returns_zero(self, simple_4_4, weight_map_4_4):
        assert weight_at_position(0.5, simple_4_4, weight_map_4_4) == 0

    def test_modulo_wraps_correctly(self, simple_4_4, weight_map_4_4):
        # position 4.0 == position 0.0 mod 4
        assert weight_at_position(4.0, simple_4_4, weight_map_4_4) == 3
        assert weight_at_position(5.0, simple_4_4, weight_map_4_4) == 1

    def test_level_weights_scaling(self, simple_4_4, weight_map_4_4):
        # raw weight 3 -> index 2 -> level_weights[2]
        lw = [10.0, 20.0, 100.0]
        assert weight_at_position(0.0, simple_4_4, weight_map_4_4, lw) == 100.0
        assert weight_at_position(2.0, simple_4_4, weight_map_4_4, lw) == 20.0
        assert weight_at_position(1.0, simple_4_4, weight_map_4_4, lw) == 10.0

    def test_level_weights_off_grid_still_zero(
        self, simple_4_4, weight_map_4_4
    ):
        lw = [10.0, 20.0, 100.0]
        assert weight_at_position(0.25, simple_4_4, weight_map_4_4, lw) == 0


# ---------------------------------------------------------------------------


class TestPositionsInSpan:
    def test_within_cycle(self, weight_map_4_4):
        result = _positions_in_span(0.0, 3.0, weight_map_4_4, 4.0)
        positions = [p for p, _ in result]
        assert positions == [1.0, 2.0]

    def test_endpoints_excluded(self, weight_map_4_4):
        result = _positions_in_span(1.0, 3.0, weight_map_4_4, 4.0)
        positions = [p for p, _ in result]
        assert 1.0 not in positions and 3.0 not in positions
        assert 2.0 in positions

    def test_wrap_around(self, weight_map_4_4):
        # span from 3.0 to 5.0 crosses the downbeat at 4.0
        result = _positions_in_span(3.0, 5.0, weight_map_4_4, 4.0)
        positions = [p for p, _ in result]
        assert 4.0 in positions

    def test_empty_span(self, weight_map_4_4):
        # adjacent quarter notes – nothing strictly between 1.0 and 2.0
        result = _positions_in_span(1.0, 2.0, weight_map_4_4, 4.0)
        assert result == []

    def test_result_is_sorted(self, weight_map_4_4):
        result = _positions_in_span(0.0, 4.0, weight_map_4_4, 4.0)
        positions = [p for p, _ in result]
        assert positions == sorted(positions)


# ---------------------------------------------------------------------------


class TestDefaultDecay:
    def test_first_lookahead(self):
        assert default_decay(1) == 1.0

    def test_second_lookahead(self):
        assert default_decay(2) == pytest.approx(0.5)

    def test_reciprocal(self):
        for n in range(1, 10):
            assert default_decay(n) == pytest.approx(1.0 / n)


# ---------------------------------------------------------------------------


class TestSyncopationForPair:
    def test_downbeat_not_syncopated(self, simple_4_4, weight_map_4_4):
        pair = syncopation_for_pair(0.0, 2.0, simple_4_4, weight_map_4_4)
        assert pair.score == 0.0
        assert pair.gap == 0

    def test_weak_beat_syncopated(self, simple_4_4, weight_map_4_4):
        pair = syncopation_for_pair(1.0, 3.0, simple_4_4, weight_map_4_4)
        assert pair.gap == 1
        assert pair.count == 1
        assert pair.score == pytest.approx(1.0)

    def test_strongly_syncopated_crosses_downbeat(
        self, simple_4_4, weight_map_4_4
    ):
        pair = syncopation_for_pair(3.0, 5.0, simple_4_4, weight_map_4_4)
        assert pair.gap == 2
        assert pair.score == pytest.approx(2.0)

    def test_decay_applied(self, simple_4_4, weight_map_4_4):
        pair_full = syncopation_for_pair(
            1.0, 3.0, simple_4_4, weight_map_4_4, decay=1.0
        )
        pair_half = syncopation_for_pair(
            1.0, 3.0, simple_4_4, weight_map_4_4, decay=0.5
        )
        assert pair_half.score == pytest.approx(pair_full.score * 0.5)

    def test_returns_pair_syncopation_instance(
        self, simple_4_4, weight_map_4_4
    ):
        pair = syncopation_for_pair(0.0, 1.0, simple_4_4, weight_map_4_4)
        assert isinstance(pair, PairSyncopation)

    def test_weight_a_stored(self, simple_4_4, weight_map_4_4):
        pair = syncopation_for_pair(2.0, 3.0, simple_4_4, weight_map_4_4)
        assert pair.weight_a == 2  # half-bar weight

    def test_raw_score_equals_count_times_gap(self, simple_4_4, weight_map_4_4):
        pair = syncopation_for_pair(1.0, 3.0, simple_4_4, weight_map_4_4)
        assert pair.raw_score == pair.count * pair.gap


# ---------------------------------------------------------------------------


class TestAnalyse:
    def test_returns_analysis_instance(self, simple_4_4):
        result = analyse([0.0, 1.0, 2.0, 3.0], simple_4_4, granular_pulse=1.0)
        assert isinstance(result, SyncopationAnalysis)

    def test_onset_count_matches(self, simple_4_4):
        onsets = [0.0, 1.0, 2.0, 3.0]
        result = analyse(onsets, simple_4_4, granular_pulse=1.0)
        assert len(result.onset_results) == len(onsets)

    def test_downbeat_score_zero(self, simple_4_4):
        result = analyse([0.0, 1.0, 2.0, 3.0], simple_4_4, granular_pulse=1.0)
        assert result.onset_results[0].score == 0.0

    def test_total_score_equals_sum_of_onset_scores(self, simple_4_4):
        result = analyse([0.0, 1.0, 2.0, 3.0], simple_4_4, granular_pulse=1.0)
        expected = sum(os.score for os in result.onset_results)
        assert result.total_score == pytest.approx(expected)

    def test_max_lookahead_1_only_one_pair(self, simple_4_4):
        result = analyse(
            [0.0, 1.0, 2.0, 3.0],
            simple_4_4,
            granular_pulse=1.0,
            max_lookahead=1,
        )
        for os in result.onset_results:
            assert len(os.pairs) <= 1

    def test_max_lookahead_2_up_to_two_pairs(self, simple_4_4):
        result = analyse(
            [0.0, 1.0, 2.0, 3.0],
            simple_4_4,
            granular_pulse=1.0,
            max_lookahead=2,
        )
        # onset at index 0 can look at indices 1 and 2
        assert len(result.onset_results[0].pairs) == 2

    def test_last_onset_fewer_pairs(self, simple_4_4):
        result = analyse(
            [0.0, 1.0, 2.0, 3.0],
            simple_4_4,
            granular_pulse=1.0,
            max_lookahead=3,
        )
        # last onset has no successors
        assert len(result.onset_results[-1].pairs) == 0

    def test_doctest_example_onset_1_score(self, simple_4_4):
        result = analyse(
            [0.0, 1.0, 2.0, 3.0],
            simple_4_4,
            granular_pulse=1.0,
            max_lookahead=2,
        )
        assert result.onset_results[1].score == pytest.approx(0.5)

    def test_custom_decay_fn(self, simple_4_4):
        constant_decay = lambda n: 1.0  # noqa: E731
        result = analyse(
            [0.0, 1.0, 2.0, 3.0],
            simple_4_4,
            granular_pulse=1.0,
            max_lookahead=2,
            decay_fn=constant_decay,
        )
        # onset at 1.0 with max_lookahead=2: pair (1,2) gap=0, pair (1,3) gap=1 * decay=1
        assert result.onset_results[1].score == pytest.approx(1.0)

    def test_single_onset_zero_score(self, simple_4_4):
        result = analyse([2.0], simple_4_4, granular_pulse=1.0)
        assert result.total_score == 0.0

    def test_hierarchy_stored_in_result(self, simple_4_4):
        result = analyse([0.0, 2.0], simple_4_4, granular_pulse=1.0)
        assert result.hierarchy is simple_4_4


# ---------------------------------------------------------------------------


class TestTransitionHeatmap:
    def test_returns_positions_and_matrix(self, simple_4_4):
        positions, matrix = transition_heatmap(simple_4_4, granular_pulse=1.0)
        assert len(positions) == 4
        assert len(matrix) == 4
        assert all(len(row) == 4 for row in matrix)

    def test_diagonal_is_zero(self, simple_4_4):
        positions, matrix = transition_heatmap(simple_4_4, granular_pulse=1.0)
        for i in range(len(positions)):
            assert matrix[i][i] == 0.0

    def test_doctest_upper_triangle(self, simple_4_4):
        positions, matrix = transition_heatmap(simple_4_4, granular_pulse=1.0)
        assert matrix[2][3] == 0.0  # pos 2 -> pos 3, not syncopated
        assert matrix[1][3] == pytest.approx(
            1.0
        )  # pos 1 -> pos 3, crosses weight-2

    def test_doctest_lower_triangle_wrap(self, simple_4_4):
        positions, matrix = transition_heatmap(simple_4_4, granular_pulse=1.0)
        assert matrix[3][1] == pytest.approx(
            2.0
        )  # wrap-around, crosses downbeat

    def test_all_scores_non_negative(self, simple_4_4):
        _, matrix = transition_heatmap(simple_4_4, granular_pulse=1.0)
        for row in matrix:
            assert all(v >= 0 for v in row)

    def test_positions_sorted(self, simple_4_4):
        positions, _ = transition_heatmap(simple_4_4, granular_pulse=1.0)
        assert positions == sorted(positions)


# ---------------------------------------------------------------------------


class TestPlotTransitionHeatmap:
    """Smoke tests: ensure the plot function runs without error and returns
    the expected (fig, ax) tuple.  No pixel-level assertion is made."""

    def test_returns_fig_and_ax(self, simple_4_4):
        pytest.importorskip("matplotlib")
        from amads.time.meter.syncopation_span import plot_transition_heatmap

        fig, ax = plot_transition_heatmap(
            simple_4_4,
            granular_pulse=1.0,
            write_not_show=False,
            title="Test heatmap",
        )
        import matplotlib.pyplot as plt

        plt.close(fig)  # avoid leaking figures during test run
        assert fig is not None
        assert ax is not None

    def test_mask_lower_runs(self, simple_4_4):
        pytest.importorskip("matplotlib")
        import matplotlib.pyplot as plt

        from amads.time.meter.syncopation_span import plot_transition_heatmap

        fig, ax = plot_transition_heatmap(
            simple_4_4,
            granular_pulse=1.0,
            mask_lower=True,
            write_not_show=False,
        )
        plt.close(fig)

    def test_custom_vmax_runs(self, simple_4_4):
        pytest.importorskip("matplotlib")
        import matplotlib.pyplot as plt

        from amads.time.meter.syncopation_span import plot_transition_heatmap

        fig, ax = plot_transition_heatmap(
            simple_4_4, granular_pulse=1.0, vmax=10.0, write_not_show=False
        )
        plt.close(fig)

    def test_write_not_show_creates_file(
        self, simple_4_4, tmp_path, monkeypatch
    ):
        """write_not_show=True should call savefig rather than show."""
        pytest.importorskip("matplotlib")
        import matplotlib.pyplot as plt

        from amads.time.meter.syncopation_span import plot_transition_heatmap

        # Redirect savefig output to tmp_path
        saved = []

        def mock_savefig(path, *args, **kwargs):
            saved.append(path)

        monkeypatch.setattr(plt, "savefig", mock_savefig)
        fig, ax = plot_transition_heatmap(
            simple_4_4, granular_pulse=1.0, write_not_show=True
        )
        plt.close(fig)
        assert len(saved) == 1
