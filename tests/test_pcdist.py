"""
Tests for amads/pitch/pcdist1.py
"""

import math

from amads.io.readscore import read_score
from amads.music import example
from amads.pitch.pcdist1 import pitch_class_distribution_1

VERBOSE = False  # to minimize test output, set to True to show score data


def test_pcdist1():
    # for some reason, could not open file with just the relative path
    my_midi_file = example.fullpath("midi/sarabande.mid")

    print("------- input midi file")
    assert my_midi_file is not None
    myscore = read_score(my_midi_file, show=False)
    if VERBOSE:
        myscore.show()
    print("------- finished input midi file")

    print("------- Calculate pitch-class distribution")
    pcd = pitch_class_distribution_1(myscore, weighted=False)
    print(pcd.data)
    desired_data = [
        0.1362126245847176,
        0.013289036544850499,
        0.15946843853820597,
        0.0,
        0.15282392026578073,
        0.10963455149501661,
        0.023255813953488372,
        0.06976744186046512,
        0.05647840531561462,
        0.14950166112956811,
        0.006644518272425249,
        0.12292358803986711,
    ]
    assert all(
        math.isclose(desired, pcd_datum)
        for desired, pcd_datum in zip(desired_data, pcd.data)
    )

    # use matlab compatible (duraccent) weighting
    pcd = pitch_class_distribution_1(
        myscore, weighted=True, miditoolbox_compatible=True
    )
    print(pcd.data)
    desired_data = [
        0.13040292278686316,
        0.013527444471608125,
        0.1518283226105654,
        0.0,
        0.1641310746920629,
        0.09730294411471833,
        0.0293624871319176,
        0.060167650150096674,
        0.06699822737996491,
        0.1636123736836623,
        0.005491345879461721,
        0.11717520709893343,
    ]
    assert all(
        math.isclose(desired, pcd_datum)
        for desired, pcd_datum in zip(desired_data, pcd.data)
    )


if __name__ == "__main__":
    test_pcdist1()
