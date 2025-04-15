"""
Provides the `skyline` function
"""

from ..core.basics import Part, Score


def skyline(score: Score, threshold: float = 0.1):
    """
    Finds the skyline of a musical score.

    (Copy-pasted from Prof Dannenberg's email)
    Filters a score, removing any note that is below another note.
    There are tricky edge cases:

    - A lower note that quickly is followed by a higher note: Probably the
      right thing is ignore the lower note if the time to the upper note is
      less than some threshold (maybe default to 0.1 beats) that can be set
      through a keyword parameter.
    - (not implemented yet) A rolled chord with 10 notes starts at the bottom,
      and every 0.05 quarter notes, a new note enters. So the previous rule
      applies to each note but the top note is a full 0.45 quarters after the
      first one? Do we still ignore notes? I would say yes.
    - A lower note is not so quickly followed by a higher note. Shorten the
      lower note to end at the time of the upper note.
    - An upper note of a melody sustains in a legato fashion past the next,
      but lower, note of the melody. Though musically the upper note should
      be shortened and we should keep the lower note, the "skyline" concept
      says the top note has priority, so shift the onset time of the lower
      note to the end time of the upper note, and shorten the lower note
      duration so that it still ends at the same time as before.
    - It is common to have melodies in lower voices. This algorithm just fails
      to find the melody.


    Args:
        score (Score): The musical score to filter
        threshold (float, optional): The threshold for quickly followed notes
                                     (default 0.1)

    Returns:
        Score: A new score containing the "skyline" notes
    """

    score = score.merge_tied_notes()
    new_score = score.emptycopy()
    skyline = Part(parent=new_score)
    notes = score.get_sorted_notes()

    # Algorithm: the basic idea is to scan notes and copy them
    # to skyline, a Part object. We can use shallow copy
    # because notes are already deep copied from score after
    # merge_tied_notes.
    #
    # In the outer looop, we test each note to see if it is below
    # the skyline as it exists so far. Since we process in order,
    # we know each note starts after all notes in the skyline, so
    # time overlap occurs when a note starts before the end of a
    # skyline note. (Use a threshold in case the note starts at
    # approximately the previous note end time) When a note is
    # added to the skyline, it may be above an existing skyline
    # note that started earlier, so the inner loop deals with
    # this problem.
    #
    # In the inner loop, we remove skyline notes that started before
    # the new note and are below it (if they were above, the new note
    # would have been filtered out before we got to this part). Since
    # notes have arbitrary duration, *any* skuyline note could potentially
    # overlap in time and be below the new note, so we have to check
    # all skyline notes. We search in reverse order so that we can remove
    # notes from skyline without worrying about the index changing.
    # Since we know the new note starts after all skyline notes, again we
    # can test for time overlap by checking if the new note starts before
    # the end of the skyline note. We remove the lower note only when
    # the new note starts within threshold of the skuyline note. Otherwise,
    # the lower note plays for longer than threshold before the new note:
    # we shorten the duration of the lower note to end at the onset time
    # of the new note.
    #
    # A consequence of this algorithm is that a very long low note will
    # be shortened to the onset time of a new note, so a piano roll like
    # this:                      ----------
    #          ------------------------------------------
    # will result in this:       ----------
    #          ------------------          (nothing here)
    # rather than this:          ----------
    #          ------------------          --------------
    # A faster algorithm would avoid iterating over all skyline notes
    # (twice!) since we know the skyline is monophonic and ordered.

    for i in range(len(notes)):
        note = notes[i]
        # ignore notes that are below another existing note in skyline
        if any(
            note.pitch.keynum < prev.pitch.keynum
            and note.onset < prev.offset - threshold
            for prev in skyline.content
        ):
            print("Skipping note ", end="")
            note.show()
            continue

        # append the note to skyline
        print("Adding note ", end="")
        note.show()
        note.copy(skyline)

        # remove notes in skyline that are below the current note

        for j in reversed(range(len(skyline.content))):
            if (
                skyline.content[j].pitch.keynum < note.pitch.keynum
                and note.onset < skyline.content[j].offset
            ):
                # remove low notes quickly followed by a higher note
                if skyline.content[j].onset > note.onset - threshold:
                    print("Removing note ", end="")
                    skyline.content[j].show()
                    skyline.content.pop(j)
                # keep low notes not so quickly followed by a higher note
                # but shorten the duration to prevent overlap
                else:
                    print("Shortening note ", end="")
                    skyline.content[j].show()
                    skyline.content[j].offset = note.onset

    return new_score
