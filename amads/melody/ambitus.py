__author__ = "Yiwen Zhao"

import numpy as np
from ..core.basics import Score, Note

def calculate_ambitus(score: Score) -> int:
    """
    Calculate the melodic range (ambitus) in semitones of a Score object.

    Parameters
    ----------
    score : Score
        A Score object containing Parts, Staves, and Notes.

    Returns
    -------
    tuple
        A tuple containing the melodic range in semitones, 
        the name of the lowest pitch, and the name of the highest pitch.

    Examples
    --------
    >>> ambitus(score)
    (7, 'C4', 'G4')  # The range is 7 semitones from C4 to G4
    """
    pitches = [note.keynum for note in score.find_all(Note)]

    if not pitches:
        return 0  # No notes found, return 0 as ambitus
    
    melodic_range = max(pitches) - min(pitches)

    return melodic_range
