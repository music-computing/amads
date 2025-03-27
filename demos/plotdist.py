import matplotlib.pyplot as plt

from amads.all import partitura_midi_import, pcdist1, plotdist
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")

myscore = partitura_midi_import(my_midi_file)

pcd = pcdist1(myscore)
fig = plotdist(pcd)

plt.show()
