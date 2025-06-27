import matplotlib.pyplot as plt
from pytest import fixture

from amads.io.readscore import import_midi
from amads.music import example


@fixture
def twochan_score():
    midi_file = example.fullpath("midi/twochan.mid")
    return import_midi(midi_file, show=True).quantize(4)


@fixture
def twochan_notes(twochan_score):
    print("twochan_notes fixture gets score:")
    score = twochan_score
    score.show()
    notes = score.get_sorted_notes()
    print("twochan_notes fixture gets sorted notes:")
    for note in notes:
        note.show()
    return twochan_score.get_sorted_notes()


# Stop matplotlib plot.show() from blocking the tests
plt.ion()
