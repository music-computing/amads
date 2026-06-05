"""
Implementation of the trim() function, which removes leading silence, from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 93

"""

from typing import cast

from amads.core.basics import Part, Score


def trim(score: Score) -> Score:
    """
    Removes all leading silence from a given score.

    trim() returns a flattened score with the first note starting at time 0.0.

    Parameters
    ----------
    score: Score
        The score that is to be trimmed.

    Returns
    -------
    Score
        A flattened score with the first note starting at 0.0. The original score is
        returned if it is already flat and its first note starts at 0.0; otherwise,
        a time-shifted flat copy is returned.
    """
    # Make sure the score is flat:
    flat = score
    if not score.is_flat():
        flat = score.flatten()

    # 2. Find earliest note
    SENTINAL = 1.0e10
    earliest = SENTINAL
    for part in flat.find_all(Part):
        part = cast(Part, part)
        if len(part.content) > 0:
            earliest = min(earliest, part.content[0].onset)

    # 2a. If it's empty, return the original or possibly flattened copy:
    if earliest == SENTINAL:
        return flat

    # 3. Shift the score by -earliest to make it start at time
    if flat == score:
        flat = score.copy()  # already know it is flat, so just copy it
    return flat.time_shift(-earliest, content_only=True)  # type: ignore
