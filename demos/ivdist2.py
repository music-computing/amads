# ivdist2_test - simple test for ivdist2() function

import matplotlib.pyplot as plt
import numpy as np

from amads.all import ivdist2, partitura_midi_import
from amads.music import example

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/sarabande.mid")
# "midi/tempo.mid"

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
print("------- finished input from partitura")

# myscore = myscore.flatten()

print("------- Calculate pitch-class distribution")
id = ivdist2(myscore, weighted=False)

print(id)

# Plot the pitch-class distribution as a heatmap
pcd_array = np.array(id)
plt.figure(figsize=(8, 6))
plt.imshow(pcd_array, cmap="hot", interpolation="nearest")
plt.colorbar(label="Probability")
plt.xlabel("Interval (to)")
plt.ylabel("Interval (from)")
plt.title("2nd Order Interval Distribution")

interval_names = [
    "-P8",
    "-M7",
    "-m7",
    "-M6",
    "-m6",
    "-P5",
    "-d5",
    "-P4",
    "-M3",
    "-m3",
    "-M2",
    "-m2",
    "P1",
    "+m2",
    "+M2",
    "+m3",
    "+M3",
    "+P4",
    "+d5",
    "+P5",
    "+m6",
    "+M6",
    "+m7",
    "+M7",
    "+P8",
]
plt.xticks(range(25), interval_names, rotation=90)
plt.yticks(range(25), interval_names)

plt.show()
