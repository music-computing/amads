# partitura_xml_test.py - some tests for partitura_xml_import.py

from amads.all import partitura_xml_import
from amads.music import example

my_xml_file = None  # defaults to pt.EXAMPLE_MUSICXML
# my_xml_file = example.fullpath("music/musicxml/ex1.xml")
my_xml_file = example.fullpath("musicxml/ex2.xml")
# my_xml_file = example.fullpath("musicxml/ex3.xml")


print("------- input from partitura")
myscore = partitura_xml_import(my_xml_file, show=True)
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
