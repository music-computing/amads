# pmexport.py - some tests for pretty_midi_midi_export

import pytest

from amads.algorithms.scores_compare import scores_compare
from amads.io.readscore import read_score, set_preferred_midi_reader
from amads.io.writescore import set_preferred_midi_writer, write_score
from amads.music import example
from amads.pitch.pitch_mean import pitch_mean

VERBOSE = True  # set to True for more debug output


@pytest.mark.parametrize(
    "midi_file",
    [
        # "midi/sarabande.mid",
        # "midi/tempo.mid",
        # "midi/tempochange.mid",
        "midi/twochan.mid",
        # "midi/tones.mid",
    ],
)
def test_midi_export_and_reimport(midi_file):
    """Test that MIDI files can be exported and re-imported with different subsystems."""
    my_midi_file = example.fullpath(midi_file)
    assert (
        my_midi_file is not None
    ), f"Could not find example MIDI file {midi_file}"

    # Read the input MIDI file
    myscore = read_score(my_midi_file, show=VERBOSE)
    if VERBOSE:
        print("AMADS score returned from read_score by default reader:")
        myscore.show()

    print("mean orig", pitch_mean(myscore))
    print("weighted mean orig", pitch_mean(myscore, weighted=True))

    # Test with pretty_midi
    set_preferred_midi_writer("pretty_midi")
    exported_file = str(my_midi_file)[:-4] + "_pmexported.mid"
    print("exporting", exported_file)
    write_score(myscore, exported_file, show=VERBOSE)
    set_preferred_midi_reader("music21")
    myscore2 = read_score(exported_file, show=VERBOSE)
    if VERBOSE:
        print("AMADS score returned from read_score by music21:")
        myscore2.show()

    print("mean pretty_midi", pitch_mean(myscore2))
    print("weighted mean pretty_midi", pitch_mean(myscore2, weighted=True))

    comparison_result = scores_compare(myscore, myscore2, True)
    assert comparison_result

    # Test with music21
    set_preferred_midi_writer("music21")
    print("exported_file", exported_file, "truncated", exported_file[:-15])
    exported_file = str(exported_file)[:-15] + "_m21exported.mid"
    print("exporting", exported_file)
    write_score(myscore, exported_file, show=VERBOSE)
    set_preferred_midi_reader("partitura")
    myscore3 = read_score(exported_file, show=VERBOSE)
    if VERBOSE:
        print("AMADS score returned from read_score by partitura:")
        myscore3.show()

    print("mean music21", pitch_mean(myscore3))
    print("weighted mean music21", pitch_mean(myscore3, weighted=True))

    comparison_result = scores_compare(myscore, myscore3, True)
    assert comparison_result

    # Test with partitura
    set_preferred_midi_writer("partitura")
    exported_file = str(exported_file)[:-16] + "_ptexported.mid"
    print("exporting", exported_file)
    write_score(myscore, exported_file, show=VERBOSE)
    set_preferred_midi_reader("pretty_midi")
    myscore4 = read_score(exported_file, show=VERBOSE)
    if VERBOSE:
        print("AMADS score returned from read_score by pretty_midi:")
        myscore4.show()

    print("mean partitura", pitch_mean(myscore2))
    print("weighted mean partitura", pitch_mean(myscore2, weighted=True))

    comparison_result = scores_compare(myscore, myscore4, True)
    assert comparison_result
