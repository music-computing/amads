"""
Provides the function `ismonophonic`
"""

from ..core.basics import Note, Score


def _ismonophonic(notes: list[Note]):
    """
    Returns if a list of notes is monophonic

    A monophonic list of notes has no overlapping notes (e.g. chords)
    Serves as a helper function for `ismonophonic`

    Args:
        note (list[Note]): The list of notes to analyze

    Returns:
        bool: True if the list of notes is monophonic
    """
    prev = None
    for note in notes:
        if prev:
            # 0.01 is to prevent precision errors when comparing floats
            if note.onset - prev.offset < -0.01:
                return False
        prev = note
    return True


def ismonophonic(score: Score):
    """
    Returns if a musical score is monophonic

    A monophonic score has no overlapping notes (e.g. chords)

    Args:
        score (Score): The musical score to analyze

    Returns:
        bool: True if the score is monophonic
    """
    for container in score.note_containers():
        notes = container.find_all(Note)
        if not _ismonophonic(notes):
            return False
    return True
