from amads.all import (
    interval_size_distribution_1,
    read_score,
    set_preferred_midi_reader,
)
from amads.music import example

my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None

set_preferred_midi_reader("music21")  # for consistent testing
print("------- input from music21")
myscore = read_score(my_midi_file, show=False)
print("------- finished input from music21")
myscore.show()

print("------- Calculate interval size distribution")
isd = interval_size_distribution_1(myscore, weighted=True)

print(isd)
isd.plot(show=True)
