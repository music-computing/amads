"""
Primitive facilities that replicate the inputs (and quirks) that are used in the
matlab testing harness (for which the json file results were derived from).
"""

import json

from amads.core.basics import Note, Score
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
    assert hasattr(test_score, "time_map") and hasattr(
        test_score, "time_signatures"
    )
    test_score.time_map = time_map
    test_score.time_signatures = time_signatures

    return test_score


def load_json_results() -> dict:
    json_results = None
    with open("tests/matlab_results_sarabande.json") as json_file:
        json_results = json.load(json_file)
    return json_results


matlab_sarabande_test_score = _sarabande_matlab_test_score()
