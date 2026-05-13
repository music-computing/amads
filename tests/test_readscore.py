"""
Basic start on testing readscore.

Important business first: score from URL ;)

See more extensive tests on musicXML in test_midi_roundtrip and test_xml_export
"""

from amads.algorithms.scores_compare import notes_compare
from amads.core.basics import Measure, Note
from amads.io.readscore import (
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
    score = read_score(kern_file)
    # print("Partitura Kern import:")
    # score.show()
    nnotes = score.list_all(Note)
    assert len(nnotes) == 25, f"Expected 25 notes, got {len(nnotes)}"
    dur = score.duration
    assert dur == 27.0, f"Expected duration 27.0, got {dur}"
    nmeasures = score.list_all(Measure)
    assert len(nmeasures) == 9, f"Expected 9 measures, got {len(nmeasures)}"


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
    score = read_score(xml_file, show=True)
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
