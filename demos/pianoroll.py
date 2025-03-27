from matplotlib import pyplot as plt

from amads.all import partitura_midi_import, pianoroll
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")
myscore = partitura_midi_import(my_midi_file, ptprint=False)

pianoroll(myscore)

my_midi_file = example.fullpath("midi/twochan.mid")
myscore = partitura_midi_import(my_midi_file, ptprint=False)

pianoroll(myscore)
plt.show()
