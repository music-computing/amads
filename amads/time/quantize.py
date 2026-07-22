"""
Implementation of the quantize() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 85

"""

import copy

from amads.core.basics import Note, Score


def quantize(
    score: Score,
    onset_divisions: int = 8,
    dur_divisions: int | None = None,
    filter_divisions: int | None = None,
    filter: bool = False,
) -> Score:
    """
    Quantize note events in a score according to onset resolution,
    duration resolution, and optionally filter out short note events.

    This function returns a new flattened score that has been quantized.
    Tied note chains are handled correctly: each note's onset is preserved
    and the chain is trimmed or adjusted as needed before merging.

    This is an implementation of the quantize function in the Matlab MIDI Toolbox.

    Note: the Matlab MIDI Toolbox default for duration resolution is double
    the onset resolution. For compatibility, explicitly
    pass ``dur_divisions = onset_divisions // 2``.

    Parameters
    ----------
    score : Score
        The input score to be quantized.
    onset_divisions : int
        The grid resolution for onsets, in divisions per quarter note.
        Default is 8.
    dur_divisions : int or None
        The grid resolution for durations. If not provided, defaults to
        onset_divisions.
    filter_divisions : int or None
        If provided, any note with a duration strictly less than
        (1 / filter_divisions) quarters will be removed before quantization.
    filter : bool
        If True, remove all zero-duration notes after quantization.
        Default is False.

    Returns
    -------
    Score
        A new, flattened, and quantized score.
    """

    # deep copy so tied chains are intact when quantize runs
    score_copy = copy.deepcopy(score)

    if filter_divisions is not None:
        threshold = 1.0 / filter_divisions
        notes_to_remove = [
            n for n in score_copy.find_all(Note) if n.duration < threshold
        ]
        for note in notes_to_remove:
            if note.parent:
                note.parent.remove(note)

    score_copy.quantize(onset_divisions, dur_divisions, filter)

    return score_copy.flatten()
