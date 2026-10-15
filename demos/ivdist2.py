# ivdist2_test - simple test for ivdist2() function

from amads.all import (
    interval_distribution_2,
    read_score,
    set_preferred_midi_reader,
)
from amads.music import example

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None
# "midi/tempo.mid"

print("------- input from music21")
set_preferred_midi_reader("music21")  # for consistent testing
myscore = read_score(my_midi_file, show=False)
print("------- finished input from music21")

# myscore = myscore.flatten()

print("------- Calculate pitch-class distribution")
id = interval_distribution_2(myscore, weighted=False)
id.plot(show=True)
