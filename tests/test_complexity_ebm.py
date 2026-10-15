import math

from amads.core.basics import Score
from amads.melody.complexity_ebm import ComplexityEBMOption, complexity_ebm
from tests.matlab_crosstesting_utils import (
    load_json_results,
    matlab_sarabande_test_score,
)

_pitch_opt = ComplexityEBMOption.PITCH
_rhythm_opt = ComplexityEBMOption.RHYTHM
_mix_opt = ComplexityEBMOption.OPTIMAL_MIX


def test_empty_score():
    """
    complexity_ebm with empty melody
    """
    empty_score = Score()
    assert complexity_ebm(empty_score) is None


def test_single_note():
    """
    complexity_ebm with a score containing a single note
    """
    single_note_score = Score.from_melody(pitches=[60], durations=[1.0])
    assert complexity_ebm(single_note_score) is None


# ! finish these test cases!
def test_simple_melodies():
    """
    complexity_ebm with simple melody
    """

    example_score = Score.from_melody([60, 64, 67])
    example_complexity = complexity_ebm(example_score, _pitch_opt)
    desired_example_complexity = 3.7082773181022706
    assert math.isclose(example_complexity, desired_example_complexity)

    pitches = [60, 64, 67, 65]
    durations = [1.0, 0.5, 1.0, 0.5]
    score = Score.from_melody(pitches=pitches, durations=durations)

    desired_pitch_complexity = 4.1318807035942955
    desired_rhythm_complexity = 4.014230767406113
    desired_optimal_complexity = 4.005016476981945

    pitch_complexity = complexity_ebm(score=score, method=_pitch_opt)
    rhythm_complexity = complexity_ebm(score=score, method=_rhythm_opt)
    optimal_complexity = complexity_ebm(score=score, method=_mix_opt)
    assert math.isclose(pitch_complexity, desired_pitch_complexity)
    assert math.isclose(rhythm_complexity, desired_rhythm_complexity)
    assert math.isclose(optimal_complexity, desired_optimal_complexity)


def test_complex_chromatic_melody():
    """
    complexity_ebm with a (slightly) complex chromatic melody.
    """
    pitches = [60, 61, 63, 67, 65]
    durations = [1.0, 0.5, 0.25, 1.5, 0.75]
    complex_score = Score.from_melody(pitches=pitches, durations=durations)
    complexity = complexity_ebm(score=complex_score, method=_mix_opt)
    desired_complexity = 4.501021140129757
    assert math.isclose(complexity, desired_complexity)


def test_midi_sarabande():
    test_result = complexity_ebm(matlab_sarabande_test_score)
    desired_result = load_json_results()["complebm"]
    assert math.isclose(test_result, desired_result)


if __name__ == "__main__":
    test_empty_score()
    test_single_note()
    test_simple_melodies()
    test_complex_chromatic_melody()
    test_midi_sarabande()
