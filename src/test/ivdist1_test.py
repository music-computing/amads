import matplotlib.pyplot as plt
from partitura_midi_import import partitura_midi_import
from ivdist1 import ivdist1
import os

my_midi_file = os.getcwd() + "/../music/midi/twochan.mid"

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
print("------- finished input from partitura")
myscore.show()

print("------- Calculate pitch-class distribution")
id = ivdist1(myscore, weighted=True)

print(id)

# Plot the interval distribution
interval_names = [
    '-P8', '-M7', '-m7', '-M6', '-m6', '-P5', '-d5', '-P4',
    '-M3', '-m3', '-M2', '-m2', 'P1', '+m2', '+M2', '+m3',
    '+M3', '+P4', '+d5', '+P5', '+m6', '+M6', '+m7', '+M7', '+P8'
]
plt.bar(interval_names, id, color='skyblue')

tick_indices = list(range(0, len(interval_names), 3))  # Every 3 ticks
tick_labels = [interval_names[i] for i in tick_indices]

plt.xlabel('Interval')
plt.ylabel('Probability')
plt.title('Interval Distribution')

# Apply every three ticks labels
plt.xticks(ticks=tick_indices, labels=tick_labels)  

plt.show()
