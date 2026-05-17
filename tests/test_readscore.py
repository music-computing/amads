"""
Basic start on testing readscore.

Important business first: score from URL ;)

See more extensive tests on musicXML in test_midi_roundtrip and test_xml_export
"""

from amads.algorithms.scores_compare import notes_compare, scores_compare
from amads.core.basics import Measure, Note
from amads.io.readscore import (
    last_used_reader,
    read_score,
    set_preferred_kern_reader,
    set_preferred_xml_reader,
    set_reader_warning_level,
)
from amads.music import example


def test_pitch_comparison():
    set_reader_warning_level("none")
    test_path = (
        "https://github.com/MarkGotham/species/raw/refs/heads/main/1x1/005.mxl"
    )
    score = read_score(test_path)
    notes = score.get_sorted_notes()
    assert len(notes) == 22


def test_read_kern():
    """Test reading a Kern file and displaying it as text."""
    set_reader_warning_level("none")
    set_preferred_kern_reader("music21")
    kern_file = example.fullpath("krn/happy_birthday_reference.krn")
    assert kern_file is not None
    score = read_score(kern_file)
    # print("Music21 Kern import:")
    # score.show()
    nnotes = score.list_all(Note)
    assert len(nnotes) == 25, f"Expected 25 notes, got {len(nnotes)}"
    # Note: The first measure is padded with rests to give a complete measure,
    #   which is consistent with other AMADS readers and especially helps with
    #   MIDI files which cannot represent partial measures. The last measure is
    #   not complete or padded with a rest, so the duration is 23.0, not 24.0
    #   as one might expect from the time signature. This behavior may change
    #   in the future, but for now we test for the current behavior.
    dur = score.duration
    assert dur == 27.0, f"Expected duration 27.0, got {dur}"
    nmeasures = score.list_all(Measure)
    assert len(nmeasures) == 9, f"Expected 9 measures, got {len(nmeasures)}"

    set_preferred_kern_reader("partitura")
    ptscore = read_score(kern_file)
    print("Partitura Kern import:")
    # ptscore.show()
    nnotes = ptscore.list_all(Note)
    assert len(nnotes) == 25, f"Expected 25 notes, got {len(nnotes)}"
    dur = ptscore.duration
    assert dur == 27.0, f"Expected duration 27.0, got {dur}"
    nmeasures = ptscore.list_all(Measure)
    assert len(nmeasures) == 9, f"Expected 9 measures, got {len(nmeasures)}"

    assert scores_compare(score, ptscore), "Expected scores to match."


def test_read_musicxml():
    """Test reading bwv846m15-16.musicxml.
    This file has a tie that was not read properly by Partitura, although
    the claim is the bug is fixed in a recent pull request. This test reads
    the test file with Music21, and later, when Partitura is updated, we
    can test Partitura on this file as well.
    """
    set_reader_warning_level("none")
    xml_file = example.fullpath("musicxml/bwv846m15-16.musicxml")
    assert xml_file is not None
    score = read_score(xml_file)  # , show=True)
    # print("MusicXML import:")
    # score.show()
    nnotes = score.list_all(Note)
    assert len(nnotes) == 60, f"Expected 60 notes, got {len(nnotes)}"
    dur = score.duration
    assert dur == 8.0, f"Expected duration 8.0, got {dur}"
    nmeasures = score.list_all(Measure)
    # The length is 2 measures, but there are 2 staves, so 4 measures in total.
    assert len(nmeasures) == 4, f"Expected 4 measures, got {len(nmeasures)}"
    set_preferred_xml_reader("partitura")
    score2 = read_score(xml_file)
    result = notes_compare(
        score, "from_music21", score2, "from_partitura", spelling=True
    )
    # print("Score from Music21:")
    # score.show()
    # print("Score from Partitura:")
    # score2.show()

    # Partitura 1.8.0 will fail this test because of a bug in reading ties,
    # but the bug is fixed in a recent pull request. Once Partitura is updated,
    # result[0] should be True and we can uncomment the following assertion.
    # assert result[0], "Expected scores to match."
    print(result[0])  # only printing here to make flake8 happy by using result


def test_time_tempo_example():
    """Test reading a file with time and tempo changes."""
    set_preferred_xml_reader("music21")
    set_reader_warning_level("none")
    xml_file = example.fullpath("musicxml/time-tempo-test.musicxml")
    assert xml_file is not None
    score = read_score(xml_file)  # , show=True)
    # print("MusicXML import with", last_used_reader())
    # score.show()
    assert score.time_map is not None, "Expected time map to be present"
    assert (
        len(score.time_map.changes) == 2
    ), f"Expected 2 tempo changes, got {len(score.time_map.changes)}"
    assert (
        score._find_time_signature(0).upper == 4
    ), "Expected time signature upper to be 4"
    assert (
        score._find_time_signature(0).lower == 4
    ), "Expected time signature lower to be 4"
    assert (
        score._find_time_signature(4).upper == 3
    ), "Expected time signature upper to be 3"
    assert (
        score._find_time_signature(4).lower == 4
    ), "Expected time signature lower to be 4"
    assert (
        score.time_map.quarter_to_tempo(0) == 100.0
    ), "Expected tempo at quarter 0 to be 100.0"
    assert (
        score.time_map.quarter_to_tempo(2) == 100.0
    ), "Expected tempo at quarter 2 to be 100.0"
    assert (
        score.time_map.quarter_to_tempo(4) == 80.0
    ), "Expected tempo at quarter 4 to be 80.0"
    assert len(score.list_all(Note)) == 16, "Expected 16 notes in score"

    set_preferred_xml_reader("partitura")
    ptscore = read_score(xml_file)  # , show=True)
    print("MusicXML import with", last_used_reader())
    ptscore.show()
    assert scores_compare(score, ptscore), "Expected scores to match"
