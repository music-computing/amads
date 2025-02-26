"""
Provides the `skyline` function
"""

from ..core.basics import Note, Part, Score


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
      says the top note has priority, so shift the start time of the lower
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
    score = score.deep_copy()

    # flatten method alone doesn't merge tied notes for some reason
    score = score.strip_ties()
    if not score.is_flattened_and_collapsed():
        score = score.flatten(collapse=True)
    filtered_notes = []
    notes = list(score.find_all(Note))

    # sort the notes by start, if start is equal, sort by pitch
    notes.sort(key=lambda note: (note.onset, -note.pitch.keynum))

    for i in range(len(notes)):
        note = notes[i]
        # ignore notes that are below another existing note in filtered_notes
        if any(
            note.pitch.keynum < prev.pitch.keynum and note.onset < prev.offset
            for prev in filtered_notes
        ):
            continue

        # append the note to filtered_notes
        filtered_notes.append(note.deep_copy())

        # remove notes in filtered_notes that are below the current note

        for j in reversed(range(len(filtered_notes))):
            if (
                filtered_notes[j].pitch.keynum < note.pitch.keynum
                and filtered_notes[j].offset > note.onset
            ):
                # remove low notes quickly followed by a higher note
                if filtered_notes[j].onset > note.onset - threshold:
                    filtered_notes.pop(j)
                # keep low notes not so quickly followed by a higher note
                # shorten the duration of the low note
                else:
                    note_end = min(note.onset, filtered_notes[j].offset)
                    filtered_notes[j].duration = note_end - filtered_notes[j].onset

    # create a new score and part to store the filtered notes
    new_score = Score()
    new_part = Part()
    for note in filtered_notes:
        new_part.insert(note)
    new_score.insert(new_part)

    return new_score
