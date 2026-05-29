from amads.io.pianoroll import pianoroll
from amads.io.pm_midi_import import pretty_midi_import
from amads.melody.contour.combcontour import get_pitch_comparison_contour_matrix
from amads.music import example

my_midi_file = example.fullpath("midi/tones.mid")

print("------- input from partitura")
myscore = pretty_midi_import(my_midi_file, format="midi")
print("------- finished input from partitura")

fig = pianoroll(myscore)

print("------- Executing combcontour")
contour_mtx = get_pitch_comparison_contour_matrix(myscore)

print(contour_mtx)