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
scaled_score = scale(myscore.deep_copy(), 2, "duration")

print("------- scaled score")
scaled_score.show()

print("------- scaling delta by 2")
scaled_score = scale(myscore.deep_copy(), 2, "onset")

print("------- scaled score")
scaled_score.show()

print("------- scaling everything (duration and delta) by 2")
scaled_score = scale(myscore.deep_copy(), 2, "all")

print("------- scaled score")
scaled_score.show()
