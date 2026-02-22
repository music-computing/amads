import matplotlib.pyplot as plt
from pytest import fixture

from amads.io.readscore import read_score
from amads.music import example


@fixture
def twochan_score():
    midi_file = example.fullpath("midi/twochan.mid")
    assert midi_file is not None
    return read_score(midi_file, show=True).quantize(4)


@fixture
def twochan_notes(twochan_score):
    print("twochan_notes fixture gets score:")
    score = twochan_score
    score.show()
    notes = score.get_sorted_notes()
    print("twochan_notes fixture gets sorted notes:")
    for note in notes:
        note.show()
    return notes


# Stop matplotlib plot.show() from blocking the tests
plt.ion()
