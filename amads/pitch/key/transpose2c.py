"""
transposes a given score to C after we've attained
the maximum correlation key of the score from
the krumhansl-kessler algorithm (kkcc with default parameters).

<small>**Author**: Tai Nakamura, Di Wang</small>

Reference
---------
https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 94.
"""

from amads.core.basics import Note, Score
from amads.pitch.key.kkcc import kkcc


def transpose2c(score: Score, profile_name: str = "KRUMHANSL-KESSLER") -> Score:
    """
    Return a copy of `score` transposed to C major/minor using
    [kkcc][amads.pitch.key.kkcc.kkcc].

    This is an implementation of the transpose2c function in the Matlab
    MIDI Toolbox.

    Parameters
    ----------
    score : Score
        Score to analyze and transpose.
    profile_name : str
        Key-profile name for [kkcc][amads.pitch.key.kkcc.kkcc]. One of
        ``"KRUMHANSL-KESSLER"``, ``"TEMPERLEY"``, ``"ALBRECHT-SHANAHAN"``.

    Returns
    -------
    Score
        A new score whose tonic is C. Empty input yields an empty copy.

    Examples
    --------
    A G major scale is estimated as G and transposed down a fifth to C:

    >>> score = Score.from_melody(
    ...     [67, 69, 71, 72, 74, 76, 78, 79],  # G4 to G5
    ... )
    >>> out = transpose2c(score)
    >>> notes = out.get_sorted_notes()
    >>> notes[0].midi_num  # G4 becomes C4
    60
    >>> notes[-1].midi_num  # G5 becomes C5
    72
    >>> score.get_sorted_notes()[0].midi_num  # input is unchanged
    67

    See Also
    --------
    - [kkcc][amads.pitch.key.kkcc.kkcc] : Key correlations used to choose the tonic.
    - [EventGroup.pitch_shift][amads.core.basics.EventGroup.pitch_shift] :
      In-place pitch shift of every note-head, including ties.
    """
    # kkcc fails when an empty score is supplied.
    # However, an empty score transposes to an empty score regardless of what key
    # you're transposing to, so we treat this as a special case here.
    if next(score.find_all(Note), None) is None:
        return score.copy()
    corr_vals = kkcc(score, profile_name)

    key_idx = corr_vals.index(max(corr_vals)) % 12
    return score.copy().pitch_shift(-key_idx)
