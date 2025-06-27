import pretty_midi
import pytest

from amads.core.basics import Score
from amads.io.readscore import import_midi
from amads.music import example


@pytest.mark.parametrize(
    "midi_filename",
    [
        "tempochange.mid",
        "sarabande.mid",
        #        pytest.param(
        "chopin_prelude_7.mid",
        #            marks=pytest.mark.skip(
        #                reason="Known to fail, issue logged in https://github.com/music-computing/amads/issues/35"
        #            ),
        #        ),
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
    score = import_midi(midi_file, show=True)
    assert isinstance(score, Score)
    # score.quantize(12)
    # score = score.merge_tied_notes()  # so we can count notes from MIDI correctly
    # score_notes = score.list_all(Note)

    # print("AMADS notes:")
    # for note in score_notes:
    #     print(f"{note.onset / 4:0.2f} {note.key_num} {note.duration:0.2f}")

    # score.show()

    pm = pretty_midi.PrettyMIDI(str(midi_file))
    print(f"PrettyMIDI resolution: {pm.resolution}")
    pm_notes = [note for instrument in pm.instruments for note in instrument.notes]

    #    score.show()
    flattened_notes = score.get_sorted_notes()

    assert len(flattened_notes) == len(pm_notes)

    #    print("PrettyMIDI notes before sort:")
    #    for note in pm_notes:
    #        print(f"{note.start:0.2f} {note.pitch} {note.end - note.start:0.2f}")

    pm_notes.sort(key=lambda x: (x.start, x.pitch))

    #    print("PrettyMIDI notes after sort:")
    #    for note in pm_notes:
    #        print(f"{note.start:0.2f} {note.pitch} {note.end - note.start:0.2f}")

    # pretty_midi notes use seconds, not beats, so convert AMADS score
    # to seconds:
    score.convert_to_seconds()  # modifies in place
    #    print("AMADS score in seconds:")
    #    score.show()
    notes = score.get_sorted_notes()

    for score_note, pm_note in zip(notes, pm_notes):
        assert score_note.key_num == pm_note.pitch
        # using 1 ms tolerance here, 1e-6 relative tolerance is too strict
        # but I don't what different packages are doing to be this far apart
        if score_note.onset != pytest.approx(
            pm_note.start, abs=1e-3
        ) or score_note.duration != pytest.approx(
            pm_note.end - pm_note.start, abs=1e-3
        ):
            print("NOTE MISMATCH IN TEST")
            print(
                f"AMADS note: onset {score_note.onset} pitch {score_note.key_num} "
                f"duration {score_note.duration}"
            )
            print(
                f"PM note: onset {pm_note.start} pitch {pm_note.pitch} "
                f"duration {pm_note.end - pm_note.start}"
            )
        assert score_note.onset == pytest.approx(pm_note.start, abs=1e-3)
        # chopin_prelude_7.mid is not well-formed because it has two note-ons
        # without an intervening note-off on pitch 62. Different readers
        # interpret this differently.
        assert score_note.duration == pytest.approx(
            pm_note.end - pm_note.start, abs=1e-3
        )
