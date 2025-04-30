import matplotlib.pyplot as plt

from amads.all import amads_midi_import, pianoroll, segment_gestalt
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")


print("------- input from partitura")
myscore = amads_midi_import(my_midi_file, show=False)
print("------- finished input from partitura")

fig = pianoroll(myscore)

print("------- Executing segmentgestalt")
clang_starts, segment_starts = segment_gestalt(myscore)
print(clang_starts)
print(segment_starts)
xmin, xmax, ymin, ymax = plt.axis()

plt.vlines(clang_starts, ymin, ymax, colors="purple", label="clang boundary starts")
plt.vlines(segment_starts, ymin, ymax, colors="green", label="segment boundary starts")
plt.legend(loc="best")

plt.show()
