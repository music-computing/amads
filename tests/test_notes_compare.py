"""tests for scores_compare.notes_compare
"""

import pytest

from amads.algorithms.scores_compare import notes_compare
from amads.core.basics import Note
from amads.core.pitch import Pitch
from amads.io.readscore import read_score
from amads.music.example import fullpath


def test_notes_compare():
    """Test that comparing two copies of a score returns correct results"""
    path = fullpath("midi/sarabande.mid")
    s1 = read_score(path)
    s2 = read_score(path)
    # we want get_sorted_notes() to return the actual notes in the score,
    # not copies, so we can purturb the score and check the returned unmatched
    # notes lists. but get_sorted_notes() needs to copy the score when there
    # are tied notes, so we need to merge tied notes first and then tell
    # get_sorted_notes() that there are no tied_notes.
    s1 = s1.merge_tied_notes()
    s2 = s2.merge_tied_notes()
    result = notes_compare(s1, "score1", s2, "score2")
    assert result[0] is True
    assert result[1] == []
    assert result[2] == []
    assert result[3] == 0.0
    assert result[4] == 0.0

    # purturb s2 slightly and check that the result is different
    s1_notes = s1.list_all(Note)
    s2_notes = s2.list_all(Note)
    s2_notes[10].duration += 0.001  # type: ignore
    result = notes_compare(s1, "score1", s2, "score2", tolerance=0.002)
    assert result[0] is True
    assert result[1] == []
    assert result[2] == []
    assert result[3] == 0.0
    assert result[4] == pytest.approx(0.001)

    # change to an enharmonic and check for ignore spelling
    s2_notes[10].pitch = Pitch(s2_notes[10].key_num, alt=-2)  # type: ignore
    result = notes_compare(
        s1, "score1", s2, "score2", tolerance=0.002, spelling=False
    )
    assert result[0] is True
    assert result[1] == []
    assert result[2] == []
    assert result[3] == 0.0
    assert result[4] == pytest.approx(0.001)

    # see if enharmonic is caught when spelling is True
    result = notes_compare(
        s1, "score1", s2, "score2", tolerance=0.002, spelling=True
    )
    assert result[0] is False
    assert len(result[1]) == 1
    assert result[1][0] == s1_notes[10]
    assert len(result[2]) == 1
    assert result[2][0] == s2_notes[10]
    assert result[3] == 0.0
    assert result[4] == pytest.approx(0.0)

    # alter a pitch in s1 and another in s2 and check that the result is
    # correct. Also alter an onset to see that max_onset_diff is correctly
    # calculated.
    s1_notes[20].pitch = Pitch(s1_notes[20].key_num + 1)  # type: ignore
    s2_notes[30].pitch = Pitch(s2_notes[30].key_num + 1)  # type: ignore
    s1_notes[40].onset += 0.0015  # type: ignore
    result = notes_compare(s1, "score1", s2, "score2", tolerance=0.002)
    assert result[0] is False
    assert len(result[1]) == 2
    assert result[1][0] == s1_notes[20]
    assert result[1][1] == s1_notes[30]
    assert len(result[2]) == 2
    assert result[2][0] == s2_notes[20]
    assert result[2][1] == s2_notes[30]
    assert result[3] == pytest.approx(0.0015)
    assert result[4] == pytest.approx(0.0015)

    # test with early stopping
    result = notes_compare(
        s1, "score1", s2, "score2", tolerance=0.002, early_stop=True
    )
    assert result[0] is False
    assert len(result[1]) == 1
    assert result[1][0] == s1_notes[20]
    assert len(result[2]) == 0
    assert result[3] == pytest.approx(0.0)
    assert result[4] == pytest.approx(0.001)
