from amads.all import interval_size_distribution_1, music21_midi_import
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None

print("------- input from partitura")
myscore = music21_midi_import(my_midi_file, show=False)
print("------- finished input from partitura")
myscore.show()

print("------- Calculate interval size distribution")
isd = interval_size_distribution_1(myscore, weighted=True)

print(isd)
isd.plot(show=True)
