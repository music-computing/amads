import matplotlib.pyplot as plt

from amads.all import pitch_class_distribution_1, read_score
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None
myscore = read_score(my_midi_file)

pcd = pitch_class_distribution_1(myscore)
pcd.plot(show=False)

plt.show()
