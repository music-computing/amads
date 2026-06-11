from amads.core.basics import Score
from amads.melody.compl_ebm import ComplEBMOption, compl_ebm

_pitch_opt = ComplEBMOption.PITCH
_rhythm_opt = ComplEBMOption.RHYTHM
_mix_opt = ComplEBMOption.OPTIMAL_MIX


def test_simple_melody():
    """
    complebm with simple melody
    """
    pitches = [60, 64, 67, 65]
    durations = [1.0, 0.5, 1.0, 0.5]
    score = Score.from_melody(pitches=pitches, durations=durations)

    print("Pitch complexity:", compl_ebm(score, _pitch_opt))
    print("Rhythm complexity:", compl_ebm(score, _rhythm_opt))
    print("Overall complexity:", compl_ebm(score, _mix_opt))
    return


def test_empty_score():
    """
    complebm with empty melody
    """
    empty_score = Score()
    print("Empty score complexity:", compl_ebm(empty_score))


def test_single_note():
    """
    complebm with a score containing a single note
    """
    single_note_score = Score.from_melody(pitches=[60], durations=[1.0])
    print("Single note complexity:", compl_ebm(single_note_score))


def test_complex_chromatic_melody():
    """
    complebm with a (slightly) complex chromatic melody.
    """
    pitches = [60, 61, 63, 67, 65]
    durations = [1.0, 0.5, 0.25, 1.5, 0.75]
    complex_score = Score.from_melody(pitches=pitches, durations=durations)
    print("Complex melody complexity:",
          compl_ebm(complex_score, _mix_opt))

def test_coefficients():
    """
    this is a test script written for the sole purpose of figuring out what the
    coefficients in the matlab implementation coincide with in the amads
    implementation of compl_ebm before recent changes.
    """
    pitch_coefs_matlab = [-0.2407, 0.3, 1, 0.8, 0.9040]
    