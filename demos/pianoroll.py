from matplotlib import pyplot as plt
from musmart.pt_midi_import import partitura_midi_import
from musmart.pianoroll import pianoroll
from musmart import example

my_midi_file = example.fullpath("midi/sarabande.mid")
myscore = partitura_midi_import(my_midi_file, ptprint=False)

pianoroll(myscore)

my_midi_file = example.fullpath("midi/twochan.mid")
myscore = partitura_midi_import(my_midi_file, ptprint=False)

pianoroll(myscore)
plt.show()