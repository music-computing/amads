import matplotlib.pyplot as plt

from amads.io.pianoroll import pianoroll
from amads.io.readscore import read_score
from amads.music import example
from amads.polyphony.skyline import skyline

VERBOSE = False  # to minimize test output, set to True to show score data

my_midi_file = example.fullpath("midi/chopin_prelude_7.mid")
assert my_midi_file is not None

print(f"------- input {my_midi_file}")
myscore = read_score(my_midi_file, show=False)
print("------- finished midi file input")
if VERBOSE:
    myscore.show()

pianoroll(myscore, show=False)

print("------- Find skyline")
sl = skyline(myscore)

# print(sl)
if VERBOSE:
    sl.show()

pianoroll(sl, title="Chopin Prelude 7 Skyline", show=False, accidental="both")
plt.show()
