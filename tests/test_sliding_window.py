from typing import Iterable

from pytest import approx

from amads.algorithms.slice.window import sliding_window
from amads.core.basics import Note, Score


def test_sliding_window(twochan_score: Score, twochan_notes: Iterable[Note]):
    size = 4.0  # one bar
    step = 0.01

    score = twochan_score.flatten(collapse=True)

    last_note = twochan_notes[-1]
    last_note_off = last_note.delta + last_note.duration
    assert last_note_off == approx(16.0)

    windows = sliding_window(
        score,
        size=size,
        step=step,
        align="right",
    )
    windows = list(windows)

    first_slice = windows[0]
    assert first_slice.start == approx(-4.0)
    assert first_slice.end == approx(0.0)
    assert len(first_slice.content) == 0

    last_slice = windows[-1]
    assert last_slice.start == approx(last_note_off, abs=step * 3)
    assert len(last_slice.content) == 0

    # The second slice should include the score's opening two notes
    assert len(windows[1].content) == 2
    assert windows[1].content[0].keynum == 67 - 2 * 12
    assert windows[1].content[1].keynum == 67
