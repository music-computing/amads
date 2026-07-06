import tempfile
from typing import cast

import pytest

from amads.algorithms.scores_compare import scores_compare
from amads.core.basics import Measure, Score, Staff, TimeSignature
from amads.io import readscore
from amads.io.readscore import (
    read_score,
    set_preferred_midi_reader,
    set_preferred_xml_reader,
    set_reader_warning_level,
)
from amads.io.writescore import set_preferred_midi_writer, write_score
from amads.music import example

VERBOSE = True


def _time_signature_tuples(score):
    return [(ts.quarters, ts.upper, ts.lower) for ts in score.time_signatures]


def _check_staff_measure_tuples(score, expected):
    for staff in score.list_all(Staff):
        measures = staff.find_all(Measure)
        tuples = [(measure.onset, measure.duration) for measure in measures]
        assert tuples == expected


def _make_true_and_expected_scores():
    xml_path = example.fullpath("musicxml/shortbars.xml")
    assert xml_path is not None, "Could not find musicxml/shortbars.xml"

    set_reader_warning_level("none")
    set_preferred_xml_reader(readscore._default_xml_reader)
    true_score = read_score(xml_path, show=True)

    expected_score = cast(Score, true_score.copy())
    if VERBOSE:
        print("Expected score for MIDI roundtrip:")
        expected_score.show()
    # hack the copy so that unfull measures (pickuup and endings) have time
    # signatures that reflect their actual duration, which is what we expect
    # when we write this score as a Standard MIDI File.
    expected_score.time_signatures = [
        TimeSignature(0.0, 1, 4),
        TimeSignature(1.0, 2, 4),
        TimeSignature(5.0, 1, 4),
        TimeSignature(6.0, 1, 4),
        TimeSignature(7.0, 2, 4),
    ]

    return true_score, expected_score


@pytest.mark.parametrize(
    ("writer", "reader"),
    [
        ("pretty_midi", "music21"),
        ("music21", "mido"),
        ("mido", "pretty_midi"),
    ],
)
def test_midi_shortbars_roundtrip(writer, reader):
    """Short pickup and ending bars should survive MIDI roundtrip.

    MIDI cannot encode short bars directly, so writers should emit new
    time signatures for the pickup and the two one-beat ending measures.
    When the MIDI file is read back, the score should preserve the original
    measure alignment and performed notes, but the time signatures will
    differ from the original.
    """
    true_score, expected_score = _make_true_and_expected_scores()

    expected_staff_measures = [
        (0.0, 1.0),
        (1.0, 2.0),
        (3.0, 2.0),
        (5.0, 1.0),
        (6.0, 1.0),
        (7.0, 2.0),
        (9.0, 2.0),
        (11.0, 2.0),
        (13.0, 2.0),
    ]

    _check_staff_measure_tuples(expected_score, expected_staff_measures)

    temp_file = tempfile.NamedTemporaryFile(
        suffix="_shortbars.mid", delete=False
    )
    midi_path = temp_file.name
    temp_file.close()

    set_preferred_midi_writer(writer)
    write_score(true_score, midi_path)

    set_preferred_midi_reader(reader)
    if VERBOSE:
        print(f"Reading back MIDI file {midi_path} with reader {reader}")
    roundtrip_score = read_score(midi_path, show=VERBOSE)
    if VERBOSE:
        print(f"Roundtrip score from MIDI file {midi_path}:")
        roundtrip_score.show()

    assert _time_signature_tuples(roundtrip_score) == [
        (0.0, 1, 4),
        (1.0, 2, 4),
        (5.0, 1, 4),
        (7.0, 2, 4),
    ]
    _check_staff_measure_tuples(roundtrip_score, expected_staff_measures)
    assert scores_compare(expected_score, roundtrip_score, midi=True)
