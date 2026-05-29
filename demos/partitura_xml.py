# partitura_xml_test.py - some tests for partitura_import.py

from typing import cast

from amads.core.basics import Score
from amads.io.pt_import import partitura_import
from amads.music import example

VERBOSE = False

# my_xml_file = example.fullpath("music/musicxml/ex1.xml")
my_xml_file = example.fullpath("musicxml/ex2.xml")
# my_xml_file = example.fullpath("musicxml/ex3.xml")


print("------- input from partitura")
myscore = partitura_import(my_xml_file, "musicxml", show=VERBOSE)
if VERBOSE:
    myscore.show()

print("------- result of score copy")
scorecopy = myscore.copy()
scorecopy = cast(Score, scorecopy)
if VERBOSE:
    scorecopy.show()


print("------- result from expand_chords")
nochords = scorecopy.expand_chords()
if VERBOSE:
    nochords.show()

print("------- result from merge_tied_notes")
noties = scorecopy.merge_tied_notes()
if VERBOSE:
    noties.show()

print("------- result from flatten")
flatscore = scorecopy.flatten()
if VERBOSE:
    flatscore.show()
