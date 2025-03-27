import matplotlib.pyplot as plt

from amads.all import partitura_midi_import, pcdist1
from amads.music import example

# for some reason, could not open file with just the relative path
my_midi_file = example.fullpath("midi/sarabande.mid")

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
myscore.show()
print("------- finished input from partitura")


print("------- Calculate pitch-class distribution")
pcd = pcdist1(myscore)

print(pcd)

# Plot the pitch-class distribution
pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
plt.bar(pitch_classes, pcd, color="skyblue")
plt.xlabel("Pitch Class")
plt.ylabel("Probability")
plt.title("Pitch-Class Distribution")
plt.show()
