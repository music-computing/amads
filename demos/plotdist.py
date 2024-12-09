import matplotlib.pyplot as plt
from amads.pt_midi_import import partitura_midi_import
from amads.pcdist1 import pcdist1
from amads.plotdist import plotdist
from amads import example

my_midi_file = example.fullpath("midi/sarabande.mid")

myscore = partitura_midi_import(my_midi_file)

pcd = pcdist1(myscore)
fig = plotdist(pcd)

plt.show()