# partitura_xml_test.py - some tests for partitura_xml_import.py

from amads.all import partitura_xml_import
from amads.music import example

my_xml_file = None  # defaults to pt.EXAMPLE_MUSICXML
# my_xml_file = "../music/xml/ex1.xml"
# my_xml_file = "../music/xml/ex2.xml"
my_xml_file = example.fullpath("xml/ex3.xml")


print("------- input from partitura")
myscore = partitura_xml_import(my_xml_file, ptprint=True)
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
