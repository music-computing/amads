import matplotlib.pyplot as plt
from pytest import fixture

from amads.io.pt_midi_import import partitura_midi_import
from amads.music import example


@fixture
def twochan_score():
    midi_file = example.fullpath("midi/twochan.mid")
    return partitura_midi_import(midi_file, ptprint=False)


@fixture
def twochan_notes(twochan_score):
    return twochan_score.sorted_notes()


# Stop matplotlib plot.show() from blocking the tests
plt.ion()
