import json
import math

from amads.core.basics import Score, Note

from amads.io.pm_midi_import import pretty_midi_import
from amads.music import example
from amads.core.distribution import Distribution
from amads.pitch.pcdist1 import pitch_class_distribution_1
from amads.pitch.ivdist1 import interval_distribution_1
from amads.time.durdist1 import duration_distribution_1
from amads.algorithms.nnotes import nnotes
from amads.pitch.key.keymode import keymode
from amads.pitch.key.kkkey import kkkey
from amads.melody.segment_gestalt import segment_gestalt

from typing import Dict

from dataclasses import dataclass
from amads.pitch.key.profiles import KeyProfile, PitchProfile


@dataclass
class TestProfile(KeyProfile):
    name: str = "Test Profile"
    literature: str = "Testing Literature"
    about: str = "Testing Profile"
    major: PitchProfile = PitchProfile(
        "TestProfile.major",
        (
            0.39,
            0.14,
            0.21,
            0.14,
            0.27,
            0.25,
            0.15,
            0.32,
            0.15,
            0.22,
            0.14,
            0.18,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "TestProfile.minor",
        (
            0.38,
            0.16,
            0.21,
            0.32,
            0.15,
            0.21,
            0.15,
            0.28,
            0.24,
            0.16,
            0.2,
            0.19,
        ),
    )

testprofile = TestProfile()


def dist_functions_test_internal(score: Score, json_results: Dict):
    # list pairs of correspondences between the distribution functions
    # and their matlab couterparts
    # we did not further modularize this because some functions may require
    # custom parameters
    dist_function_correspondences = [
        (pitch_class_distribution_1, "pcdist1"),
        (interval_distribution_1, "ivdist1"),
        (duration_distribution_1, "durdist1"),
    ]
    for dist_func, matlab_func_json_string in dist_function_correspondences:
        result = dist_func(score, miditoolbox_compatible=True)
        matlab_result = json_results[matlab_func_json_string]
        assert isinstance(result, Distribution)
        print(matlab_func_json_string)
        print(result.data)
        print(matlab_result)
        assert all(
            math.isclose(py_data, mlb_result, abs_tol=1e-4)
            for py_data, mlb_result in zip(result.data, matlab_result)
        )


def nnotes_test_internal(score: Score, json_results: Dict):
    assert nnotes(score, True) == json_results["nnotes"]


def keymode_test_internal(score: Score, json_results: Dict):
    # converts integer results from matlab keymode into python results
    keymode_interpretation = [["major", "minor"], ["major"], ["minor"]]
    assert keymode(score) == keymode_interpretation[json_results["keymode"]]


def kkkey_test_internal(score: Score, json_results: Dict):
    matlab_result = json_results["kkkey"]
    matlab_result_py = None
    matlab_py_key_index = (matlab_result - 1) % 12
    if matlab_result > 12:
        matlab_result_py = ("minor", matlab_py_key_index)
    elif matlab_result <= 12:
        matlab_result_py = ("major", matlab_py_key_index)

    py_result = kkkey(score, profile=testprofile)

    assert py_result == matlab_result_py


def segmentgestalt_test_internal(score: Score, json_results: Dict):
    # ? segment getsalt has 2 results, bot hthe clang peaks as well as
    # ? the segment boundaries
    matlab_result = json_results["segmentgestalt"]
    py_result = segment_gestalt(score)
    print(py_result)
    py_result_matlab = [int(item) for item in py_result[0] + py_result[1]]
    assert matlab_result == py_result_matlab


def test_against_matlab_results():
    # import sarabande.midi
    score = pretty_midi_import(
        example.fullpath("midi/sarabande.mid"), "midi", flatten=True
    )

    # obtain first 10 notes
    notes_list = []
    for idx, note in enumerate(score.find_all(Note)):
        if idx >= 10:
            break
        notes_list.append(note)
    pitches = [note.pitch for note in notes_list]
    durations = [note.duration for note in notes_list]
    onsets = [note.onset for note in notes_list]
    time_map = score.time_map
    time_signatures = score.time_signatures

    score = Score.from_melody(
        pitches=pitches,
        durations=durations,
        onsets=onsets,
    )
    assert hasattr(score, "time_map") and hasattr(score, "time_signatures")
    score.time_map = time_map
    score.time_signatures = time_signatures

    score.show()

    # import json test results that were exported from the script
    json_results = None
    with open("tests/matlab_results_sarabande.json") as json_file:
        json_results = json.load(json_file)
    assert json_results

    # all tested functions and their corresponding matlab result strings
    # (in the json) are listed in pairs for easy reading
    dist_functions_test_internal(score, json_results)
    nnotes_test_internal(score, json_results)
    # keymode_test_internal(score, json_results)
    kkkey_test_internal(score, json_results)
    segmentgestalt_test_internal(score, json_results)

    return


test_against_matlab_results()
