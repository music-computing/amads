import matplotlib.pyplot as plt

from amads.all import partitura_midi_import, pianoroll
from amads.melody.contour.combcontour import pairwiseCombinationContour
from amads.music import example

my_midi_file = example.fullpath("midi/tones.mid")

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
print("------- finished input from partitura")

fig = pianoroll(myscore)

print("------- Executing combcontour")
notes, contour_mtx = pairwiseCombinationContour(myscore)

print(contour_mtx)
plt.show()
