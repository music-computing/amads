import json
import math

import numpy as np

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
from amads.melody.boundary import boundary
from amads.time.notedensity import note_density

from typing import Dict

from dataclasses import dataclass
from amads.pitch.key.profiles import KeyProfile, PitchProfile


@dataclass
class TestProfile(KeyProfile):
    name: str = "Test Profile"
    literature: str = "kkprofs profile values in MidiToolbox1.1"
    about: str = "This test profile corresponds to the kkprofs profile in " \
    "miditoolbox1.1. It is included separately because it is slightly altered " \
    "from its original intention of being a normalized krumhansl-kessler" \
    "key profile"
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

def _extract_gestalt_marks(score):
    """
    annotates the score when there is a clang onset and/or segment onset
    by setting has_clang_onset and/or has_segment_onset to True
    and False otherwise
    """
    clang_indices = []
    seg_indices = []
    for idx, note in enumerate(score.find_all(Note)):
        clang_onset = note.get("has_clang_onset", None)
        segment_onset = note.get("has_segment_onset", None)
        assert clang_onset is not None and segment_onset is not None
        if clang_onset:
            clang_indices.append(idx)
        if segment_onset:
            seg_indices.append(idx)

    return clang_indices, seg_indices

def segmentgestalt_test_internal(score: Score, json_results: Dict):
    matlab_result = json_results["segmentgestalt"]
    py_matlab_result = list(np.nonzero(matlab_result)[0])
    score = segment_gestalt(score)
    clang_indices, seg_indices = _extract_gestalt_marks(score)
    score_len = nnotes(score)
    py_result = clang_indices + [idx + score_len for idx in seg_indices]

    assert py_result == py_matlab_result

def _extract_boundary_marks(score):
    boundary_strengths = []
    for note in score.find_all(Note):
        boundary_strength = note.get("boundary_strength", None)
        boundary_strengths.append(boundary_strength)
    return boundary_strengths

def boundary_test_internal(score: Score, json_results: Dict):
    matlab_result = json_results["boundary"]
    score = boundary(score)
    py_result = _extract_boundary_marks(score)

    assert all(
        math.isclose(py_data, mlb_result, abs_tol=1e-9)
        for py_data, mlb_result in zip(py_result, matlab_result)
    )

def notedensity_test_internal(score: Score, json_results: Dict):
    matlab_result = json_results["notedensity"]
    assert score.units_are_quarters
    py_result = note_density(score, 'seconds')
    assert math.isclose(py_result, matlab_result, abs_tol=1e-9)

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

    test_score = Score.from_melody(
        pitches=pitches,
        durations=durations,
        onsets=onsets,
    )
    assert hasattr(test_score, "time_map") and hasattr(test_score, "time_signatures")
    test_score.time_map = time_map
    test_score.time_signatures = time_signatures

    # import json test results that were exported from the script
    json_results = None
    with open("tests/matlab_results_sarabande.json") as json_file:
        json_results = json.load(json_file)
    assert json_results

    # (5) notedensity
    notedensity_test_internal(test_score, json_results)
    # all tested functions and their corresponding matlab result strings
    # (in the json) are listed in pairs for easy reading
    dist_functions_test_internal(test_score, json_results)
    nnotes_test_internal(test_score, json_results)
    keymode_test_internal(score, json_results)
    kkkey_test_internal(test_score, json_results)
    segmentgestalt_test_internal(test_score, json_results)
    # (3) boundary
    boundary_test_internal(test_score, json_results)
    # TODO:
    # (1) meldistance
    # (2) melcontour
    # (4) nPVI
    # (6) entropy_pcdist1
    # (7) narmour
    # (8) tessitura
    # (9) ambitus
    # (10) complebm
    # (11) compltrans
    # (12) gradus
    # (13) melaccent
    # (14) melattraction
    # (15) mobility
    # (16) narmour

    return


test_against_matlab_results()
