"""
Implementation of the trim() function, which removes leading silence, from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 93

"""

from amads.core.basics import Score


def trim(score: Score) -> Score:
    """Remove leading silence from a score.

    Always returns a flattened copy. The first note starts at time 0.0.
    The original ``score`` is not modified. The time framework
    (``time_map`` and ``time_signatures``) shifts with the notes.

    Parameters
    ----------
    score : Score
        The score that is to be trimmed.

    Returns
    -------
    Score
        A flattened score with the first note at 0.0. If there are no
        notes, or the earliest note is already at 0.0, the flattened
        copy is returned without a further shift.

    Examples
    --------
    >>> from amads.algorithms.trim import trim
    >>> from amads.core.basics import Note, Part, Score
    >>> score = Score(Part(Note(onset=3.0, duration=1.0, pitch="C4")))
    >>> trimmed = trim(score)
    >>> trimmed.get_sorted_notes()[0].onset
    0.0
    >>> score.get_sorted_notes()[0].onset  # original unchanged
    3.0
    """
    flat = score.flatten()  # flattened copy of the score
    notes = flat.get_sorted_notes()
    if len(notes) == 0:
        return flat
    earliest = notes[0].onset
    if earliest == 0.0:
        return flat
    return flat.time_shift(-earliest, content_only=True, shift_framework=True)
