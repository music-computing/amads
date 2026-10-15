"""
Tests for amads/time/durdist2.py
"""

import math

from amads.algorithms.nnotes import nnotes
from amads.core.histogram import boundaries_to_centers, centers_to_boundaries
from amads.io.readscore import read_score
from amads.music import example
from amads.time.durdist1 import duration_distribution_1
from amads.time.durdist2 import duration_distribution_2


def assert_equal_dist1d(dist, correct, tol=1e-6):
    """Asserts that two 1d distributions are equal within a tolerance."""
    csum = 0.0
    dsum = 0.0
    for i in range(len(correct)):
        csum += correct[i]
        dsum += dist.data[i]
        assert (
            abs(dist.data[i] - correct[i]) < tol
        ), f"dist data mismatch at {i}: {dist.data[i]} vs {correct[i]}"
    assert abs(csum - 1) < tol, "'correct' does not sum to 1"
    assert abs(dsum - 1) < tol, "dist data does not sum to 1"


def assert_equal_dist2d(dist, correct, tol=1e-6):
    """Asserts that two 2d distributions are equal within a tolerance."""
    csum = 0.0
    dsum = 0.0
    for r in range(len(correct)):
        for c in range(len(correct[r])):
            csum += correct[r][c]
            dsum += dist.data[r][c]
            assert abs(dist.data[r][c] - correct[r][c]) < tol, (
                f"dist data mismatch at ({r},{c}): "
                + f"{dist.data[r][c]} vs {correct[r][c]}"
            )
    assert abs(csum - 1) < tol, "'correct' does not sum to 1"
    assert abs(dsum - 1) < tol, "dist data does not sum to 1"


