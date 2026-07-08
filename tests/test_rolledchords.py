"""test_rolledchord tests for reading musicxml with rolled chords
"""

from amads.core.basics import Chord, Note
from amads.io.readscore import read_score, set_preferred_xml_reader
from amads.music import example

VERBOSE = False


def test_rolledchord():
    set_preferred_xml_reader("music21")
    score = read_score(example.fullpath("musicxml/rolledchords.xml"))
    if VERBOSE:
        score.show()
    chords = score.list_all(Chord)
    assert len(chords) > 0
    assert sum(ch.get("rolled", False) for ch in chords) == 4

    score = score.flatten()
    chords = score.list_all(Chord)
    assert len(chords) == 0
    notes = score.list_all(Note)
    assert sum(nt.get("rolled", False) for nt in notes) == 12
