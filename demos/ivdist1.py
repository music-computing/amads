from typing import cast

import matplotlib.pyplot as plt

from amads.all import Part, Score, interval_distribution_1, music21_midi_import
from amads.music import example

my_midi_file = example.fullpath("midi/twochan.mid")
assert my_midi_file is not None

print("------- input from partitura")
myscore = music21_midi_import(my_midi_file, show=False)
print("------- finished input from partitura")
myscore.show()
print("------- Removing all but the first part")
mono_score = cast(Score, myscore.emptycopy())
first_part = next(myscore.find_all(Part))  # Get the first part
first_part.insert_copy_into(mono_score)
print("------- finished removing all but the first part")
mono_score.show()
print("------- Calculate pitch-class distribution")
id = interval_distribution_1(mono_score, weighted=True)

print(id)

id.plot()
plt.show()