def test_durdist_with_custom_bins():
    """
    Test duration_distribution_2 with custom bin centers.
    """
    # Load example MIDI file
    my_midi_file = example.fullpath("midi/sarabande.mid")
    assert my_midi_file is not None, "Example MIDI file not found."

    # Import MIDI using partitura
    myscore = read_score(my_midi_file, show=False)

    # Calculate duration distribution with custom bins
    centers = [0.05 * (2**i) for i in range(9)]  # Custom boundaries
    dd2 = duration_distribution_2(myscore, bin_centers=centers)

    print("Duration pair distribution, miditoolbox compatible:", dd2)
    print(dd2.data)
    correct = [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.357, 0.047, 0.0, 0.013, 0.003, 0.0, 0.0],
        [0.0, 0.0, 0.050, 0.427, 0.023, 0.013, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.023, 0.017, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.013, 0.013, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    assert_equal_dist2d(dd2, correct, 0.001)

    dd2 = duration_distribution_2(myscore, bin_centers=centers)
    print("Duration pair distribution:", dd2)
    print(dd2.data)
    correct = [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.357, 0.047, 0.0, 0.013, 0.003, 0.0, 0.0],
        [0.0, 0.0, 0.05, 0.427, 0.023, 0.013, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.023, 0.017, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.013, 0.013, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    assert_equal_dist2d(dd2, correct, 0.001)

    # test durdist1 too
    dd1 = duration_distribution_1(myscore, bin_centers=centers)
    print("Duration distribution 1, miditoolbox compatible:", dd1)
    print(dd1.data)
    correct = [0.0, 0.0, 0.4186, 0.5116, 0.0399, 0.0266, 0.0033, 0.0, 0.0]
    assert_equal_dist1d(dd1, correct, 0.001)

    dd3 = duration_distribution_1(
        myscore, bin_centers=centers, ignore_extrema=True
    )
    print("Duration distribution 1:", dd3)
    print(dd3.data)
    correct = [0.0, 0.4186, 0.5116, 0.0399, 0.0266, 0.0033, 0.0]
    assert_equal_dist1d(dd3, correct, 0.001)

    # see if we can relate the two results. First, reconstruct the counts from
    # the probabilities in dd2, using nnotes to get the number of notes
    n = nnotes(myscore)
    dc1 = [round(n * p) for p in dd1.data]
    n_pairs = n - 1  # number of note pairs
    dc2 = [[round(n_pairs * p) for p in row] for row in dd2.data]
    # derive duration counts by summing over rows
    dc2to1 = [0] * len(dc2)
    for col in range(len(dc2[0])):
        s = 0
        for row in range(len(dc2)):
            s += dc2[row][col]
        dc2to1[col] = s
    print("dc2 counts:", dc2)
    print("dc2 to dc1 counts:", dc2to1)
    print("dc1 counts:", dc1)

    # now, one of the duration counts in dc2to1 will be one less than in dc1,
    # because the first note has no "prev" note to form a pair with. This loop
    # will "fix" one and ony one count to make them match (or die trying)
    for i in range(len(dc1)):
        if dc1[i] == dc2to1[i] + 1:
            dc2to1[i] += 1
            break
    else:
        assert False, "Could not reconcile dd1 and dd2 counts"
    assert dc1 == dc2to1, "Duration counts from dd1 and dd2 do not match"

    # test durdist1 with default bins
    dd1_default = duration_distribution_1(myscore)
    print("Duration distribution 1 with default bins:", dd1_default)
    print(dd1_default.data)
    correct = [0.419, 0.0, 0.5116, 0.0, 0.0399, 0.0166, 0.010, 0.0033, 0.0]
    assert_equal_dist1d(dd1_default, correct, 0.001)


def test_long_dur():
    """when durations are outside the bin boundaries"""
    from amads.core.basics import Note, Part, Score

    score = Score()
    _ = Part(
        Note(onset=0.0, duration=20.0, pitch=60),
        Note(onset=21.0, duration=30.0, pitch=62),
        Note(onset=52.0, duration=40.0, pitch=64),
        parent=score,
    )

    # Calculate duration distribution
    dd2 = duration_distribution_2(score)

    print("Duration pair distribution with long durations:", dd2)
    for row in dd2.data:
        for val in row:
            assert (
                val == 0.0
            ), "Expected all zero distribution for long durations"

    dd2 = duration_distribution_2(
        score, bin_centers=boundaries_to_centers([0.3, 1.0, 3.0, 6.0], "log")
    )
    print(
        "Duration pair distribution with long durations, custom bins:", dd2.data
    )
    correct = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    assert_equal_dist2d(dd2, correct)


def test_dd2_long_and_short():
    """
    Test duration_distribution_2 with long and short durations.
    """
    from amads.core.basics import Note, Part, Score

    score = Score()
    _ = Part(
        Note(onset=0.0, duration=0.01, pitch=60),  # very short
        Note(onset=0.02, duration=0.02, pitch=62),
        Note(onset=0.05, duration=8.0, pitch=64),  # very long
        Note(onset=8.1, duration=0.5, pitch=65),
        Note(onset=8.7, duration=2, pitch=66),
        Note(onset=11, duration=0.03, pitch=67),  # very short
        parent=score,
    )

    # Calculate duration distribution (default
    dd2 = duration_distribution_2(score)

    print("Duration pair distribution with long and short durations:", dd2)
    print(dd2.data)
    # Check that the very short and very long durations are handled correctly
    correct = [[0.0] * 9 for _ in range(9)]
    correct[3][7] = 1.0
    print('"correct" values', correct)
    assert_equal_dist2d(dd2, correct)

    # now test with explicit bin boundaries
    boundaries = [0.3, 1.0, 3.0, 6.0]
    dd2b = duration_distribution_2(
        score,
        bin_centers=boundaries_to_centers(boundaries, interpolation="log"),
    )
    print("Duration pair distribution with custom bins:", dd2b)
    print(dd2b.data)
    correct = [[0.2, 0.2, 0.2], [0.2, 0.0, 0.0], [0.2, 0.0, 0.0]]
    assert_equal_dist2d(dd2b, correct)


def test_centers_to_boundaries():
    """
    Test centers_to_boundaries function.
    """
    centers = [0.2, 0.5, 1.0, 2.0, 5.0]
    boundaries = centers_to_boundaries(centers, interpolation="log")
    print("Centers:", centers)
    print("Boundaries:", boundaries)
    correct = [
        math.sqrt(0.2 * 0.5),
        math.sqrt(0.5 * 1.0),
        math.sqrt(1.0 * 2.0),
        math.sqrt(2.0 * 5.0),
    ]
    for b, c in zip(boundaries, correct):
        assert abs(b - c) < 1e-6, f"Boundary mismatch: {b} vs {c}"

    boundaries = centers_to_boundaries(centers, interpolation="linear")
    print("Boundaries (linear):", boundaries)
    correct = [
        (0.2 + 0.5) / 2,
        (0.5 + 1.0) / 2,
        (1.0 + 2.0) / 2,
        (2.0 + 5.0) / 2,
    ]
    for b, c in zip(boundaries, correct):
        assert abs(b - c) < 1e-6, f"Boundary mismatch (linear): {b} vs {c}"
