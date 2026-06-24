__author__ = "Yiwen Zhao"

import numpy as np
from ..core.basics import Score, Note

def calculate_tessitura(score: Score) -> list[float]:
    """
    Calculate the tessitura based on the standard deviation of pitch height.

    Parameters
    ----------
    score : Score
        A Score object containing Note objects.

    Returns
    -------
    list
        A list of tessitura values for each tone in the score.

    Examples
    --------
    >>> calculate_tessitura(score)
    [-1.224, 0.0, 1.224]  # Example output based on the standard deviation
    """
    pitches = [note.keynum for note in score.find_all(Note)]
    median_pitch = np.median(pitches)
    std_dev = np.std(pitches)

    tessitura_values = [
        float((pitch - median_pitch) / std_dev) if std_dev > 0 else 0.0
        for pitch in pitches
    ]

    return tessitura_values
