import math

from amads.core.basics import Note, Score
from amads.io.pm_midi_import import pretty_midi_import
from amads.melody.gradus import gradus
from amads.music import example


def test_edge_cases():
    # Empty score
    empty_score = Score()
    assert gradus(empty_score) is None

    # Single note
    single_note_score = Score.from_melody([60])
    assert gradus(single_note_score) is None


def test_toy_scores():
    # C major triad (C-E-G)
    score = Score.from_melody([60, 64, 67])
    assert gradus(score) == 7.5

    # Chromatic sequence
    chromatic_score = Score.from_melody([60, 61, 62, 63, 64])
    assert gradus(chromatic_score) == 11.0


def test_gradus_sarabande():
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
    assert math.isclose(gradus(test_score), 8.777777777777779)


if __name__ == "__main__":
    test_edge_cases()
    test_toy_scores()
    test_gradus_sarabande()
