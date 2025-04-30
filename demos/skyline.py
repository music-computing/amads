import matplotlib.pyplot as plt

from amads.all import amads_midi_import, pianoroll, skyline
from amads.music import example

my_midi_file = example.fullpath("midi/chopin_prelude_7.mid")


print("------- input from partitura")
myscore = amads_midi_import(my_midi_file, show=False)
print("------- finished input from partitura")
myscore.show()

pianoroll(myscore, show=False)

print("------- Find skyline")
sl = skyline(myscore)

# print(sl)
sl.show()

pianoroll(sl, show=False)
plt.show()
