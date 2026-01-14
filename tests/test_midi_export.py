"""test_midi_pmexport.py - some tests for pretty_midi_midi_export

Testing input/output with pretty_midi (PM) and music21 (M21)
The test sequence is:
1. read *.mid with PM -> myscore -> write with M21 -> *_m21exported.mid
2. read *_m21exported.mid with PM -> myscore2
   compare myscore and myscore2
3. read *.mid with M21 -> myscore3 -> write with PM -> *_pmexported.mid
4. read *_pmexported.mid with M21 -> myscore4
    compare myscore and myscore4
"""

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
        # "midi/sarabande.mid",
        "midi/tempo.mid",
        # "midi/tempochange.mid",
        # "midi/twochan.mid",
        # "midi/tones.mid",
    ],
)
def test_midi_export_and_reimport(midi_file):
    """Test that MIDI files can be exported and re-imported.

    Tested with different subsystems.
    """

    print("test_midi_export_and_reimport", midi_file)
    midi_path = example.fullpath(midi_file)
    assert (
        midi_path is not None
    ), f"Could not find example MIDI file {midi_file}"
    verbose_blank()
    m21_write_path = str(midi_path)[:-4] + "_m21exported.mid"
    pm_write_path = str(midi_path)[:-4] + "_pmexported.mid"

    #
    # test with music21 writer
    #
    set_preferred_midi_reader("pretty_midi")
    set_preferred_midi_writer("music21")

    # Read the input MIDI file
    verbose_blank()
    myscore = read_score(midi_path, show=VERBOSE)
    if VERBOSE:
        print()
        print("AMADS score returned from read_score by pretty_midi reader:")
        myscore.show()

    verbose_blank()
    print("mean orig", pitch_mean(myscore))
    print("weighted mean orig", pitch_mean(myscore, weighted=True))

    # Write the score with music21
    verbose_blank()
    print("AMADS score writing with music21 midi writer:")

    verbose_blank()
    write_score(myscore, m21_write_path, show=VERBOSE)
    verbose_blank()
    myscore2 = read_score(m21_write_path, show=VERBOSE)
    if VERBOSE:
        verbose_blank()
        print("AMADS score returned from read_score by pretty_midi:")
        myscore2.show()

    verbose_blank()
    print("mean music21", pitch_mean(myscore2))
    print("weighted mean music21", pitch_mean(myscore2, weighted=True))

    comparison_result = scores_compare(myscore, myscore2, True)
    assert comparison_result

    #
    # test with pretty_midi writer
    #
    set_preferred_midi_reader("music21")
    set_preferred_midi_writer("pretty_midi")

    # Read the input MIDI file
    verbose_blank()
    myscore3 = read_score(midi_path, show=VERBOSE)
    if VERBOSE:
        print()
        print("AMADS score returned from read_score by music21 reader:")
        myscore3.show()

    verbose_blank()
    print("mean orig", pitch_mean(myscore3))
    print("weighted mean orig", pitch_mean(myscore3, weighted=True))

    comparison_result = scores_compare(myscore, myscore3, True)
    assert comparison_result

    # Write the score with pretty_midi
    print("AMADS score writing with pretty_midi midi writer:")
    verbose_blank()
    write_score(myscore3, pm_write_path, show=VERBOSE)
    verbose_blank()
    myscore4 = read_score(pm_write_path, show=VERBOSE)
    if VERBOSE:
        verbose_blank()
        print("AMADS score returned from read_score by music21:")
        myscore4.show()
    verbose_blank()
    print("mean pretty_midi", pitch_mean(myscore4))
    print("weighted mean pretty_midi", pitch_mean(myscore4, weighted=True))
    verbose_blank()

    comparison_result = scores_compare(myscore, myscore4, True)
    assert comparison_result
