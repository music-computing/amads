"""
Test the `ivdirdist1` function
"""

import matplotlib.pyplot as plt

from amads.all import (
    interval_direction_distribution_1,
    read_score,
    set_preferred_midi_reader,
)
from amads.music import example

my_midi_file = example.fullpath("/midi/sarabande.mid")
assert my_midi_file is not None

print("------- input from music21")
set_preferred_midi_reader("music21")  # for consistent testing
myscore = read_score(my_midi_file, show=False)
print("------- finished input from music21")
myscore.show()

print("------- Calculate pitch-class distribution")
id = interval_direction_distribution_1(myscore, weighted=True)

print(id)
id.plot()
plt.show()
