"""
Implementation of the dropshortnotes() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 57

"""

from amads.core.basics import Note, Score


def dropshortnotes(score: Score, threshold: float) -> Score:
    """
    Removes notes whose total tied duration is less than or equal to a threshold.

    The score is first flattened, which merges any tied note chains into single
    notes. Notes whose duration is then less than or equal to ``threshold`` are
    removed.

    Note: this is not an exact port of the MIDI Toolbox function, which uses
    strictly less than for the threshold comparison. This implementation uses
    less than or equal to.

    Parameters
    ----------
    score : Score
        The score to filter.
    threshold : float
        Duration threshold in beats. Notes with ``tied_duration <= threshold``
        are removed. Use 0 to drop only zero-duration grace notes.

    Returns
    -------
    Score
        A new, flattened score with short notes removed.

    Notes
    -----
    To drop notes strictly shorter than a duration *d*, it is recommended to first quantize the score
    to an appropriate sub-multiple of *d* so that durations slightly less than
    *d* round up to *d*. Then call ``dropshortnotes`` with ``threshold = d -
    1.0e-6``.
    """
    # 1. Flatten the score
    flat_score = score.flatten()

    # 2. Remove notes whose duration is at or below the threshold
    for part in flat_score.content:
        i = 0
        while i < len(part.content):
            event = part.content[i]
            if isinstance(event, Note) and event.tied_duration <= threshold:
                event.parent.remove(event)  # doesn't increment i
            else:
                i += 1
    return flat_score
