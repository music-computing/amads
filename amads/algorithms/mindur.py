"""impose_mindur expands the duration of short notes to a minimum,
pushing subsequent onset times ahead.

The algorithm and behavior is tricky: The goal is to give some "room" to
grace notes so they are visible and audible when displayed or played as MIDI.

Since it is MIDI oriented and notes can be shifted around, this function
only manipulates flat scores.

For each part, scan across the part and process one note at a time. If a note
A with offset A_end has a duration < minimum_duration, extend its duration.
For any future notes with onsets between A_end - 1e-6 and
A_end + minimum_duration, adjust the note offsets to A_end + minimum_duration
(but keep their offsets). Some notes in the future will get negative durations,
but when they are processed, this will be fixed.
"""

from typing import cast

from amads.core.basics import Part, Score


def impose_mindur(score: Score, minimum_duration: float) -> Score:
    """Expand the duration of short notes to minimum_duration.

    If necessary, onsets of notes that start after short notes will
    be shifted so there is no overlap. Typically, this means a
    zero-duration grace note followed by a longer note will be
    transformed into a short grace note *followed* by the longer note.
    Offset times are preserved except when that would cause a note
    to be shorter than minimum_duration.

    Parameters
    ----------
    score: Score
        The score to be altered.
    minimum_duration: float
        The shortest duration after altering the score.

    Returns
    -------
    Score
        A newly constructed flat Score with minimum duration imposed.
        The input Score is unaltered.
    """

    result = score.flatten()  # copy and flatten the input
    # make sure result has same units as score
    if score.units_are_seconds != result.units_are_seconds:
        if score.units_are_seconds:
            result.convert_to_seconds()
        else:
            result.convert_to_quarters()

    for part in cast(list[Part], result.list_all(Part)):
        notes = part.content
        for i, note in enumerate(notes):
            if note.duration < minimum_duration:
                original_offset = note.offset
                note.duration = minimum_duration
                new_offset = note.offset
                print(f"  final for lengthened note {note}")
                # move all notes between original_offset and new_offset to
                # begin at new_offset
                j = i + 1
                while j < len(notes) and notes[j].onset < new_offset:
                    if notes[j].onset > original_offset - 0.001:
                        offset_j = notes[j].offset
                        notes[j].onset = new_offset
                        notes[j].duration = offset_j - new_offset  # keep offset
                        print(
                            f"    notes[{j}] {notes[j]}, "
                            f"onset {new_offset}, offset {notes[j].offset}, "
                            f"dur {notes[j].duration}"
                        )
            else:
                print(f"  final note not lengthened {note}")
    return result
