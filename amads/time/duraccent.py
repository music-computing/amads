"""
Calculate Parncutt's durational accent (1994) for either a note or a Score.

Based on Matlab MIDI Toolbox implementation.

References
----------
- https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=58
- Parncutt, R. (1994). A perceptual model of pulse salience and
  metrical accent in musical rhythms. *Music Perception*. 11(4), 409-464.
"""

import math

from amads.core.basics import Note, Score

def duraccent_note(note: Note, tau: float = 0.5, accent_index: int = 2) -> float:
    """
    Calculate Parncutt's durational accent (1994) for a note.

    Based on Matlab MIDI Toolbox implementation.

    Parameters
    ----------
    note : Note
        The note for which to calculate the durational accent.
    tau : float
        Saturation duration (optional, default duration of 0.5)
    accent_index: int
        Minimum discriminable duration (default of 2)

    Returns
    -------
    float
        The durational accent value.
    """
    accent = 1 - math.exp(-note.duration / tau) ** accent_index
    return accent


def duraccent(score: Score, tau: float = 0.5, accent_index: int = 2) -> Score:
    """
    Calculate Parncutt's durational accent (1994) for a score.

    Based on Matlab MIDI Toolbox implementation.

    Parameters
    ----------
    score : Score
        Score of notes for which to calculate the durational accents.
    tau : float
        Saturation duration (optional, default duration of 0.5)
    accent_index: int
        Minimum discriminable duration (default of 2)

    Returns
    -------
    Score
        A flattened, annotated score with the duration accents under the
        attribute name "accent_val".
    """
    if not score.has_instanceof(Note):
        raise ValueError("nonempty scores only")
    flattened_score = score.flatten()
    note_iter = flattened_score.find_all(Note)
    for note in note_iter:
        accent = 1 - math.exp(-note.duration / tau) ** accent_index
        note.accent_val = accent
    return flattened_score

