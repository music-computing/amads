"""
On this module:
- `skyline` demonstrates a strict case for
    retrieving the highest sounding notes at any given point (with caveats as noted below).
- `extreme` is a similar function but for returning the *single* highest/lowest/sharpest/flatest note only.

See also
 -`envelope.py` for a variant on skyline that could be said to constitute a "smoothed" form of the same.

<small>**Authors**: Roger Dannenberg, Arnav Sayooj, Mark Gotham</small>
"""

__authors__ = ["Roger Dannenberg", "Arnav Sayooj", "Mark Gotham"]

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


def extreme(score: Score, attribute: str = "high") -> int:
    """
    Returns the extreme pitched Note from any score, as measured by one of four `attribute` options.

    The highest/lowest pair is relatively clear.
    This resembles the `skyline` functionality also in this module
    as well as the `extreme` function in in MIDI Toolbox
    (https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 61)
    except that this function returns the single highest/lowest note overall.

    To this logic we add another pair of options: the sharpest/flattest note,
    for that note who's pitch *spelling* is furthest along the spiral of fifths.

    Parameters
    ----------
    score : Score
        The polyphonic score to process.
    attribute : str. One of 4 options:
        "high" (default) or "low" by absolute pitch value (MIDI number, no spelling)
        or "sharp" or "flat" for that note who's pitch spelling is furthest along the spiral of fifths.
        Note that for the latter pair, the integer refers to the number of fifths from C,
        so F is -1 and G is plus 1, for example.

    Returns
    -------
    int
        The value in question.

    Examples
    --------
    >>> from amads.music import example
    >>> from amads.io.readscore import read_score
    >>> mid = read_score(example.fullpath("midi/sarabande.mid"))  # doctest: +ELLIPSIS
    Reading ...
    >>> extreme(mid, attribute="high")
    92
    >>> extreme(mid, attribute="low")
    62
    >>> extreme(mid, attribute="sharp")
    7
    >>> extreme(mid, attribute="flat")
    -4

    >>> extreme(mid, attribute="invalid_attribute")
    Traceback (most recent call last):
    ...
    ValueError: attribute must be one of ('high', 'low', 'sharp', 'flat'), got 'invalid_attribute'

    """

    valid_attributes = ("high", "low", "sharp", "flat")
    attribute = attribute.lower()
    if attribute not in valid_attributes:
        raise ValueError(
            f"attribute must be one of {valid_attributes}, got {attribute!r}"
        )

    flat_score = score.flatten()
    notes = flat_score.get_sorted_notes()

    if len(notes) < 2:
        raise ValueError(
            "Only call this function on cases with at least two notes."
        )

    if attribute in ("high", "low"):
        current = notes[0].pitch.key_num
    elif attribute in ("sharp", "flat"):
        current = notes[0].pitch.fifths_from_c

    for note in notes[1:]:
        if attribute == "high" and note.pitch.key_num > current:
            current = note.pitch.key_num
        elif attribute == "low" and note.pitch.key_num < current:
            current = note.pitch.key_num
        elif attribute == "sharp" and note.pitch.fifths_from_c > current:
            current = note.pitch.fifths_from_c
        elif attribute == "flat" and note.pitch.fifths_from_c < current:
            current = note.pitch.fifths_from_c

    return current
