"""
Test file for comparing snapshotted outputs from a selection of miditoolbox
implemented functions and their corresponding versions in amads.

Functions implemented:
notedensity
nnotes
keymode
kkkey
segment_gestalt
boundary
nPVI

Functions that have not been implemented or are implemented in a different form:
meldistance (unimplemented)
melcontour (there are 4 classes defined for various melodic distance paradigms)
entropy_pcdist1 (unimplemented)
tessitura (unimplemented)
ambitus (unimplemented)
complebm (unimplemented)
compltrans (unimplemented)
gradus (unimplemented)
melaccent (unimplemented)
melattraction (unimplemented)
mobility (unimplemented)
narmour (unimplemented)
"""

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
from amads.time.variability import normalized_pairwise_variability_index

from typing import Dict

from dataclasses import dataclass
from amads.pitch.key.profiles import KeyProfile, PitchProfile


@dataclass
class TestProfile(KeyProfile):
    name: str = "Test Profile (used in MidiToolbox under the name kkprofs)"
    literature: str = "kkprofs profile values in MidiToolbox1.1"
    about: str = (
        "This test profile corresponds to the kkprofs profile in "
        "miditoolbox1.1. It is included separately from Krumhansl Kessler "
        "because it is slightly inconsistent from a normalized "
        "krumhansl-kessler profile, which was its original intention"
    )
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
    """
    list pairs of correspondences between the distribution functions
    and their matlab couterparts.
    This part is generalized because the outputs of all distribution functions
    for matlab implementation follow the same structure. Likewise, the same
    applies for all amads distribution functions as well.
    """
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
    """
    nnotes has the same output structure as nnotes in miditoolbox
    """
    assert nnotes(score, True) == json_results["nnotes"]


def keymode_test_internal(score: Score, json_results: Dict):
    """
    By default, the attribute names of ["major", "minor"] was passed into
    keymode in python.
    Compared to the miditoolbox implementation, the only difference is the
    ambiguous case, where the miditoolbox version simply returns "major"
    while the amads implementation returns ["major", "minor"] to highlight
    the ambiguity.
    """
    # converts integer results from matlab keymode into python results
    keymode_interpretation = [["major", "minor"], ["major"], ["minor"]]
    assert (
        keymode(score, profile=testprofile)
        == keymode_interpretation[json_results["keymode"]]
    )


def kkkey_test_internal(score: Score, json_results: Dict):
    """ """
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
    Simple internal function that extracts the onsets (in quarters) from
    a score annotated by segment_gestalt.
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
    """
    The matlab function returns a result that concatenates the clang
    onsets (as a vector of booleans on note onsets in the miditoolbox score
    matrix) and gestalt segment onsets (as a vector of booleans on notes in the
    miditoolbox score matrix).
    The amads version returns an annotated monophonic score annotating the
    boundaries on each note with has_clang_onset and has_segment_onset booleans.

    To compare these two results, we process the matlab result by finding
    the indices in the original boolean matrices. We also extract those indices
    from the gestalt marks, and concatenate them as well before comparing
    both results.
    """
    matlab_result = json_results["segmentgestalt"]
    py_matlab_result = list(np.nonzero(matlab_result)[0])
    score = segment_gestalt(score)
    clang_indices, seg_indices = _extract_gestalt_marks(score)
    score_len = nnotes(score)
    py_result = clang_indices + [idx + score_len for idx in seg_indices]

    assert py_result == py_matlab_result


def _extract_boundary_marks(score):
    """
    Extracts the annotated information from the monophonic score and
    concatenates them into a list.
    """
    boundary_strengths = []
    for note in score.find_all(Note):
        boundary_strength = note.get("boundary_strength", None)
        boundary_strengths.append(boundary_strength)
    return boundary_strengths


def boundary_test_internal(score: Score, json_results: Dict):
    """
    The matlab implementation returns a list of strengths that coincide (by row
    indices) to the notes in the note matrix.
    The python implementation annotates the supplied monophonic score argument
    instead.
    To compare the two results, we extract the annotated information from
    the score into a list, then compare said list to the values in the
    matlab implementation.
    """
    matlab_result = json_results["boundary"]
    score = boundary(score)
    py_result = _extract_boundary_marks(score)

    assert all(
        math.isclose(py_data, mlb_result, abs_tol=1e-9)
        for py_data, mlb_result in zip(py_result, matlab_result)
    )


def notedensity_test_internal(score: Score, json_results: Dict):
    """
    note density is represented as a float in both the amads implementation
    and the miditoolbox implementation.

    One thing of note is that the matlab implementation defaults to the
    "beats" argument in the implementation, but still uses the "seconds"
    argument instead.
    """
    matlab_result = json_results["notedensity"]
    assert score.units_are_quarters
    py_result = note_density(score, "seconds")
    assert math.isclose(py_result, matlab_result, abs_tol=1e-9)


def npvi_test_internal(score: Score, json_results: Dict):
    """
    Both matlab and amads implementations output a float
    """
    matlab_result = json_results["nPVI"]
    py_result = normalized_pairwise_variability_index(score)
    assert math.isclose(py_result, matlab_result, abs_tol=1e-9)


def test_against_matlab_results():
    """
    Function where the test inputs are setup, and all the internal test
    functions are run.
    """
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

    notedensity_test_internal(test_score, json_results)
    dist_functions_test_internal(test_score, json_results)
    nnotes_test_internal(test_score, json_results)
    keymode_test_internal(score, json_results)
    kkkey_test_internal(test_score, json_results)
    segmentgestalt_test_internal(test_score, json_results)
    boundary_test_internal(test_score, json_results)
    npvi_test_internal(test_score, json_results)

    return