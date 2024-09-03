"""
How to run:
1. navigate to the toolkit directory.
2. python -m tests.pcdist1_test
"""

import matplotlib.pyplot as plt
import os
from musmart.io_tools.partitura_midi_import import partitura_midi_import
from musmart.algorithm.pcdist1 import pcdist1

# for some reason, could not open file with just the relative path
my_midi_file = os.getcwd() + "/music/midi/twochan.mid"

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
myscore.show()
print("------- finished input from partitura")


print("------- Calculate pitch-class distribution")
pcd = pcdist1(myscore)

print(pcd)

# Plot the pitch-class distribution
pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#',
                 'B']
plt.bar(pitch_classes, pcd, color='skyblue')
plt.xlabel('Pitch Class')
plt.ylabel('Probability')
plt.title('Pitch-Class Distribution')
plt.show()
