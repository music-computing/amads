# test_xml_export.py - some tests for pretty_midi_midi_export

import pytest

from amads.algorithms.scores_compare import scores_compare
from amads.io.readscore import read_score, set_preferred_xml_reader
from amads.io.writescore import set_preferred_xml_writer, write_score
from amads.music import example
from amads.pitch.pitch_mean import pitch_mean

VERBOSE = True  # set to True for more debug output


@pytest.mark.parametrize(
    "xml_file",
    [
        "musicxml/ex1.xml",
        "musicxml/ex2.xml",
        "musicxml/ex3.xml",
    ],
)
def test_xml_export_and_reimport(xml_file):
    """Test that XML files can be exported and re-imported with different subsystems."""
    my_xml_file = example.fullpath(xml_file)
    assert (
        my_xml_file is not None
    ), f"Could not find example XML file {xml_file}"

    # Read the input XML file
    myscore = read_score(my_xml_file, show=VERBOSE)
    if VERBOSE:
        myscore.show()

    pitch_mean(myscore)
    pitch_mean(myscore, weighted=True)

    # Test with music21
    exported_file = str(my_xml_file)[:-4] + "_m21exported.xml"
    set_preferred_xml_writer("music21")
    write_score(myscore, exported_file, show=VERBOSE)
    set_preferred_xml_reader("partitura")  # to vary the readers used
    myscore2 = read_score(exported_file, show=VERBOSE)
    if VERBOSE:
        myscore2.show()

    comparison_result = scores_compare(myscore, myscore2)
    assert comparison_result

    # Test with partitura
    exported_file = str(my_xml_file)[:-16] + "_ptexported.xml"
    set_preferred_xml_writer("partitura")
    write_score(myscore, exported_file, show=VERBOSE)
    set_preferred_xml_reader("music21")  # to vary the readers used
    myscore3 = read_score(exported_file, show=VERBOSE)
    if VERBOSE:
        myscore3.show()

    comparison_result = scores_compare(myscore, myscore3)
    assert comparison_result
