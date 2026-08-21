"""Tests for Histogram1D behavior."""

import pytest

from amads.core.histogram import Histogram1D, boundaries_to_centers


def test_histogram_ignore_extrema_last_bin_and_discard_out_of_range():
    """Values in range should fill bins, and high out-of-range values are dropped."""
    boundaries = [0, 10, 20, 30]
    centers = boundaries_to_centers(boundaries)
    h = Histogram1D(
        bin_boundaries=boundaries,
        bin_centers=centers,
        ignore_extrema=True,
    )

    h.add_point(25)  # expected to add to last bin
    assert h.bins == [0.0, 0.0, 1.0]

    h.add_point(31)  # expected to discard value
    assert h.bins == [0.0, 0.0, 1.0]


def test_histogram_centers_only_ignore_extrema_false_linear():
    h = Histogram1D(bin_centers=[10, 20, 30], ignore_extrema=False)

    for value in [5, 15, 24.9, 25, 40]:
        h.add_point(value)

    assert h.bins == [1.0, 2.0, 2.0]


def test_histogram_centers_only_ignore_extrema_true_raises():
    with pytest.raises(ValueError):
        Histogram1D(bin_centers=[10, 20, 30], ignore_extrema=True)


def test_histogram_boundaries_only_ignore_extrema_false_linear():
    h = Histogram1D(bin_boundaries=[0, 10, 20, 30], ignore_extrema=False)

    for value in [-2, 10, 15, 20, 99]:
        h.add_point(value)

    assert h.bins == [1.0, 2.0, 2.0]


def test_histogram_boundaries_only_ignore_extrema_true_linear():
    h = Histogram1D(bin_boundaries=[0, 10, 20, 30], ignore_extrema=True)

    for value in [-1, 0, 10, 20, 30, 31]:
        h.add_point(value)

    assert h.bins == [1.0, 1.0, 1.0]


def test_histogram_two_centers_ignore_extrema_false():
    h = Histogram1D(bin_centers=[10, 20], ignore_extrema=False)

    for value in [1, 15, 100]:
        h.add_point(value)

    assert h.bins == [1.0, 2.0]


def test_histogram_centers_only_log_interpolation():
    h = Histogram1D(
        bin_centers=[1, 100, 10000],
        interpolation="log",
        ignore_extrema=False,
    )

    assert h.bin_boundaries == pytest.approx([10.0, 1000.0])

    for value in [5, 10, 500, 1000, 100000]:
        h.add_point(value)

    assert h.bins == [1.0, 2.0, 2.0]
