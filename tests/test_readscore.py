"""
Basic start on testing readscore.

Important business first: score from URL ;)

See more extensive tests on musicXML in test_midi_roundtrip and test_xml_export
"""

from amads.core.basics import Measure, Note
from amads.io.readscore import (
    read_score,
    set_preferred_kern_reader,
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
