"""
Tests for amads/pitch/pcdist1.py
"""

from amads.all import import_midi, pitch_class_distribution_1
from amads.music import example

from .test_durdist import assert_equal_dist1d


def test_pcdist1():
    # for some reason, could not open file with just the relative path
    my_midi_file = example.fullpath("midi/sarabande.mid")

    print("------- input midi file")
    assert my_midi_file is not None
    myscore = import_midi(my_midi_file, show=False)
    myscore.show()
    print("------- finished input midi file")

    print("------- Calculate pitch-class distribution")
    pcd = pitch_class_distribution_1(myscore, weighted=False)
    print(pcd.data)
    assert_equal_dist1d(
        pcd,
        [
            0.13621,
            0.01328,
            0.15946,
            0.0,
            0.15282,
            0.10963,
            0.02325,
            0.06976,
            0.05647,
            0.14950,
            0.00664,
            0.12292,
        ],
        0.0001,
    )

    # use matlab compatible (duraccent) weighting
    pcd = pitch_class_distribution_1(
        myscore, weighted=True, miditoolbox_compatible=True
    )
    print(pcd.data)
    assert_equal_dist1d(
        pcd,
        [
            0.13468,
            0.01383,
            0.15803,
            0.00000,
            0.15395,
            0.10322,
            0.02472,
            0.06591,
            0.06099,
            0.15488,
            0.00636,
            0.12337,
        ],
        0.0001,
    )
