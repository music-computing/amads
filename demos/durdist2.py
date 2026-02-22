"""
Plot the duration distribution of notes in a MIDI file.

This example demonstrates how to calculate and visualize the duration distribution
of notes in a MIDI file.
"""

# %%
import matplotlib.pyplot as plt

from amads.io.readscore import read_score, set_preferred_midi_reader
from amads.music import example
from amads.time.durdist2 import duration_distribution_2

# %%
# Load example MIDI file
my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None, "Example MIDI file not found."
# %%
# Import MIDI using music21
set_preferred_midi_reader("music21")  # for consistent testing
print("------- input from music21")
myscore = read_score(my_midi_file, show=False)
myscore.show()

# %%
# Calculate duration distribution
dd = duration_distribution_2(myscore)

print("Duration pair distribution:", dd)
dd.plot(show=True)  # Creates and displays the plot

# %%
# Obtain the figure from dd.plot() and show plot explicitly
fig = dd.plot()
plt.show()
