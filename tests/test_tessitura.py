import math

from amads.core.basics import Note, Score
from amads.io.pm_midi_import import pretty_midi_import
from amads.melody.tessitura import _RunningMedian, tessitura
from amads.music import example


def _extract_tessitura_values(
    score: Score, miditoolbox_compatible: bool = True
) -> list:
    test_tessitura = []
    if miditoolbox_compatible:
        tessitura_label = "tessitura_mtb"
    else:
        tessitura_label = "tessitura"
    for note in score.find_all(Note):
        test_tessitura_val = note.get(tessitura_label, None)
        test_tessitura.append(test_tessitura_val)
    return test_tessitura


def test_internal_median_tracker():
    median_tracker = _RunningMedian()
    median_tracker.insert_integer(1)
    assert median_tracker.obtain_current_median() == 1
    median_tracker.insert_integer(2)
    assert median_tracker.obtain_current_median() == 1.5
    median_tracker.insert_integer(5)
    assert median_tracker.obtain_current_median() == 2
    median_tracker.insert_integer(4)
    assert median_tracker.obtain_current_median() == 3.0


def test_empty_score():
    empty_score = Score()
    assert tessitura(empty_score, True) is None
    assert tessitura(empty_score, False) is None


def test_singleton_score():
    singleton_score = Score.from_melody([60])
    annotated_score = tessitura(singleton_score, True)
    assert annotated_score is not None
    test_tessitura = _extract_tessitura_values(annotated_score, True)
    assert test_tessitura == [0]
    annotated_score = tessitura(singleton_score, False)
    assert annotated_score is not None
    test_tessitura = _extract_tessitura_values(annotated_score, False)
    assert test_tessitura == [0]


def test_toy_scores():
    double_score = Score.from_melody([60, 63])
    double_score = tessitura(double_score, True)
    assert double_score is not None
    double_test = _extract_tessitura_values(double_score, True)
    desired_double = [0, 0]
    assert double_test == desired_double
    another_toy_score = Score.from_melody([60, 63, 71, 31])
    another_toy_score = tessitura(another_toy_score, True)
    assert another_toy_score is not None
    another_toy_test = _extract_tessitura_values(another_toy_score, True)
    another_toy_desired = [0, 0, 4.478342947514801, 5.627619664901272]
    assert all(
        math.isclose(desired, test)
        for desired, test in zip(another_toy_desired, another_toy_test)
    )


def test_midi_sarabande():
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

    annotated_score = tessitura(test_score, True)
    test_tessitura = _extract_tessitura_values(annotated_score, True)

    desired_tessitura = [
        0,
        0,
        1.4142135623730949,
        3.2732683535398857,
        1.1888908858518257,
        0.64216129906793562,
        1.7082997212852289,
        1.4433756729740645,
        0.78018949760549394,
        0.26620695282483414,
    ]

    assert all(
        math.isclose(desired, test)
        for desired, test in zip(desired_tessitura, test_tessitura)
    )


if __name__ == "__main__":
    test_internal_median_tracker()
    test_empty_score()
    test_singleton_score()
    test_toy_scores()
    test_midi_sarabande()
