"""
Melodic accent salience according to Thomassen's model.

Ports the `mobility` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 74-75.
"""

import numpy as np
import math
from typing import cast, Optional

from amads.core.basics import Note, Score
from itertools import accumulate


def mobility(score: Score) -> Optional[Score]:
    """
    Calculate the mobility measure for each tone in a melody (von Hippel, 2000).

    Mobility describes why melodies change direction after large skips by observing
    that they would otherwise run out of the comfortable melodic range. It uses
    lag-one autocorrelation between successive pitch heights.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.

    Returns
    -------
    Optional[Score]
        score with ties stripped where each note is annotated with a
        mobility value (in float) in the attribute "mobility"
        None if score is not monophonic or there are not enough notes
        in the score to run mobility

    References
    ----------
    .. [1] von Hippel, P. (2000). Redefining pitch proximity: Tessitura and 
           mobility as constraints on melodic interval size. Music Perception, 
           17 (3), 315-327. 
    """
    # hack to check if score is empty
    if not score.ismonophonic():
        return None
    pitches = [note.key_num for note in score.get_sorted_notes()]
    if len(pitches) < 3:
        return None
    means = [sum / (num + 1) for num, sum in enumerate(accumulate(pitches))]
    # list of pitch differences to running mean, added 0 at the beginning for
    # convenience when slicing lists for correlation coefficients
    pitch_diffs = [0]
    pitch_diffs.extend((pitch - mean for pitch, mean in zip(pitches, means)))

    current_corrcoef = 0.0
    mobility_vals = [0.0, 0.0]
    for idx in range(1, len(pitches) - 1):
        assert not math.isnan(current_corrcoef)
        mobility_val = abs(current_corrcoef * (pitches[idx + 1] - means[idx]))
        mobility_vals.append(mobility_val)
        # prepare next corrcoef by slicing the pitch diff lists for corrcoef
        prev_list = pitch_diffs[:idx + 2]
        next_list = pitch_diffs[1:idx + 2]
        next_list.append(pitch_diffs[idx + 1])
        slice_list = [prev_list, next_list]
        slice_array = np.array(slice_list)
        coef_array = np.corrcoef(slice_array)
        current_corrcoef = coef_array[0, 1]

    # annotate a score
    annotated_score = cast(Score, score.merge_tied_notes())
    annotate_str = "mobility"
    for note, mobility_val in zip(annotated_score.find_all(Note), mobility_vals):
        note.set(annotate_str, mobility_val)

    return annotated_score
