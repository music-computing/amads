"""
transposes a given score to C after we've attained
the maximum correlation key of the score from
the krumhansl-kessler algorithm (kkcc with default parameters).

Author(s):
Tai Nakamura
Di Wang (diwang2)

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=93
"""

from ..core.basics import Note, Score
from ..core.pitch import Pitch
from .kkcc import kkcc


def transpose2c(score: Score, profile_name: str = "KRUMHANSL-KESSLER") -> Score:
    """
    returns a copy of score transposed to C-major/minor with the key from the
    krumhansl-kessler algorithm (kkcc with default parameters).

    Parameters
    ----------
    score (Score): The musical score to analyze.
    profile_name (str): string argument denoting the relevant miditoolbox
    string option for kkcc

    Returns
    -------
    Score:
        a copy of the input score transposed to C-major/minor
    """
    # a point of optimization is to check for empty case of the score...
    # this is very hacky...
    if next(score.find_all(Note), None) is None:
        return score.deepcopy()
    corr_vals = kkcc(score, profile_name)

    key_idx = corr_vals.index(max(corr_vals)) % 12
    # TODO: please change this to shift later on when shift is implemented
    # i.e. return shift(score, "pitch", -key_idx)
    score_copy = score.deepcopy()
    for note in score_copy.find_all(Note):
        keynum, alt = note.pitch.as_tuple()
        # since Pitches with same alt and keynum are equivalent
        # and Pitches themselves are considered "immutable" in
        # our representation scheme
        note.pitch = Pitch(keynum - key_idx, alt)
    return score_copy
