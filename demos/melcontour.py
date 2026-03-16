import matplotlib.pyplot as plt

from amads.all import partitura_midi_import, pianoroll
from amads.melody.contour.melcontour import autocorrelatecontour, melodySamplingContour
from amads.music import example

my_midi_file = example.fullpath("midi/tones.mid")


print("------- input from partitura")
myscore = partitura_midi_import(my_midi_file, ptprint=False)
print("------- finished input from partitura")

print("------- Executing melcontour")
# we are calling melcontour with a resolution of 0.25 beats per sample tick
contour = melodySamplingContour(myscore, 0.40)
print(contour)

print("------- Executing autocorrelatecontour")
# Note that autocorrelate contour
autocorrelation = autocorrelatecontour(contour)
print(autocorrelation)
assert len(autocorrelation) == 2 * len(contour) - 1


def hacky_plot(correspondences, mode="ac"):
    """
    very hacky plot function. Not much to be said except:
    (1) mode "c" plots the contour as obtained by melcontour
    onto the original score
    (2) mode "ac" plots the autocorrelation of the melody contour
    independent of the original score
    """
    if mode == "ac":
        # autocorrelation plot
        fig, ax = plt.subplots()
        lag_tuple, correlation_tuple = zip(*correspondences)
        plt.plot(
            lag_tuple,
            correlation_tuple,
            color="green",
            marker="o",
            label="autocorrelation values",
        )
        return
    if mode == "c":
        # sample contour plot
        pianoroll(myscore)
        sample_tick_tuple, pitch_tuple = zip(*correspondences)
        plt.plot(
            sample_tick_tuple,
            pitch_tuple,
            color="purple",
            marker="o",
            label="contour samples",
        )
        return
    raise ValueError("wrong mode, probably not supported yet!")


hacky_plot(contour, "c")

plt.legend(loc="best")
plt.show()
