"""
Duration distributions (I)
==========================

This example demonstrates how to calculate and visualize the duration distribution
of notes in a MIDI file.
"""

from amads.algorithms import duration_distribution_1
from amads.io import partitura_midi_import
from amads.music import example

# Load example MIDI file
my_midi_file = example.fullpath("midi/sarabande.mid")

# Import MIDI using partitura
myscore = partitura_midi_import(my_midi_file, ptprint=False)
# myscore.show()

# Calculate duration distribution
dd = duration_distribution_1(myscore)
plt, fig = dd.plot()

print("Duration distribution:", dd.data, dd.x_categories)
plt.show()

# %%
