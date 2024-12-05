"""
Plot the duration distribution of notes in a MIDI file.

This example demonstrates how to calculate and visualize the duration distribution
of notes in a MIDI file.
"""

from musmart import example
from musmart.pt_midi_import import partitura_midi_import
from musmart.durdist2 import duration_distribution_2

# Load example MIDI file
my_midi_file = example.fullpath("midi/sarabande.mid")

# Import MIDI using partitura
myscore = partitura_midi_import(my_midi_file, ptprint=False)
# myscore.show()

# Calculate duration distribution
dd = duration_distribution_2(myscore)
plt, fig = dd.plot()

print("Duration pair distribution:", dd.data, dd.x_categories, 
      dd.y_categories, dd.x_label, dd.y_label)
plt.show()
