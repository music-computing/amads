# read_score_dmeo.py - examples of reading scores

from amads.io.readscore import (
    read_score,
    set_preferred_midi_reader,
    set_preferred_xml_reader,
    set_reader_warning_level,
)
from amads.music import example

# read the small midi file: "midi/twochan.mid"
#
# You can read with different readers. We use the default ("pretty_midi") here.
my_midi_file = example.fullpath("midi/short2staff.mid")
assert my_midi_file is not None
myscore = read_score(my_midi_file)
print("------- short2staff.mid read with default reader -------")
myscore.show()

# notice there are multiple warnings printed by pretyy_midi. You can minimize
# these by setting the warning level to "low" so at most one message is printed,
# telling you how many warnings were generated. In this case the number will be
# just 1 since all but 1 warning in the previous read were about loading the
# pretty midi module itself, but now it is already loaded.
print()  # blank line for readability
set_reader_warning_level("low")
myscore2 = read_score(my_midi_file)
print("------- short2staff.mid read with warnings minimized -------")
myscore2.show()

# The MIDI file has two tracks representing the two staves of a piano part.
# By default, since both tracks have the same instrument (Acoustic Grand Piano),
# read_score groups them into a single Part with two Staffs. You can change this
# behavior by setting the "group_by_instrument" flag to False, in which case
# each track becomes a separate Part. There will then be 2 Parts instead of 1.
# We will also set warnings to "none" to suppress even the notice that warnings
# were generated.
print()  # blank line for readability
set_reader_warning_level("none")
myscore3 = read_score(my_midi_file, group_by_instrument=False)
print("------- short2staff.mid read with group_by_instrument=False -------")
myscore3.show()

# Notice that there are notes tied across the bar line into measure 2. This is
# an AMADS *full* score, which includes Parts, Staffs, Measures, and more. You
# can read a *flat* score that omits Staffs and Measures and joins tied notes
# into single notes. To do this, set the "flatten" flag to True.
print()  # blank line for readability
myscore4 = read_score(my_midi_file, flatten=True)
print("------- short2staff.mid read with flatten=True -------")
myscore4.show()

# You can also specify which reader to use. Here we read the same file with
# Music21. Results can be slightly different.
print()  # blank line for readability
set_preferred_midi_reader("music21")
set_reader_warning_level("low")
myscore5 = read_score(my_midi_file)
print("------- short2staff.mid read with music21 reader -------")
myscore5.show()

# You can also read MusicXML files. Here we read the original MusicXML file
# that was used to create the MIDI file above.
print()  # blank line for readability
my_xml_file = example.fullpath("musicxml/short2staff.mxl")
assert my_xml_file is not None
set_preferred_xml_reader("music21")
set_reader_warning_level("low")
myscore6 = read_score(my_xml_file)
print("------- short2staff.xml read with music21 reader -------")
myscore6.show()

# If your goal is just to extract the notes, you should work with a flat score
# and retrieve the notes with one of:
#    score.find_all(Note)  # all notes iterator, in order of the Parts
#    score.list_all(Note)  # all notes in a list, in order of the Parts
#    score.get_sorted_notes()  # all notes in a list, sorted by onset time
print()  # blank line for readability
print("------- Extracting notes only from score -------")
for note in myscore4.get_sorted_notes():  # myscore4 is a flat score
    print(
        f"  Note: pitch={note.pitch}, onset={note.onset:.3f},"
        f" duration={note.duration:.3f}"
    )
