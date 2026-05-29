from amads.all import read_score
from amads.io.displayscore import display_score, set_preferred_display_method
from amads.music import example

set_preferred_display_method("pianoroll")
my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None, "Example MIDI file not found."
myscore = read_score(my_midi_file, show=False)

display_score(myscore)

my_midi_file = example.fullpath("midi/twochan.mid")
assert my_midi_file is not None, "Example MIDI file not found."
myscore = read_score(my_midi_file, show=False)

display_score(myscore)
