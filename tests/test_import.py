from typing import List

import pretty_midi
import pytest

from amads.core.basics import Note, Score
from amads.io.readscore import (
    last_used_reader,
    read_score,
    set_preferred_midi_reader,
)
from amads.music import example

VERBOSE = False  # set to True for more debug output


def basic_note_compare(
    score_notes: List[Note], pm_notes: List[pretty_midi.Note]
):
    """Compare a list of AMADS Notes with a list of pretty_midi Notes."""
    for i in range(min(len(score_notes), len(pm_notes))):
        score_note = score_notes[i]
        pm_note = pm_notes[i]
        if VERBOSE:
            print(
                f"Comparing note {i}: AMADS onset {score_note.onset} "
                f"pitch {score_note.key_num} duration {score_note.duration} | "
                f"PM onset {pm_note.start} pitch {pm_note.pitch} "
                f"duration {pm_note.end - pm_note.start}"
            )
        if (
            score_note.onset != pytest.approx(pm_note.start, abs=1e-3)
            or score_note.duration
            != pytest.approx(pm_note.end - pm_note.start, abs=1e-3)
            or score_note.key_num != pm_note.pitch
        ):
            print(f"NOTE MISMATCH IN TEST at index {i}")
            print(
                f"AMADS note: onset {score_note.onset} pitch {score_note.key_num} "
                f"duration {score_note.duration}"
            )
            print(
                f"PM note: onset {pm_note.start} pitch {pm_note.pitch} "
                f"duration {pm_note.end - pm_note.start}"
            )
            # now add assertions so debug output will tell us what failed
            assert score_note.onset == pytest.approx(
                pm_note.start, abs=1e-3
            ), f"Onset mismatch at note {i}"

            # duration testing is pretty lax because with partitura, we try to avoid
            # ties to very short notes, and that can change the duration by more than
            # just rounding error.
            assert score_note.duration == pytest.approx(
                pm_note.end - pm_note.start, abs=1e-3
            ), f"Duration mismatch at note {i}"
            assert (
                score_note.key_num == pm_note.pitch
            ), f"Pitch mismatch at note {i}"
    assert len(score_notes) == len(pm_notes), (
        f"Number of notes mismatch: AMADS has {len(score_notes)} notes, "
        f"pretty_midi has {len(pm_notes)} notes."
    )


@pytest.mark.parametrize(
    "midi_filename",
    [
        "tempochange.mid",
        "sarabande.mid",
        # "chopin_prelude_7.mid",  # chopin_prelude_7.mid has overlapping notes on same pitch
        # partitura treats this differently than music21 and pretty_midi
        "twochan.mid",
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
    assert midi_file is not None
    set_preferred_midi_reader(reader="pretty_midi")
    pmscore = read_score(midi_file, show=VERBOSE)
    assert isinstance(pmscore, Score)
    pmscore = pmscore.flatten(collapse=True)
    print(
        f"Imported MIDI file {midi_filename} into AMADS Score "
        f"using {last_used_reader()}."
    )
    # pmscore.quantize(12)
    # pmscore = pmscore.merge_tied_notes()  # so we can count notes from MIDI correctly
    # score_notes = pmscore.list_all(Note)

    # print("AMADS notes:")
    # for note in score_notes:
    #     print(f"{note.onset / 4:0.2f} {note.key_num} {note.duration:0.2f}")

    pmscore.convert_to_seconds()
    if VERBOSE:
        print("PrettyMIDI imported score converted to SECONDS:")
        pmscore.show()
    pmscore_notes = pmscore.get_sorted_notes()
    for note in pmscore_notes:
        assert note.dynamic != 0, "Note has zero dynamic after import."

    pm = pretty_midi.PrettyMIDI(str(midi_file))
    print(f"PrettyMIDI resolution: {pm.resolution}")
    pm_notes = [
        note for instrument in pm.instruments for note in instrument.notes
    ]

    # print("PrettyMIDI notes before sort:")
    # for note in pm_notes:
    #     print(f"{note.start:0.2f} {note.pitch} {note.end - note.start:0.2f}")

    pm_notes.sort(key=lambda x: (x.start, x.pitch))
    #    print("PrettyMIDI notes after sort:")
    #    for note in pm_notes:
    #        print(f"{note.start:0.2f} {note.pitch} {note.end - note.start:0.2f}")

    basic_note_compare(pmscore_notes, pm_notes)

    set_preferred_midi_reader(reader="music21")
    m2score = read_score(midi_file, show=VERBOSE)
    m2score.convert_to_seconds()
    assert isinstance(m2score, Score)
    print(
        f"Imported MIDI file {midi_filename} into AMADS Score "
        f"using {last_used_reader()}."
    )
    basic_note_compare(m2score.get_sorted_notes(), pm_notes)

    set_preferred_midi_reader(reader="partitura")
    pscore = read_score(midi_file, show=VERBOSE)
    pscore.convert_to_seconds()
    assert isinstance(pscore, Score)
    print(
        f"Imported MIDI file {midi_filename} into AMADS Score "
        f"using {last_used_reader()}."
    )
    basic_note_compare(pscore.get_sorted_notes(), pm_notes)
