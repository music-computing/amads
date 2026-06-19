"""
Implementation of the quantize() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 85

"""

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

    This function flattens the input score and
    returns a new flattened score that has been quantized.

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

    # 1. Create a flattened copy of the score
    flat_score = score.flatten()

    # 2. Filter out short notes if a filter threshold is provided
    if filter_divisions is not None:
        threshold = 1.0 / filter_divisions
        notes_to_remove = []
        for note in flat_score.find_all(Note):
            if note.duration < threshold:
                notes_to_remove.append(note)

        for note in notes_to_remove:
            if note.parent:
                note.parent.remove(note)

    # 3. Quantize the score using the built-in method
    flat_score.quantize(onset_divisions, dur_divisions, filter)

    return flat_score
