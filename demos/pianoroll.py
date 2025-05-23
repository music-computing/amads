from matplotlib import pyplot as plt

from amads.all import import_midi, pianoroll
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")
myscore = import_midi(my_midi_file, show=False)

pianoroll(myscore)

my_midi_file = example.fullpath("midi/twochan.mid")
myscore = import_midi(my_midi_file, show=False)

pianoroll(myscore)
plt.show()
