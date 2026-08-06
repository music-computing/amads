"""
Implementation of the dropshortnotes() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 57

<small>**Author**: Arnav Sayooj</small>
"""

from typing import cast

from amads.core.basics import Note, Score


def dropshortnotes(score: Score, threshold: float) -> Score:
    """
    Removes notes whose total tied duration is strictly less than a threshold.

    For each note that starts a tied chain, the total tied duration is compared
    against the threshold. If the total duration is strictly less than the
    threshold, all notes in the chain are removed.

    Zero is a special case: passing `threshold = 0` removes only notes whose
    tied duration is exactly zero.

    Parameters
    ----------
    score : Score
        The score to filter.
    threshold : float
        Duration threshold in beats. Notes with (tied) `duration < threshold`
        are removed. Pass `0` to remove only zero-duration grace notes.

    Returns
    -------
    Score
        A copy of the score with short notes removed.
    """
    # 1. Copy the score to avoid modifying the original
    score_copy = cast(Score, score.copy())
    all_notes = list(score_copy.find_all(Note))

    # 2. Find notes to remove, starting only from chain heads
    tied_to_ids = {id(n.tie) for n in all_notes if n.tie}

    to_remove = []
    for note in all_notes:
        if id(note) in tied_to_ids:
            continue
        if threshold == 0:
            should_drop = note.duration == 0
        else:
            should_drop = note.duration < threshold
        if should_drop:
            node = note
            while isinstance(node, Note):
                to_remove.append(node)
                if node.tie is None:
                    break
                node = node.tie

    # 3. Remove all collected notes
    for note in to_remove:
        if note.parent:
            note.parent.remove(note)

    return score_copy
