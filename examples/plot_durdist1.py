"""
Duration distributions (I)
==========================

This example demonstrates how to calculate and visualize the duration distribution
of notes in a MIDI file.
"""

import matplotlib.pyplot

from amads.algorithms import duration_distribution_1
from amads.io import amads_midi_import
from amads.music import example

# Load example MIDI file
my_midi_file = example.fullpath("midi/sarabande.mid")

# Import MIDI using partitura
myscore = amads_midi_import(my_midi_file, show=False)
# myscore.show()

# Calculate duration distribution
dd = duration_distribution_1(myscore)
dd.plot()

print("Duration distribution:", dd.data, dd.x_categories)
matplotlib.pyplot.show()

# %%
