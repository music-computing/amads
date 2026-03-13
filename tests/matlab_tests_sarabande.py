import json

from amads.core.basics import Score

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
        result = dist_func(score)
        matlab_result = json_results[matlab_func_json_string]
        assert isinstance(result, Distribution)
        print(matlab_func_json_string)
        print(result.data)
        print(matlab_result)
        assert result.data == matlab_result


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

    assert kkkey(score) == matlab_result_py


def segmentgestalt_test_internal(score: Score, json_results: Dict):
    # ? segment getsalt has 2 results, bot hthe clang peaks as well as
    # ? the segment boundaries
    matlab_result = json_results["segmentgestalt"]
    py_result = segment_gestalt(score)
    py_result_matlab = [int(item) for item in py_result[0] + py_result[1]]
    assert(matlab_result == py_result_matlab)
    assert 0


def test_against_matlab_results():
    # import sarabande.midi
    score = pretty_midi_import(
        example.fullpath("midi/sarabande.mid"), "midi"
    )

    score.show()

    # import json test results that were exported from the script
    json_results = None
    with open("tests/matlab_results_sarabande.json") as json_file:
        json_results = json.load(json_file)
    assert(json_results)

    # all tested functions and their corresponding matlab result strings
    # (in the json) are listed in pairs for easy reading
    dist_functions_test_internal(score, json_results)
    nnotes_test_internal(score, json_results)
    keymode_test_internal(score, json_results)
    kkkey_test_internal(score, json_results)

    return

test_against_matlab_results()