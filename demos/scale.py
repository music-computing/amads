# scale_test.py - simple test for scale() function

from amads.all import partitura_midi_import, scale
from amads.music import example

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/twochan.mid")
# "midi/tempo.mid"

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
print("------- finished input from partitura")

print("------- scaling duration by 2")
scaled_score = scale(myscore, 2, "duration")

print("------- scaled score")
scaled_score.show()

print("------- scaling onsets by 2")
# this time, we make a copy and then scale the copy in place
scaled_score = scale(myscore.copy(), 2, "onset", inplace=True)

print("------- scaled score")
scaled_score.show()

print("------- scaling everything (duration and onset) by 2")
scaled_score = scale(myscore, 2, "all")

print("------- scaled score")
scaled_score.show()
