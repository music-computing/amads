"""
Provides the function `ismonophonic`
"""

from ..core.basics import Note, Part, Score


def _ismonophonic(notes: list[Note]):
    """
    Returns if a list of notes is monophonic

    A monophonic list of notes has no overlapping notes (e.g. chords)
    Serves as a helper function for `ismonophonic` and
    `parts_are_monophonic`.

    Args:
        note (list[Note]): The list of notes to analyze

    Returns:
        bool: True if the list of notes is monophonic
    """
    prev = None
    notes = list(notes)
    # Sort the notes by start time
    notes.sort(key=lambda note: note.onset)
    # Check for overlaps
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
    return _ismonophonic(score.find_all(Note))


def parts_are_monophonic(score: Score):
    """
    Returns if all parts of a musical score are monophonic
    """
    for part in score.find_all(Part):
        if not _ismonophonic(part.find_all(Note)):
            return False
    return True
