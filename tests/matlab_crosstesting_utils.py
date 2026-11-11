"""
Primitive facilities that replicate the inputs (and quirks) that are used in the
matlab testing harness (for which the json file results were derived from).
"""

import json

from amads.core.basics import Score
from amads.io.pm_midi_import import pretty_midi_import
from amads.music import example


def _sarabande_matlab_test_score() -> Score:
    """
    Returns the sarabande

    Returns
    -------
    Score
        Score containing the same data as the one used in the matlab
        testing harness.
    """
    # this test tests first 10 notes imported from sarabande.midi
    score = pretty_midi_import(
        example.fullpath("midi/sarabande.mid"), "midi", flatten=True
    )
    test_score = score.slice(0, 6.5, "quarters")
    test_score.convert_to_seconds()

    return test_score


def load_json_results() -> dict:
    json_results = None
    with open("tests/matlab_results_sarabande.json") as json_file:
        json_results = json.load(json_file)
    return json_results


matlab_sarabande_test_score = _sarabande_matlab_test_score()
