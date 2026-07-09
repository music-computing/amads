import math
from amads.io.pm_midi_import import pretty_midi_import
from amads.core.basics import Note, Part, Score
from amads.melody.mobility import mobility
from amads.music import example


def test_len_edge_cases():
    # Tests the edge cases where the score does not have enough length to run
    # mobility

    # Test case 2: Empty score
    empty_score = Score()
    assert mobility(empty_score) is None

    # Test case 3: Single note
    single_note_score = Score.from_melody([60])
    assert mobility(single_note_score) is None

    # Test case 4: Two notes
    two_note_score = Score.from_melody([60, 64])
    assert mobility(two_note_score) is None


def test_simple_melody():
    # Simple melody for sanity checking
    score = Score.from_melody(pitches=[60, 64, 62, 67, 65])

    annotated_score = mobility(score)
    desired_mobilities = [
        0,
        0,
        0,
        2.4999999999999996,
        0.5833333333333333
    ]
    test_mobilities = []

    for note in annotated_score.find_all(Note):
        test_mobility_val = note.get("mobility", None)
        test_mobilities.append(test_mobility_val)

    assert all(
        math.isclose(desired, test)
        for desired, test in zip(desired_mobilities, test_mobilities)
    )
    assert len(desired_mobilities) == len(test_mobilities)


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
    assert hasattr(test_score, "time_map") and hasattr(test_score, "time_signatures")
    test_score.time_map = time_map
    test_score.time_signatures = time_signatures

    annotated_score = mobility(test_score)
    desired_mobilities = [
        0,
        0,
        0,
        2.666666666666664,
        2.989569952312868,
        1.7537141286518487,
        0.7368605193721804,
        0.5656933439530208,
        1.5240237901574767,
        0.5218209445947577,
    ]
    test_mobilities = []

    for note in annotated_score.find_all(Note):
        test_mobility_val = note.get("mobility", None)
        test_mobilities.append(test_mobility_val)
    assert all(
        math.isclose(desired, test)
        for desired, test in zip(desired_mobilities, test_mobilities)
    )
    assert len(desired_mobilities) == len(test_mobilities)


if __name__ == "__main__":
    test_len_edge_cases()
    test_simple_melody()
    test_midi_sarabande()
