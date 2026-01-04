import numpy as np
import pytest

import amads.pitch.key.profiles as prof
from amads.core.basics import Score
from amads.io.readscore import import_midi
from amads.music import example
from amads.pitch.key.key_cc import key_cc


def test_error_handling():
    """Invalid attribute name should return None"""
    score = Score.from_melody([60, 62, 64])
    result = key_cc(score, prof.krumhansl_kessler, ["invalid_attribute"])
    assert result == [("invalid_attribute", None)]


def test_empty_melody():
    score = Score.from_melody([])
    with pytest.raises(RuntimeError):
        key_cc(score, prof.krumhansl_kessler, ["major", "minor"])


def test_equal_prob_melody():
    """
    Equal prob melody containing 1 of each pitch.
    Without salience this should return all 24 coefficients as equivalent
    for all 3 profiles of kkcc
    """
    melody = list(range(60, 72))  # C4 to B4
    score = Score.from_melody(melody)
    for profile in [
        prof.krumhansl_kessler,
        prof.temperley,
        prof.albrecht_shanahan,
    ]:
        with pytest.raises(RuntimeError):
            key_cc(score, profile, ["major", "minor"])
    return


def test_none_input():
    score = Score.from_melody([60, 62, 64])
    result = key_cc(score, prof.krumhansl_kessler)
    names = [name for name, _ in result]
    # _sum options removed, len(result) changed from 4 to 2
    assert "major" in names and "minor" in names and len(result) == 2
    for _, corr in result:
        assert corr is None or (len(corr) == 12)


def test_crafted_nonempty_melodies():
    """
    These melodies are here to test the various codepaths and are specific
    to the implementation itself...
    """
    # C major scale
    score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])

    # transpositionally equivalent
    result = key_cc(score, prof.bellman_budge, ["major", "minor"])
    assert isinstance(result, list)
    assert len(result) == 2
    for (attr, corr), expected in zip(result, ["major", "minor"]):
        assert attr == expected
        assert corr is not None
        assert len(corr) == 12
        assert all(isinstance(x, float) for x in corr)  # floats expected

    # transpositionally unequivalent
    result2 = key_cc(score, prof.quinn_white, ["major_asym", "minor_asym"])
    assert isinstance(result2, list)
    assert len(result2) == 2
    for (attr, corr), expected in zip(result2, ["major_asym", "minor_asym"]):
        assert attr == expected
        assert corr is not None
        assert len(corr) == 12
        assert all(isinstance(x, float) for x in corr)  # floats expected


def test_salience():
    score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    result = key_cc(
        score, prof.bellman_budge, ["major", "minor"], salience_flag=True
    )

    desired_result = [
        (
            "major",
            (
                0.8589199195366316,
                -0.4928457031507043,
                0.13510786343852957,
                0.021800560014594423,
                -0.4848395336049385,
                0.8864712999650085,
                -0.7580783042781523,
                0.49867476936679633,
                -0.26277204130638754,
                -0.07430447758834385,
                0.5116620962143172,
                -0.8397964486073511,
            ),
        ),
        (
            "minor",
            (
                0.48763696023361736,
                -0.5157939127725522,
                0.5098344810194787,
                -0.46897908125799087,
                -0.019579162103099696,
                0.49606499477013105,
                -0.419549682349258,
                0.34970893349182736,
                -0.6227295770208436,
                0.5195833057186816,
                0.06438698022010515,
                -0.38058423995009677,
            ),
        ),
    ]
    for (attr, corr), (expected_attr, expected_corr) in zip(
        result, desired_result
    ):
        assert attr == expected_attr
        assert np.allclose(corr, expected_corr, rtol=1e-15)


def test_sarabande():
    from amads.pitch.pcdist1 import pitch_class_distribution_1

    my_midi_file = example.fullpath("midi/sarabande.mid")
    myscore = import_midi(my_midi_file, show=False)

    pcd = np.array([pitch_class_distribution_1(myscore, False)])
    print("Pitch-Class Distribution:", pcd)

    result = key_cc(myscore, prof.krumhansl_kessler, ["major", "minor"])

    assert isinstance(result, list)
    assert len(result) == 2
    for (attr, corr), expected in zip(result, ["major", "minor"]):
        assert attr == expected
        assert corr is not None
        assert len(corr) == 12
        assert all(isinstance(x, float) for x in corr)  # floats expected

    desired_result = [
        (
            "major",
            (
                0.618783892738462,
                -0.6519513221653466,
                0.4875907439536567,
                -0.5290638735709131,
                0.2542559399388133,
                0.4379780281498363,
                -0.7149269867198986,
                0.5069337968414559,
                -0.45268834604256136,
                0.44440110296372387,
                -0.15309251162008541,
                -0.24822046446714316,
            ),
        ),
        (
            "minor",
            (
                -0.044203856666773005,
                -0.1307611916483344,
                0.5377973285450691,
                -0.7181318384052082,
                0.4801058958544669,
                -0.07985223669882462,
                -0.022968241834542897,
                -0.13552507482362564,
                -0.3137266030925678,
                0.7957737140544804,
                -0.6323415693586513,
                0.2638336740745113,
            ),
        ),
    ]

    for (attr, corr), (expected_attr, expected_corr) in zip(
        result, desired_result
    ):
        assert attr == expected_attr
        assert np.allclose(corr, expected_corr, rtol=1e-15)


def test_random_generated_melodies():
    """
    These are randomly generated (but deterministic due to fixed seed) melodies
    Are we sure we have a reference implementation or a decent set of
    verification properties to test against to pull this one off?
    """
    np.random.seed(42)
    test_iterations = 10
    for _ in range(test_iterations):
        pitches = np.random.randint(
            60, 72, size=16
        )  # length 16, pitches from C4 to B4
        score = Score.from_melody(pitches.tolist())
        result = key_cc(score, prof.sapp, ["major", "minor"])
        assert isinstance(result, list)
        assert len(result) == 2
        for (attr, corr), expected in zip(result, ["major", "minor"]):
            assert attr == expected
            assert corr is not None
            assert len(corr) == 12
            assert all(isinstance(x, float) for x in corr)  # floats expected
