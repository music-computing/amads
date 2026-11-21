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
# we are calling melcontour with a resolution of 0.4 beats per sample
contour = melodySamplingContour(myscore, 0.40, "abs")
print(contour)

print("------- Executing autocorrelatecontour")
# Same as last call, except we take the resulting output's autocorrelation
autocorrelation = melodySamplingCorrelation(myscore, 0.40, "abs")
print(autocorrelation)
assert len(autocorrelation) == 2 * len(contour) - 1

none_autocorrelation = melodySamplingCorrelation(myscore, 0.40)
assert none_autocorrelation is None
