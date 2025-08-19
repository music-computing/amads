import matplotlib.pyplot as plt

from amads.all import import_midi, pcdist1, plotdist
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")

myscore = import_midi(my_midi_file)

pcd = pcdist1(myscore)
fig = plotdist(pcd)

plt.show()
