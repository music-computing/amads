"""
Basic start on testing readscore.

Important business first: score from URL ;)

See more extensive tests on musicXML in test_midi_roundtrip and test_xml_export
"""

from amads.algorithms.scores_compare import notes_compare, scores_compare
from amads.core.basics import Measure, Note, Staff
from amads.io.readscore import (
    last_used_reader,
    read_score,
    set_preferred_kern_reader,
    set_preferred_xml_reader,
    set_reader_warning_level,
)
from amads.music import example

VERBOSE = False


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
    print("READING KERN FILE", kern_file)
    score = read_score(kern_file, show=VERBOSE)
    print("Music21 Kern import:")
    score.show()
    nnotes = score.list_all(Note)
    assert len(nnotes) == 25, f"Expected 25 notes, got {len(nnotes)}"
    # Note that first and last measure are shorter than time signature duration:
    dur = score.duration
    assert dur == 23.0, f"Expected duration 23.0, got {dur}"
    nmeasures = score.list_all(Measure)
    assert len(nmeasures) == 9, f"Expected 9 measures, got {len(nmeasures)}"

    set_preferred_kern_reader("partitura")
    ptscore = read_score(kern_file, show=VERBOSE)
    print("Partitura Kern import:")
    ptscore.show()
    nnotes = ptscore.list_all(Note)
    assert len(nnotes) == 25, f"Expected 25 notes, got {len(nnotes)}"
    dur = ptscore.duration
    assert dur == 23.0, f"Expected duration 23.0, got {dur}"
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
    score = read_score(xml_file)  # , show=VERBOSE)
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
    xml_file = example.fullpath("musicxml/time_tempo_test.musicxml")
    assert xml_file is not None
    score = read_score(xml_file, show=VERBOSE)
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
    ptscore = read_score(xml_file)  # , show=VERBOSE)
    print("MusicXML import with", last_used_reader())
    ptscore.show()
    assert scores_compare(score, ptscore), "Expected scores to match"


def test_grace_trills_example():
    """Test reading a file with grace notes and trills."""
    set_preferred_xml_reader("music21")
    set_reader_warning_level("none")
    xml_file = example.fullpath("musicxml/trills.musicxml")
    assert xml_file is not None
    score = read_score(xml_file)  # , show=VERBOSE)
    print("MusicXML import with", last_used_reader())
    score.show()
    assert len(score.list_all(Note)) == 30, "Expected 30 notes in score"
    staffs: list[Staff] = score.list_all(Staff)  # type: ignore
    assert len(staffs) == 2, "Expected 2 staffs in score"
    notes = staffs[0].list_all(Note)
    assert notes[0].get("has_trill", False)
    assert notes[0].get("trill_pitch").name_with_octave == "B4"
    assert notes[2].get("has_turn", False)
    assert notes[2].get("turn_pitches")[0].name_with_octave == "Db5"
    assert notes[2].get("turn_pitches")[1].name_with_octave == "B4"
    assert notes[3].get("has_turn", False)
    assert notes[3].get("turn_pitches")[0].name_with_octave == "C##5"
    assert notes[3].get("turn_pitches")[1].name_with_octave == "Ab4"
    assert notes[4].get("has_mordent", False)
    assert notes[4].get("mordent_pitch").name_with_octave == "B4"
    assert notes[5].get("has_inverted_mordent", False)
    assert notes[5].get("inverted_mordent_pitch").name_with_octave == "F#4"
    assert notes[6].get("has_inverted_mordent", False)
    assert notes[6].get("inverted_mordent_pitch").name_with_octave == "Cb5"
    assert notes[7].get("has_inverted_mordent", False)
    assert notes[7].get("inverted_mordent_pitch").name_with_octave == "F4"
    assert notes[8].get("has_mordent", False)
    assert notes[8].get("mordent_pitch").name_with_octave == "F##4"
    assert notes[9].get("has_mordent", False)
    assert notes[9].get("mordent_pitch").name_with_octave == "C5"
    assert notes[10].get("has_turn", False)
    assert notes[10].get("turn_pitches")[0].name_with_octave == "C5"
    assert notes[10].get("turn_pitches")[1].name_with_octave == "A#4"
    assert notes[11].get("has_turn", False)
    assert notes[11].get("turn_pitches")[0].name_with_octave == "A4"
    assert notes[11].get("turn_pitches")[1].name_with_octave == "F##4"
    assert notes[12].get("has_turn", False)
    assert notes[12].get("turn_pitches")[0].name_with_octave == "Bbb4"
    assert notes[12].get("turn_pitches")[1].name_with_octave == "Gb4"
    assert notes[13].get("has_turn", False)
    assert notes[13].get("turn_pitches")[0].name_with_octave == "Db5"
    assert notes[13].get("turn_pitches")[1].name_with_octave == "Bbb4"

    notes = staffs[1].list_all(Note)
    assert notes[0].get("has_trill", False)
    assert notes[0].get("trill_pitch").name_with_octave == "Gb3"
    assert notes[1].get("is_grace", False)
    assert notes[1].get("has_slash", False)
    assert not notes[2].get("is_grace", False)
    assert notes[3].get("is_grace", False)
    assert notes[3].get("has_slash", False)
    assert notes[5].get("is_grace", False)
    assert notes[5].get("has_slash", False)
    assert notes[7].get("has_trill", False)
    assert notes[7].get("trill_pitch").name_with_octave == "F3"
    assert notes[8].get("has_mordent", False)
    assert notes[8].get("mordent_pitch").name_with_octave == "C#3"
    assert notes[9].get("has_mordent", False)
    assert notes[9].get("mordent_pitch").name_with_octave == "D3"
    assert notes[10].get("has_inverted_mordent", False)
    assert notes[10].get("inverted_mordent_pitch").name_with_octave == "C#3"
    assert notes[11].get("has_inverted_mordent", False)
    assert notes[11].get("inverted_mordent_pitch").name_with_octave == "D3"
    assert notes[12].get("has_turn", False)
    assert notes[12].get("turn_pitches")[0].name_with_octave == "G#3"
    assert notes[12].get("turn_pitches")[1].name_with_octave == "E3"
    assert notes[13].get("has_turn", False)
    assert notes[13].get("turn_pitches")[0].name_with_octave == "A3"
    assert notes[13].get("turn_pitches")[1].name_with_octave == "F#3"
    assert notes[14].get("has_turn", False)
    assert notes[14].get("turn_pitches")[0].name_with_octave == "Bb3"
    assert notes[14].get("turn_pitches")[1].name_with_octave == "G3"
    assert notes[15].get("has_turn", False)
    assert notes[15].get("turn_pitches")[0].name_with_octave == "C4"
    assert notes[15].get("turn_pitches")[1].name_with_octave == "Ab3"
