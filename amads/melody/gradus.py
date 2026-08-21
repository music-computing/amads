"""
Calculates the degree of melodiousness (gradus suavitatis), proposed by Euler.

Made some slight touchups to Yiwen Zhao's original function to bring it into
our newer AMADS design.

Ports the `gradus` function from Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 63.
"""

__author__ = "Yiwen Zhao"

from amads.core.basics import Note, Score

_gradus_interval_ratios = [
    (1, 1),  # unison
    (16, 15),  # minor second
    (9, 8),  # major second
    (6, 5),  # minor third
    (5, 4),  # major third
    (4, 3),  # perfect fourth
    (45, 32),  # tritone
    (3, 2),  # perfect fifth
    (8, 5),  # minor sixth
    (5, 3),  # major sixth
    (9, 5),  # minor seventh
    (15, 8),  # major seventh
    (2, 1),  # octave
]


def _prime_factors(n: int) -> list[int]:
    """Helper function to get prime factors of a number."""
    factors = []
    d = 2
    while n > 1:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
        if d * d > n:
            if n > 1:
                factors.append(n)
            break
    return factors


def _suavitatis(ratio: tuple[int, int]) -> int:
    """
    Calculates Euler's suavitatis metric according to a given interval ratio

    Parameters
    ----------
    ratio: tuple[int, int]
        Given interval ratio as specified in Euler's original paper

    Returns
    -------
    int
        Suavitatis value

    """
    numerator, denominator = ratio
    factors = _prime_factors(numerator * denominator)
    return sum(factor - 1 for factor in factors) + 1


def gradus(score: Score) -> float | None:
    """
    Calculate the degree of melodiousness (gradus suavitatis) according to Euler (1739).

    The gradus suavitatis measures melodic pleasantness based on the simplicity of
    frequency ratios between successive notes. Lower values indicate higher melodiousness.
    The calculation decomposes intervals into frequency ratios and analyzes their prime factors.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.

    Returns
    -------
    float
        The degree of melodiousness value. Lower values indicate higher melodiousness.
        Returns 0 for empty scores or single notes.

    References
    ----------
    .. [1] Euler, L. (1739). Tentamen novae theoriae musicae.
    .. [2] Leman, M. (1995). Music and schema theory: Cognitive foundations of
           systematic musicology. Berlin: Springer.
    """

    current_note_iter = score.find_all(Note)
    next_note_iter = score.find_all(Note)
    if next(next_note_iter, None) is None:
        return None
    gradus_sum = 0
    num_intervals = 0
    for current_note, next_note in zip(current_note_iter, next_note_iter):
        interval = next_note.midi_num - current_note.midi_num
        # interval processed to be within an octave and always positive.
        processed_interval = abs(interval) % 12
        gradus_sum += _suavitatis(_gradus_interval_ratios[processed_interval])
        num_intervals += 1

    if num_intervals > 0:
        # essentially returns the mean gradus sum
        return gradus_sum / num_intervals
    else:
        return None
