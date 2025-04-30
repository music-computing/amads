from matplotlib import pyplot as plt

from amads.all import amads_midi_import, pianoroll
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")
myscore = amads_midi_import(my_midi_file, show=False)

pianoroll(myscore)

my_midi_file = example.fullpath("midi/twochan.mid")
myscore = amads_midi_import(my_midi_file, show=False)

pianoroll(myscore)
plt.show()
