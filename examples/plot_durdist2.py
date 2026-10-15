"""
Duration pair distributions
===========================

This example demonstrates how to calculate and visualize the pair-wise
duration distribution of notes in a MIDI file.
"""

from amads.algorithms import duration_distribution_2
from amads.io import read_score
from amads.music import example

# Load example MIDI file
my_midi_file = example.fullpath("midi/sarabande.mid")

# Import MIDI using partitura
myscore = read_score(my_midi_file, show=False)
# myscore.show()

# Calculate duration distribution
dd = duration_distribution_2(myscore)
fig = dd.plot()

print(
    "Duration pair distribution:",
    dd.data,
    dd.x_categories,
    dd.y_categories,
    dd.x_label,
    dd.y_label,
)
