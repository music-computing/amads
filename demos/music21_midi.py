# music21_midi_test.py - some tests for music21_midi_import.py

from amads.all import music21_midi_import, pitch_mean
from amads.music import example

# "midi/tones.mid"
my_midi_file = example.fullpath("midi/twochan.mid")
# "midi/tempo.mid"

print("------- input from music21")
myscore = music21_midi_import(my_midi_file, show=True)
myscore.show()


print("------- result of score copy")
scorecopy = myscore.copy()
scorecopy.show()


print("------- result from expand_chords")
nochords = scorecopy.expand_chords()
nochords.show()

print("------- result from merge_tied_notes")
noties = scorecopy.merge_tied_notes()
noties.show()

print("------- result from flatten")
flatscore = scorecopy.flatten()
flatscore.show()

print("------- result from collapse_parts()")
myscore.collapse_parts().show()

print("------- result from collapse_parts(part=[0])")
myscore.collapse_parts(part=[0]).show()

print("------- result from pitch_mean(myscore)")
print(pitch_mean(myscore))

print("------- result from pitch_mean(myscore, weighted=True)")
print(pitch_mean(myscore, weighted=True))
