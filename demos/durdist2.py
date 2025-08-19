"""
Plot the duration distribution of notes in a MIDI file.

This example demonstrates how to calculate and visualize the duration distribution
of notes in a MIDI file.
"""

# %%
import matplotlib.pyplot as plt

from amads.algorithms import duration_distribution_2
from amads.io import music21_midi_import
from amads.music import example

# %%
# Load example MIDI file
my_midi_file = example.fullpath("midi/sarabande.mid")

# %%
# Import MIDI using partitura
myscore = music21_midi_import(my_midi_file, show=False)
myscore.show()

# %%
# Calculate duration distribution
dd = duration_distribution_2(myscore)

print("Duration pair distribution:", dd)
dd.plot(show=True)  # Creates and displays the plot

# %%
# Optain the figure from dd.plot() and show plot explicitly
fig = dd.plot()
plt.show()
