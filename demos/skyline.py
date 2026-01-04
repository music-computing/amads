import matplotlib.pyplot as plt

from amads.io.pianoroll import pianoroll
from amads.io.readscore import import_midi
from amads.music import example
from amads.polyphony.skyline import skyline

my_midi_file = example.fullpath("midi/chopin_prelude_7.mid")
assert my_midi_file is not None

print(f"------- input {my_midi_file}")
myscore = import_midi(my_midi_file, show=False)
print("------- finished midi file input")
myscore.show()

pianoroll(myscore, show=False)

print("------- Find skyline")
sl = skyline(myscore)

# print(sl)
sl.show()

pianoroll(sl, title="Chopin Prelude 7 Skyline", show=False, accidental="both")
plt.show()
