"""
Tests for amads/time/durdist2.py
"""

from amads.algorithms import (
    boundaries_to_centers,
    duration_distribution_1,
    duration_distribution_2,
)
from amads.io import read_score
from amads.music import example


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
    boundaries = [0.05 * (2**i) for i in range(9)]  # Custom boundaries
    dd2 = duration_distribution_2(
        myscore,
        bin_centers=boundaries_to_centers(boundaries),
        miditoolbox_compatible=True,
    )

    print("Duration pair distribution, miditoolbox compatible:", dd2)
    print(dd2.data)
    assert dd2.data == [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [
            0.0,
            0.0,
            0.3566666666665906,
            0.04666666666665671,
            0.009999999999997866,
            0.006666666666665245,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.04999999999998933,
            0.42666666666657566,
            0.029999999999993598,
            0.006666666666665245,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.01333333333333049,
            0.02666666666666098,
            0.01666666666666311,
            0.0,
            0.0,
            0.0,
        ],
        [0.0, 0.0, 0.0, 0.009999999999997866, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]

    dd2 = duration_distribution_2(
        myscore, bin_centers=boundaries_to_centers(boundaries)
    )

    print("Duration pair distribution:", dd2)
    print(dd2.data)
    assert dd2.data == [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [
            0.0,
            0.0,
            0.3566666666666667,
            0.04666666666666667,
            0.01,
            0.006666666666666667,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.05,
            0.4266666666666667,
            0.03,
            0.006666666666666667,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.013333333333333334,
            0.02666666666666667,
            0.016666666666666666,
            0.0,
            0.0,
            0.0,
        ],
        [0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]

    # test durdist1 too
    dd1 = duration_distribution_1(
        myscore,
        bin_centers=boundaries_to_centers(boundaries),
        miditoolbox_compatible=True,
    )
    print("Duration distribution 1, miditoolbox compatible:", dd1)
    print(dd1.data)
    assert dd1.data == [
        0.0,
        0.0,
        0.41860465116277956,
        0.5116279069767306,
        0.056478405315613114,
        0.013289036544850145,
        0.0,
        0.0,
    ]

    dd1 = duration_distribution_1(
        myscore, bin_centers=boundaries_to_centers(boundaries)
    )
    print("Duration distribution 1:", dd1)
    print(dd1.data)
    assert dd1.data == [
        0.0,
        0.0,
        0.4186046511627907,
        0.5116279069767442,
        0.05647840531561462,
        0.013289036544850499,
        0.0,
        0.0,
    ]

    # see if we can relate the two results. First, reconstruct the counts from
    # the probabilities, using dd1 to get the number of notes
    n = sum(dd1.data)
    dc1 = [round(n * p) for p in dd1.data]
    n_pairs = n - 1  # number of note pairs
    dc2 = [[round(n_pairs * p) for p in row] for row in dd2.data]
    # derive duration counts by summing over rows
    dc2to1 = [0] * len(dc1)
    for col in range(len(dc2[0])):
        s = 0
        for row in range(len(dc2)):
            s += dc2[row][col]
        dc2to1[col] = s
    print("dd1 counts:", dc1)
    print("dd2 to dd1 counts:", dc2to1)

    # now, one of the duration counts in dd2to1 will be one less than in dc1,
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
    assert dd1_default.data == [
        0.4186046511627907,
        0.0,
        0.5116279069767442,
        0.0,
        0.03986710963455149,
        0.016611295681063124,
        0.009966777408637873,
        0.0033222591362126247,
        0.0,
    ]
