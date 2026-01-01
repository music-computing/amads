import matplotlib.pyplot as plt

from amads.all import import_midi, pitch_class_distribution_1
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None
myscore = import_midi(my_midi_file)

pcd = pitch_class_distribution_1(myscore)
pcd.plot(show=False)

plt.show()
