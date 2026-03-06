
import json

from amads.io.pm_midi_import import pretty_midi_import
from amads.music import example
from amads.core.distribution import Distribution
from amads.pitch.pcdist1 import pitch_class_distribution_1
from amads.time.durdist1 import duration_distribution_1



def test_against_matlab_results():
    # import sarabande.midi
    score = pretty_midi_import( \
                example.fullpath("midi/sarabande.mid"), "midi",\
                flatten=True)  # show=True to see PrettyMIDI data

    # import json test results that were exported from the script
    json_results = None
    with open("tests/matlab_results_sarabande.json") as json_file:
        json_results = json.load(json_file)

    # list pairs of correspondences between the distribution functions
    # and their matlab couterparts
    dist_function_correspondences = [(pitch_class_distribution_1, 'pcdist1'), (duration_distribution_1, 'durdist1')]
    for dist_func, matlab_func_string in dist_function_correspondences:
        result = dist_func(score)
        assert(isinstance(result, Distribution))
        assert(result.data == json_results[matlab_func_string])
