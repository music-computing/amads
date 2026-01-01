# ivdist2_test - simple test for ivdist2() function

from amads.all import interval_distribution_2, music21_midi_import
from amads.music import example

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None
# "midi/tempo.mid"

print("------- input from partitura")
myscore = music21_midi_import(my_midi_file, show=False)
print("------- finished input from partitura")

# myscore = myscore.flatten()

print("------- Calculate pitch-class distribution")
id = interval_distribution_2(myscore, weighted=False)
id.plot(show=True)
