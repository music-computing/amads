"""
Basic start on testing readscore.

Important business first: score from URL ;)
"""

from amads.io.readscore import read_score, set_reader_warning_level


def test_pitch_comparison():
    set_reader_warning_level("none")
    test_path = (
        "https://github.com/MarkGotham/species/raw/refs/heads/main/1x1/005.mxl"
    )
    score = read_score(test_path)
    notes = score.get_sorted_notes()
    assert len(notes) == 22
