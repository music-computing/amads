import matplotlib.pyplot as plt

from amads.all import Part, ivdist1, partitura_midi_import
from amads.music import example

my_midi_file = example.fullpath("midi/twochan.mid")

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
print("------- finished input from partitura")
myscore.show()
print("------- Removing all but the first part")
mono_score = myscore.emptycopy()
first_part = next(myscore.find_all(Part))  # Get the first part
first_part.copy(mono_score)
print("------- finished removing all but the first part")
mono_score.show()
print("------- Calculate pitch-class distribution")
id = ivdist1(mono_score, weighted=True)

print(id)

# Plot the interval distribution
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
plt.bar(interval_names, id, color="skyblue")

tick_indices = list(range(0, len(interval_names), 3))  # Every 3 ticks
tick_labels = [interval_names[i] for i in tick_indices]

plt.xlabel("Interval")
plt.ylabel("Probability")
plt.title("Interval Distribution")

# Apply every three ticks labels
plt.xticks(ticks=tick_indices, labels=tick_labels)

plt.show()
