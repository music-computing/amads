"""
In this directory:
- `skyline` returns a score with the highest sounding notes at any given point.
- [this module] `extreme` is similar, and designed to match the MIDI toolkit as exactly as possible.
- `envelope` is a variant on skyline that could be said to constitute a "smoothed" form,
    and (currently) operates on pitch-onset pairs only (analysis only, no score return).
- `superlative` is the most reductive, returning only the *single* highest/lowest/sharpest/flattest value.

This module implements the extreme() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 61

<small>**Author**: Arnav Sayooj</small>
"""

__author__ = "Arnav Sayooj"


from amads.core.basics import Note, Score


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
            if (
                method == "high"
                and note.pitch.midi_num > current.pitch.midi_num
            ):
                onset_note[onset] = note
            elif (
                method == "low" and note.pitch.midi_num < current.pitch.midi_num
            ):
                onset_note[onset] = note

    # 3. Replace part content with only the extreme notes
    part = flat_score.content[0]
    part.content = sorted(onset_note.values(), key=lambda n: n.onset)
    for note in part.content:
        note.parent = part

    return flat_score
