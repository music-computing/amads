import pretty_midi
import pytest

from amads.core.basics import Note, Score
from amads.io.pt_midi_import import partitura_midi_import
from amads.music import example


@pytest.mark.parametrize(
    "midi_filename",
    [
        "sarabande.mid",
        pytest.param(
            "chopin_prelude_7.mid",
            marks=pytest.mark.skip(
                reason="Known to fail, issue logged in https://github.com/music-computing/amads/issues/35"
            ),
        ),
    ],
)
def test_import_midi(midi_filename):
    """
    Test MIDI import by comparing the results with pretty_midi.

    Parameters
    ----------
    midi_filename : str
        Name of the MIDI file to test
    """
    midi_file = example.fullpath(f"midi/{midi_filename}")
    score = partitura_midi_import(midi_file, ptprint=False)
    assert isinstance(score, Score)

    score_notes = score.list_all(Note)

    pm = pretty_midi.PrettyMIDI(str(midi_file))
    pm_notes = [note for instrument in pm.instruments for note in instrument.notes]

    assert len(score_notes) == len(pm_notes)

    flattened_notes = score.get_sorted_notes()

    assert len(flattened_notes) == len(pm_notes)

    pm_notes.sort(key=lambda x: (x.start, x.pitch))

    quarter_note_duration = pm_notes[1].start / flattened_notes[1].onset

    for score_note, pm_note in zip(flattened_notes, pm_notes):
        assert score_note.num == pm_note.pitch
        assert score_note.onset == pytest.approx(pm_note.start / quarter_note_duration)
        assert score_note.duration == pytest.approx(
            pm_note.end / quarter_note_duration - pm_note.start / quarter_note_duration
        )
