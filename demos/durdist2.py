"""
Plot the duration distribution of notes in a MIDI file.

This example demonstrates how to calculate and visualize the duration distribution
of notes in a MIDI file.
"""

# %%
import matplotlib.pyplot as plt
import numpy as np

from amads.algorithms import duration_distribution_2
from amads.io import partitura_midi_import
from amads.music import example

# %%
# Load example MIDI file
my_midi_file = example.fullpath("midi/sarabande.mid")

# %%
# Import MIDI using partitura
myscore = partitura_midi_import(my_midi_file, ptprint=False)
myscore.show()

# %%
# Calculate duration distribution
dd = duration_distribution_2(myscore)

print("Duration pair distribution:", dd)

# %%
# Plot the 2nd order duration distribution as a heatmap
dd_array = np.array(dd)
plt.figure(figsize=(8, 6))
plt.imshow(dd_array, cmap="gray_r", interpolation="nearest")
plt.colorbar(label="Probability")
plt.xlabel("Duration (to)")
plt.ylabel("Duration (from)")
plt.title("2nd Order Duration Distribution")

bin_centers = [
    "1/4",
    "sqrt(2)/4",
    "1/2",
    "sqrt(2)/2",
    "1",
    "sqrt(2)",
    "2",
    "2*sqrt(2)",
    "4",
]
plt.xticks(range(len(bin_centers)), bin_centers)
plt.yticks(range(len(bin_centers)), bin_centers)

plt.gca().invert_yaxis()

plt.show()

# %%
