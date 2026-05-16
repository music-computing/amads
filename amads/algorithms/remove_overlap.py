"""Remove overlapping notes with the same pitch from a score."""

from collections import defaultdict

from amads.core.basics import Note, Part, Score


def remove_overlap(
    score: Score, tolerance: float = 0.1, min_separation: float = 0.0
) -> Score:
    """Remove overlapping notes with the same pitch from a score.

    Sometimes in piano parts, a note participates in two voices and
    is printed as if two voices play the same note in unison, when
    of course the pianist only plays the pitch once. After reading
    a musicXML score, these doubled notes will be represented in the
    score. You can use this function to remove overlap.

    Other cases can arise from reductions or merging of parts, or
    from rounding errors. This function can be used to clean up
    these cases.

    When producing MIDI output for playback, there is a risk of
    rounding error causing a note-on to be placed immediately *before*
    the note-off of a prceding note of the same pitch. This can cause
    a "stuck note." A simple solution is to shorten notes by a small
    amount when the same pitch follows immediately. Then, their note-off
    event will be sorted *before* the next note's note-on event. (A
    very slightly reduced duration is rarely audible, and separation
    must be introduced in a physical piano performance.) The
    `min_separation` parameter can be used to ensure that adjacent
    notes with the same pitch are separated by at least that amount.
    0.02 is a reasonable choice: no one can play 50 notes per beat,
    but 0.02 is certain to quantize to at least one Standard MIDI File
    tick at any reasonable tick size. If units are seconds, 0.02 is
    just 20 milliseconds.

    The score is first flattened (ties merged, notes extracted from
    measures and staves). Within each part, notes sharing the same
    `key_num` that overlap in time are resolved:

    - If two notes start within `tolerance` of each other, the note that
      starts first (or the first in sorted order when onsets are equal)
      is kept and extended to the maximum offset of the two; the second
      note is removed.
    - If the notes do not start within `tolerance` but the first note
      extends past the onset of the second, the first note is shortened
      so that it ends at the onset of the second note. The second note
      is extended to the offset of the first if necessary.

    Each part is processed independently.

    Parameters
    ----------
    score : Score
        The score to process.  The original score is not modified; a
        new flat score is returned.
    tolerance : float
        Maximum onset difference (in seconds or beats depending on the
        score's time unit) for two notes with the same `key_num` to be
        considered simultaneous.  Defaults to `0.1`.
    min_separation : float
        Minimum separation (in seconds or beats depending on the score's
        time unit) between adjacent notes with the same `key_num`.  If
        `0.0`, no minimum separation is enforced.  Defaults to `0.0`.
        Must be less than half of `tolerance` to avoid introducing note
        durations less than min_separation.

    Returns
    -------
    Score
        A new flat score with overlapping same-pitch notes resolved.

    Examples
    --------
    Two notes with the same pitch that start at the same time are merged
    into a single note whose duration is the maximum of the two:

    >>> from amads.core.basics import Note, Part, Score
    >>> score = Score(Part(Note(pitch="C4", onset=0.0, duration=2.0),
    ...                    Note(pitch="C4", onset=0.0, duration=3.0)))
    >>> result = remove_overlap(score)
    >>> notes = result.content[0].content
    >>> len(notes)
    1
    >>> notes[0].duration
    3.0

    A note that overlaps a later note with the same pitch is trimmed so
    that it ends exactly when the later note begins. The later note is
    extended if necessary to cover the full duration of the first note:

    >>> score = Score(Part(Note(pitch="C4", onset=0.0, duration=4.0),
    ...                    Note(pitch="C4", onset=1.0, duration=2.0)))
    >>> result = remove_overlap(score)
    >>> notes = result.content[0].content
    >>> len(notes)
    2
    >>> notes[0].duration
    1.0
    >>> notes[1].onset
    1.0
    >>> notes[1].duration
    3.0

    Use min_separation to ensure that adjacent notes with the same pitch
    are separated by at least that amount:

    >>> score = Score(Part(Note(pitch="C4", onset=0.0, duration=4.0),
    ...                    Note(pitch="C4", onset=4.0, duration=2.0)))
    >>> result = remove_overlap(score, min_separation=0.02)
    >>> notes = result.content[0].content
    >>> len(notes)
    2
    >>> notes[0].duration
    3.98
    >>> notes[1].onset
    4.0
    >>> notes[1].duration
    2.0
    """
    score = score.flatten()
    assert min_separation * 2 < tolerance, (
        "min_separation must be less " "than half of tolerance"
    )

    for part in score.find_all(Part):
        _remove_overlap_in_part(part, tolerance, min_separation)

    return score


def _remove_overlap_in_part(
    part: Part, tolerance: float, min_separation: float
) -> None:
    """Resolve overlapping same-pitch notes within a single Part in place."""
    notes: list[Note] = part.list_all(Note)  # type: ignore  (return list[Note])

    # Group notes by key_num.  Part.flatten() sorts by (onset, pitch), so
    # each group is already onset-ordered.
    by_key: dict = defaultdict(list)
    for note in notes:
        by_key[note.key_num].append(note)

    to_remove: set[int] = set()

    for key_notes in by_key.values():
        i = 0
        j = 1
        while j < len(key_notes):
            a = key_notes[i]
            b = key_notes[j]
            # see if b (at j) overlaps a (at i)
            if a.offset > b.onset - min_separation:  # overlap detected
                if abs(b.onset - a.onset) <= tolerance:
                    # Same start: extend a to cover both offsets, drop b.
                    if b.offset > a.offset:
                        a.offset = b.offset
                    to_remove.add(id(b))
                else:
                    # Different starts: trim a to end at b's onset.
                    if a.offset > b.offset:
                        b.offset = a.offset  # extend b to cover a if necessary
                    a.offset = b.onset - min_separation
                    i = j  # a no longer overlaps; advance to b
            else:
                i = j  # no overlap; advance to b
            j = j + 1  # advance to next b

    if to_remove:
        part.content = [  # type: ignore
            n
            for n in part.content
            if not (isinstance(n, Note) and id(n) in to_remove)
        ]
