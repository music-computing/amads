# music21_xml_test.py - some tests for music21_xml_import.py

from typing import cast

from amads.all import read_score
from amads.core.basics import Score
from amads.music import example

# my_xml_file = example.fullpath("musicxml/ex1.xml") - fails with music21
my_xml_file = example.fullpath("musicxml/ex2.xml")
# my_xml_file = example.fullpath("musicxml/ex3.xml") - fails with music21


print("------- input from music21")
myscore = read_score(my_xml_file, format="musicxml", show=True)
myscore.show()

print("------- result of score copy")
scorecopy = myscore.copy()
scorecopy = cast(Score, scorecopy)
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
