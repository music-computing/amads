"""test_midi_roundtrip.py - some tests for pretty_midi_midi_export

read and write with pretty midi
read and write with music21

testing is done outside using allegroconvert
"""

import tempfile

from amads.io.readscore import read_score, set_preferred_midi_reader
from amads.io.writescore import set_preferred_midi_writer, write_score
from amads.music import example

VERBOSE = True  # set to True for more debug output


def verbose_blank():
    if VERBOSE:
        print()


def test_midi_export_and_reimport():
    """Test that MIDI files can be exported and re-imported with different subsystems.

    score -> pm_reader -> m21_writer -> pm_reader;
    score -> m21_reader -> pm_writer -> m21_reader;
    """

    midi_file = "midi/tempo.mid"
    midi_path = example.fullpath(midi_file)
    assert (
        midi_path is not None
    ), f"Could not find example MIDI file {midi_file}"
    verbose_blank()
    m21_temp_file = tempfile.NamedTemporaryFile(
        suffix="_m21exported.mid", delete=False
    )
    m21_write_path = m21_temp_file.name
    m21_temp_file.close()
    pm_temp_file = tempfile.NamedTemporaryFile(
        suffix="_pmexported.mid", delete=False
    )
    pm_write_path = pm_temp_file.name
    pm_temp_file.close()

    #
    # test with music21 writer
    #
    set_preferred_midi_reader("pretty_midi")
    set_preferred_midi_writer("pretty_midi")

    # Read the input MIDI file
    verbose_blank()
    myscore = read_score(midi_path, show=VERBOSE)
    if VERBOSE:
        print()
        print("AMADS score returned from read_score by pretty_midi reader:")
        myscore.show()

    # Write the score with music21
    verbose_blank()
    print("AMADS score writing with pretty_midi writer:")

    verbose_blank()
    write_score(myscore, pm_write_path, show=VERBOSE)

    # now do music21 round-trip

    set_preferred_midi_reader("music21")
    set_preferred_midi_writer("music21")
    verbose_blank()
    myscore2 = read_score(midi_path, show=VERBOSE)
    if VERBOSE:
        verbose_blank()
        print("AMADS score returned from read_score by pretty_midi:")
        myscore2.show()

    verbose_blank()

    # Write the score with pretty_midi
    print("AMADS score writing with music21 midi writer:")
    verbose_blank()
    write_score(myscore2, m21_write_path, show=VERBOSE)
