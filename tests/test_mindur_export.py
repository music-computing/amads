import math
from pathlib import Path
from typing import cast

from amads.algorithms.mindur import impose_mindur
from amads.algorithms.scores_compare import scores_compare
from amads.core.basics import Measure, Note, Part, Score, Staff
from amads.io.readscore import read_score, set_preferred_midi_reader
from amads.io.writescore import set_preferred_midi_writer, write_score

VERBOSE = False


def _check_imported_score(
    imported: Score, dur1: float, start2: float, dur2: float
) -> None:
    """Check for correct score after MIDI import"""
    notes = cast(list[Note], imported.list_all(Note))

    assert len(notes) == 2
    assert notes[0].pitch.get_name_with_octave() == "B4"  # type: ignore
    assert notes[1].pitch.get_name_with_octave() == "C5"  # type: ignore

    # m21 midi export imposes a minimum duration of 0.001 beat on MIDI notes
    # to avoid an out-of-order note-off-before-note-on problem:
    assert math.isclose(notes[0].onset, 0.0, abs_tol=1e-3)
    assert math.isclose(notes[0].duration, dur1, abs_tol=2e-3)

    assert math.isclose(notes[1].onset, start2, abs_tol=1e-3)
    assert math.isclose(notes[1].duration, dur2, abs_tol=1e-3)


def test_mindur(tmp_path: Path):
    """Grace-note and short note exporting to MIDI."""
    measure = Measure(onset=0.0, duration=4.0)
    grace_note = Note(parent=measure, onset=0.0, duration=0.0, pitch="B4")
    grace_note.set("is_grace", True)
    Note(parent=measure, onset=0.0, duration=4.0, pitch="C5")
    score = Score(Part(Staff(measure)))

    previous_writer = set_preferred_midi_writer("music21")
    previous_reader = set_preferred_midi_reader("mido")
    midi_path_1 = tmp_path / "with_grace_1.mid"
    write_score(score, midi_path_1, show=VERBOSE)
    imported = read_score(midi_path_1, flatten=True)
    _check_imported_score(imported, 0.0, 0.0, 4.0)

    # now, let's "open up" the grace note with impose_mindur to make
    # MIDI more visible and audible:

    score_mindur = impose_mindur(score, 0.1)
    midi_path_1b = tmp_path / "with_grace_1b.mid"
    write_score(score_mindur, midi_path_1b, show=VERBOSE)
    imported = read_score(midi_path_1b, flatten=True)
    _check_imported_score(imported, 0.1, 0.1, 3.9)

    # Repeat with "mido", "pretty_midi"
    set_preferred_midi_writer("mido")
    set_preferred_midi_reader("pretty_midi")
    midi_path_2 = tmp_path / "with_grace_2.mid"
    write_score(score, midi_path_2, show=VERBOSE)
    imported = read_score(midi_path_2, flatten=True, show=VERBOSE)
    _check_imported_score(imported, 0.0, 0.0, 4.0)

    midi_path_2b = tmp_path / "with_grace_2b.mid"
    write_score(score_mindur, midi_path_2b, show=VERBOSE)
    imported = read_score(midi_path_2b, flatten=True)
    _check_imported_score(imported, 0.1, 0.1, 3.9)

    # Repeat with "pretty_midi", "music21"
    set_preferred_midi_writer("pretty_midi")
    set_preferred_midi_reader("music21")
    midi_path_3 = tmp_path / "with_grace_3.mid"
    write_score(score, midi_path_3, show=VERBOSE)
    imported = read_score(midi_path_3, flatten=True, show=VERBOSE)
    _check_imported_score(imported, 0.0, 0.0, 4.0)

    midi_path_3b = tmp_path / "with_grace_3b.mid"
    write_score(score_mindur, midi_path_3b, show=VERBOSE)
    imported = read_score(midi_path_3b, flatten=True, show=VERBOSE)
    _check_imported_score(imported, 0.1, 0.1, 3.9)

    set_preferred_midi_writer(previous_writer)
    set_preferred_midi_reader(previous_reader)


def test_mindur_seq():
    """test for impose_mindur() with a sequence of notes that
    get shifted
    """
    D = 0.001
    score = Score.from_melody(
        pitches=[64, 65, 67, 69, 71, 72, 67],
        durations=[D, D, D, D, D, D, 2.0 - 6 * D],
    )
    E = 0.125
    correct = Score.from_melody(
        pitches=[64, 65, 67, 69, 71, 72, 67],
        durations=[E, E, E, E, E, E, 2.0 - 6 * E],
    )
    score_mindur = impose_mindur(score, 0.125)
    assert len(score_mindur.list_all(Note)) == 7
    print("---------- correct --------------")
    correct.show()
    print("---------- score_mindur -------------")
    score_mindur.show()
    assert scores_compare(score_mindur, correct, True)
