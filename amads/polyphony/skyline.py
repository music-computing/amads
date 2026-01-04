"""
Provides the `skyline` function
"""

from typing import List, Optional, cast

from amads.core.basics import Note, Part, Score


def skyline(score: Score, threshold: float = 0.1) -> Score:
    """
    Finds the skyline of a musical score.

    Filters a score, removing any note that is below another note.
    There are tricky edge cases:

    - A higher note can occur while a lower note is still sounding. The lower
      note is shortened to end at the onset of the upper note.
    - A higher note can follow a lower note very quickly: Rather than setting
      the lower note's duration to a very small value, the lower note is
      completely removed and ignored. The lower bound on duration is set by
      the `threshold` parameter.
    - A rolled chord with 10 notes starts at the bottom, and every 0.05
      quarter notes, a new note enters. So the previous rule applies to
      each note, making the top note is a full 0.45 quarters after the
      first one. Even in this case, the previous rule is applied repeatedly,
      leaving a gap (rest) of at least 0.45 quarters.
    - An upper note of a melody sustains in a legato fashion past the next,
      but lower, note of the melody. Although, musically, the upper note
      should be shortened and we should keep the lower note, the “skyline”
      concept says the top note has priority, so the lower note is ignored
      if the overlap is greater than `threshold`.
    - It is common to have melodies in lower voices or in MIDI arrangements
      to have very high accompaniment notes in a non-melodic track. This
      algorithm just fails to find the melody in those cases.

    Parameters
    ----------
    score : Score
        The musical score to filter
    threshold : float
        The threshold for quickly followed notes (default 0.1) and allowed
        overlap. Processing onsets in time order, if an onset is within
        `threshold` of the previous onset, the two notes are considered
        to be conconcurrent, and only the top note is considered in
        constructing the skyline. In the case of processing a note that
        is lower in pitch than the current skyline, we ignore the note
        if the skyline extends more than `threshold` beyond the note's
        onset. Otherwise, we shorten the skyline duration to end at the
        note onset and append the note to the skyline.

    Returns
    -------
    Score
        A new score containing the “skyline” notes

    Algorithm
    ---------
    The basic idea is to scan notes and copy them to skyline, a Part object
    belonging to a new Score. We can use shallow copy because notes are
    already deep-copied from score after merge_tied_notes.

    In the outer looop, we test each note to see if it is below the skyline
    as it exists so far. Since we process in order, we know each note cannot
    start before any note in the skyline. If the note is higher than the
    most recent skyline note (so far), there are two cases:

    1. The new note is approximately concurrent with the most recent skyline
       note: Replace the most recent skyline note with this one.
    2. The new note is after the most recent skyline note: Append the new
       note to the skyline. If the previous note overlaps the new note,
       adjust the previous note's duration to end at the onset of the new
       note.

    A consequence of this algorithm is that a very long low note will
    be shortened to the onset time of a new note, so a piano roll like
    this:
    ```
                               ----------
             ------------------------------------------
    ```
    will result in this:
    ```
                               ----------
             ------------------          (nothing here)
    ```
    rather than this:
    ```                        ----------
             ------------------          --------------
    ```

    Another consequence is that since skyline notes are never lengthened,
    there can be gaps in the skyline. It can look like this, where gaps
    (rests) can occur between notes:
    ```
                           ------      -----
             --------            ------         -------
    ```
    """
    # this code is based on get_sorted_notes():
    score = score.flatten(collapse=True)  # deep copies the score
    skyline: Part = cast(
        Part, score.content[0]
    )  # types: ignore (retrieves the Part)
    notes: List[Note] = cast(
        List[Note], skyline.content
    )  # (content is all Notes)
    skyline.content = []  # we will construct skyline from notes here

    prev_note: Optional[Note] = None
    for note in notes:
        if prev_note is None:
            skyline.content.append(note)
            prev_note = note

        # ignore notes that are below last note in skyline
        elif note.key_num < prev_note.key_num and (
            note.onset < prev_note.offset - threshold  # overlap
            or note.onset < prev_note.onset + threshold
        ):  # concurrent
            continue

        elif note.duration < threshold:
            continue

        # see if note is concurrent and higher
        if (
            note.onset < prev_note.onset + threshold
            and note.key_num >= prev_note.key_num
        ):
            skyline.content.pop()  # replace prev_note
            skyline.content.append(note)
            prev_note = note

        elif (
            note.onset >= prev_note.offset - threshold
            or note.key_num >= prev_note.key_num
        ):
            skyline.content.append(note)
            prev_note = note
            if prev_note.offset > note.onset:
                prev_note.offset = note.onset

        else:
            assert False, "Unexpected condition, implementation error detected"
    return score
