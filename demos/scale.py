# scale_test.py - simple test for scale() function

from amads.all import read_score, scale
from amads.music import example

VERBOSE = False  # to minimize test output, set to True to show score data

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/twochan.mid")
# "midi/tempo.mid"

print("------- input from partitura")
myscore = read_score(my_midi_file, show=False)
print("------- finished input from partitura")

print("------- scaling duration by 2")
scaled_score = scale(myscore, 2, "duration")

print("------- scaled score")
if VERBOSE:
    scaled_score.show()

print("------- scaling onsets by 2")
# this time, we make a copy and then scale the copy in place
scaled_score = scale(myscore.copy(), 2, "onset", inplace=True)

print("------- scaled score")
if VERBOSE:
    scaled_score.show()

print("------- scaling everything (duration and onset) by 2")
scaled_score = scale(myscore, 2, "all")

print("------- scaled score")
if VERBOSE:
    scaled_score.show()
