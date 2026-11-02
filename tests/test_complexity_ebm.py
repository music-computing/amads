from amads.core.basics import Score
from amads.melody.complexity_ebm import ComplexityEBMOption, complexity_ebm

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
def test_simple_melody():
    """
    complexity_ebm with simple melody
    """
    pitches = [60, 64, 67, 65]
    durations = [1.0, 0.5, 1.0, 0.5]
    score = Score.from_melody(pitches=pitches, durations=durations)

    print("Pitch complexity:", complexity_ebm(score, _pitch_opt))
    print("Rhythm complexity:", complexity_ebm(score, _rhythm_opt))
    print("Overall complexity:", complexity_ebm(score, _mix_opt))
    return


def test_complex_chromatic_melody():
    """
    complexity_ebm with a (slightly) complex chromatic melody.
    """
    pitches = [60, 61, 63, 67, 65]
    durations = [1.0, 0.5, 0.25, 1.5, 0.75]
    complex_score = Score.from_melody(pitches=pitches, durations=durations)
    complexity_ebm(complex_score, _mix_opt)


if __name__ == "__main__":
    test_simple_melody()
