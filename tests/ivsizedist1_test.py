import matplotlib.pyplot as plt
from partitura_midi_import import partitura_midi_import
from ivsizedist1 import ivsizedist1

my_midi_file = "../music/midi/sarabande.mid"

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
print("------- finished input from partitura")
myscore.show()

print("------- Calculate interval size distribution")
isd = ivsizedist1(myscore, weighted=True)

print(isd)

# Plot the interval size distribution
interval_names = [
    'P1', 'm2', 'M2', 'm3', 'M3', 'P4', 'd5',
    'P5', 'm6', 'M6', 'm7', 'M7', 'P8'
]
plt.bar(interval_names, isd, color='skyblue')
plt.xlabel('Interval Size')
plt.ylabel('Proportion (%)')
plt.title('Interval Size Distribution')
plt.show()