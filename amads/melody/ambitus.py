from amads.core.basics import Note, Score

__author__ = "Yiwen Zhao"


def ambitus(score: Score) -> int | None:
    """
    Returns the pitch range (ambitus) in semitones (or midi keynums)
    of a Score object.

    Ports the "ambitus" function from miditoolbox.

    Parameters
    ----------
    score : Score
        A Score object containing Parts, Staves, and Notes.

    Returns
    -------
    int | None
        None if score is empty.
        Otherwise, the difference between the largest pitch and the smallest
        pitch (in semitones specified by midi keynums).
    """
    if next(score.find_all(Note), None) is None:
        return None
    min_pitch = min(note.midi_num for note in score.find_all(Note))
    max_pitch = max(note.midi_num for note in score.find_all(Note))

    return max_pitch - min_pitch
