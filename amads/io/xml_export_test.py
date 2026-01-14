# test_xml_export.py - some tests for pretty_midi_midi_export

from amads.algorithms.scores_compare import scores_compare
from amads.io.readscore import read_score, set_preferred_xml_reader
from amads.io.writescore import set_preferred_xml_writer, write_score
from amads.music import example
from amads.pitch.pitch_mean import pitch_mean

VERBOSE = True  # set to True for more debug output


def verbose_blank():
    if VERBOSE:
        print()


def xml_export_and_reimport(xml_file):
    """Test that XML files can be exported and re-imported.

    Uses different subsystems.
    """
    my_xml_file = example.fullpath(xml_file)
    assert (
        my_xml_file is not None
    ), f"Could not find example XML file {xml_file}"
    verbose_blank()

    set_preferred_xml_reader("partitura")
    set_preferred_xml_writer("music21")

    # Read the input XML file
    myscore = read_score(my_xml_file, show=VERBOSE)
    if VERBOSE:
        print()
        print("AMADS score returned from read_score by partitura reader:")
        myscore.show()

    verbose_blank()
    print("mean orig", pitch_mean(myscore))
    print("weighted mean orig", pitch_mean(myscore, weighted=True))

    # Write the score with music21
    verbose_blank()
    exported_file = str(my_xml_file)[:-4] + "_m21exported.xml"
    write_score(myscore, exported_file, show=VERBOSE)
    verbose_blank()
    myscore2 = read_score(exported_file, show=VERBOSE)
    if VERBOSE:
        verbose_blank()
        print("AMADS score returned from read_score by partitura:")
        myscore2.show()

    verbose_blank()
    comparison_result = scores_compare(myscore, myscore2)
    assert comparison_result

    set_preferred_xml_reader("music21")
    set_preferred_xml_writer("partitura")
    # Test with partitura
    exported_file = str(my_xml_file)[:-4] + "_ptexported.xml"
    write_score(myscore, exported_file, show=VERBOSE)
    verbose_blank()
    myscore3 = read_score(exported_file, show=VERBOSE)
    if VERBOSE:
        verbose_blank()
        print("AMADS score returned from read_score by music21:")
        myscore3.show()

    verbose_blank()
    comparison_result = scores_compare(myscore, myscore3)
    assert comparison_result


xml_export_and_reimport("musicxml/ex1.xml")
