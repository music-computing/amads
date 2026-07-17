"""
Implementation of the extreme() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 61

"""

from amads.core.basics import Note, Part, Score


def extreme(score: Score, method: str = "high") -> Score:
    """
    Returns the extreme pitched note at each onset from a polyphonic score.

    For each unique onset time, only the highest or lowest pitched note
    is kept. All other notes at that onset are discarded.

    Parameters
    ----------
    score : Score
        The polyphonic score to process.
    method : str
        Either "high" (which is the default) to keep the highest pitched note at each
        onset, or "low" to keep the lowest.

    Returns
    -------
    Score
        A new, flattened score containing only the extreme pitched note
        at each onset.
    """
    method = method.lower()

    # 1. Flatten the score
    flat_score = score.flatten()
    notes = flat_score.get_sorted_notes()

    # 2. Group notes by onset and keep only the extreme pitch at each onset
    onset_note: dict[float, Note] = {}
    for note in notes:
        onset = note.onset
        if onset not in onset_note:
            onset_note[onset] = note
        else:
            current = onset_note[onset]
            if method == "high" and note.pitch.key_num > current.pitch.key_num:
                onset_note[onset] = note
            elif method == "low" and note.pitch.key_num < current.pitch.key_num:
                onset_note[onset] = note

    # 3. Build a new score with only the extreme notes
    result = Score()
    part = Part(parent=result)
    for note in sorted(onset_note.values(), key=lambda n: n.onset):
        Note(
            parent=part,
            onset=note.onset,
            duration=note.duration,
            pitch=note.pitch.key_num,
        )

    return result
