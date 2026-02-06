"""
transposes a given score to C after we've attained
the maximum correlation key of the score from
the krumhansl-kessler algorithm (kkcc with default parameters).

<small>**Author**: Tai Nakamura, Di Wang</small>

Reference
---------
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=93
"""

from amads.core.basics import Note, Score
from amads.core.pitch import Pitch
from amads.pitch.key.kkcc import kkcc


def transpose2c(score: Score, profile_name: str = "KRUMHANSL-KESSLER") -> Score:
    """
    returns a copy of score transposed to C-major/minor with the key from the
    original krumhansl-kessler algorithm (kkcc with default parameters).

    Parameters
    ----------
    score : Score
        The musical score to analyze.
    profile_name : str
        string argument denoting the relevant profile for key estimation

    Returns
    -------
    Score
        a copy of the input score transposed to C-major/minor
    """
    # kkcc fails when an empty score is supplied.
    # However, an empty score transposes to an empty score regardless of what key
    # you're transposing to, so we treat this as a special case here.
    if next(score.find_all(Note), None) is None:
        return score.deepcopy()
    corr_vals = kkcc(score, profile_name)

    key_idx = corr_vals.index(max(corr_vals)) % 12
    # TODO: need to use pitch_shift which is to be implemented in Score
    score_copy = score.deepcopy()
    for note in score_copy.find_all(Note):
        keynum, alt = note.pitch.as_tuple()
        # since Pitches with same alt and keynum are equivalent
        # and Pitches themselves are considered "immutable" in
        # our representation scheme
        note.pitch = Pitch(keynum - key_idx, alt)
    return score_copy
