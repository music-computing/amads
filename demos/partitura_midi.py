# partitura_midi_test.py - some tests for partitura_midi_import.py

from amads.all import partitura_midi_import, pitch_mean
from amads.music import example

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/twochan.mid")
# "midi/tempo.mid"

print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=True)
myscore.show()


print("------- result of score copy")
scorecopy = myscore.deep_copy()
scorecopy.show()


print("------- result from strip_chords")
nochords = scorecopy.strip_chords()
nochords.show()

print("------- result from strip_ties")
noties = scorecopy.strip_ties()
noties.show()

print("------- result from flatten")
flatscore = scorecopy.flatten()
flatscore.show()

print("------- result from keynum_list")
print(myscore.collapse_parts().content[0].content)

print("------- result from keynum_list(part=(0))")
print(myscore.collapse_parts(part=[0]).content[0].content)

print("------- result from pitch_mean(myscore)")
print(pitch_mean(myscore))

print("------- result from pitch_mean(myscore, weighted=True)")
print(pitch_mean(myscore, weighted=True))
