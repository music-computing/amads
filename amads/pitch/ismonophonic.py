"""
Determine if a musical score or its parts are monophonic.
"""

from amads.core.basics import Note, Part, Score


def _ismonophonic(notes: list[Note]):
    """
    Determine if a list of notes is monophonic.

    A monophonic list of notes has no overlapping notes (e.g., chords).
    Serves as a helper function for `ismonophonic` and
    `parts_are_monophonic`.

    Parameters
    ----------
    notes : list of Note
        The list of notes to analyze.

    Returns
    -------
    bool
        True if the list of notes is monophonic, False otherwise.
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
    Determine if a musical score is monophonic.

    A monophonic score has no overlapping notes (e.g., chords).

    Parameters
    ----------
    score : Score
        The musical score to analyze.

    Returns
    -------
    bool
        True if the score is monophonic, False otherwise.
    """
    return _ismonophonic(score.find_all(Note))


def parts_are_monophonic(score: Score) -> bool:
    """
    Determine if all parts of a musical score are monophonic.

    A monophonic part has no overlapping notes (e.g., chords).

    Parameters
    ----------
    score : Score
        The musical score to analyze.

    Returns
    -------
    bool
        True if all parts are monophonic, False otherwise.
    """
    for part in score.find_all(Part):
        if not _ismonophonic(part.find_all(Note)):
            return False
    return True
