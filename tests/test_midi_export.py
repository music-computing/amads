"""test_midi_pmexport.py - some tests for pretty_midi_midi_export

Testing input/output with pretty_midi (PM), music21 (M21), and mido_midi (MM)
We're going to consider PM to be the "reference" reader and use PM to read
the original MIDI file. Once we have the score as an AMADS Score, we will
test all writer/reader combinations by writing the score with one writer
and reading it back with each reader.  The results is compared to the original
score read by PM.  The table below shows the combinations of writers and
readers that are tested.

writer:   PM    M21    MM
reader:
PM         x      x     x
M21        x      x     x
"""

import math
import tempfile

import pytest

from amads.algorithms.scores_compare import scores_compare
from amads.io.readscore import read_score, set_preferred_midi_reader
from amads.io.writescore import set_preferred_midi_writer, write_score
from amads.music import example
from amads.pitch.pitch_mean import pitch_mean

VERBOSE = False  # set to True for more debug output


def verbose_blank():
    if VERBOSE:
        print()


@pytest.mark.parametrize(
    "midi_file",
    [
        "midi/short2staff.mid",
        "midi/sarabande.mid",
        "midi/tempo.mid",
        "midi/tempochange.mid",
        "midi/twochan.mid",
        "midi/tones.mid",
    ],
)
def test_midi_export_and_reimport(midi_file):
    """Test that MIDI files can be exported and re-imported.

    Tested with different subsystems.
    """

    midi_file_readers = ["pretty_midi", "music21"]
    midi_file_writers = ["pretty_midi", "music21", "mido_midi"]

    print("==== test_midi_export_and_reimport ====", midi_file)
    midi_path = example.fullpath(midi_file)
    assert (
        midi_path is not None
    ), f"Could not find example MIDI file {midi_file}"

    set_preferred_midi_reader("pretty_midi")
    ref_score = read_score(midi_path, show=VERBOSE)
    if VERBOSE:
        print()
        print(f"---- AMADS reference score from {midi_file}:")
        ref_score.show()
    verbose_blank()
    ref_pitch_mean = pitch_mean(ref_score)
    ref_weighted_pitch_mean = pitch_mean(ref_score, weighted=True)
    print("reference pitch mean", ref_pitch_mean)
    print("reference weighted pitch mean", ref_weighted_pitch_mean)

    # Create temp files for the different writers
    midi_temp_file = tempfile.NamedTemporaryFile(
        suffix="_exported.mid", delete=False
    )
    midi_write_path = midi_temp_file.name
    midi_temp_file.close()

    for writer in midi_file_writers:
        for reader in midi_file_readers:
            print(f"--- Testing with writer={writer} and reader={reader}")
            set_preferred_midi_writer(writer)
            set_preferred_midi_reader(reader)

            # Write the score with the specified writer
            verbose_blank()
            print(f"AMADS score writing with {writer} midi writer:")

            verbose_blank()
            write_score(ref_score, midi_write_path, show=VERBOSE)
            verbose_blank()

            # Read the input MIDI file
            verbose_blank()
            test_score = read_score(midi_write_path, show=VERBOSE)
            if VERBOSE:
                print()
                print(f"---- AMADS score read by {reader}:")
                test_score.show()

            verbose_blank()
            test_pitch_mean = pitch_mean(test_score)
            test_weighted_pitch_mean = pitch_mean(test_score, weighted=True)
            print("test pitch mean", test_pitch_mean)
            print("test weighted pitch mean", test_weighted_pitch_mean)
            print("ref score units are seconds", ref_score.units_are_seconds)
            print("test score units are seconds", test_score.units_are_seconds)
            assert math.isclose(test_pitch_mean, ref_pitch_mean, abs_tol=0.001)
            assert math.isclose(
                test_weighted_pitch_mean, ref_weighted_pitch_mean, abs_tol=0.001
            )
            comparison_result = scores_compare(ref_score, test_score, True)
            assert comparison_result
