from amads.io.pm_midi_import import pretty_midi_import
from amads.melody.contour.melcontour import (
    melodySamplingContour,
    melodySamplingCorrelation,
)
from amads.music import example

my_midi_file = example.fullpath("midi/tones.mid")


print("------- input from partitura")
myscore = pretty_midi_import(my_midi_file, format="midi")
print("------- finished input from partitura")

print("------- Executing melcontour")
# we are calling melcontour with a resolution of 0.25 beats per sample tick
contour = melodySamplingContour(myscore, 0.40)
print(contour)

print("------- Executing autocorrelatecontour")
# Note that autocorrelate contour
autocorrelation = melodySamplingCorrelation(myscore, 0.40)
print(autocorrelation)
assert len(autocorrelation) == 2 * len(contour) - 1
