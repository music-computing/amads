# pcdist2_test.py - simple test of pcdist2()

from amads.all import import_midi, pitch_class_distribution_2
from amads.music import example

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/sarabande.mid")
# "midi/tempo.mid"
assert my_midi_file is not None

print("------- input from partitura")
myscore = import_midi(my_midi_file, show=False)
print("------- finished input from partitura")

# myscore = myscore.flatten()

print("------- Calculate pitch-class distribution")
pcd = pitch_class_distribution_2(myscore, weighted=False)
plot = pcd.plot(show=False)
plot.show()
