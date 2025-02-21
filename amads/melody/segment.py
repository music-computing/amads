from typing import List

from amads.core.basics import Note, Score


def fantastic_segmenter(score: Score, phrase_gap: float = 1.0) -> List[Note]:
    """Segment melody into phrases based on IOI gaps.
    Parameters
    ----------
    score : Score
        Score object containing melody to segment
    phrase_gap : float, optional
        The minimum IOI gap to consider a new phrase, by default 1.0

    Returns
    -------
    list[Note]
        List of Note objects representing phrases
    """
    # Extract notes from score
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))
    # Calculate IOIs
    for i, note in enumerate(notes):
        if i < len(notes) - 1:
            note.ioi = notes[i + 1].start - note.start
        else:
            note.ioi = None

    phrases = []
    current_phrase = []
    for note in notes:
        # Check whether we need to make a new phrase
        need_new_phrase = (
            len(current_phrase) > 0
            and current_phrase[-1].ioi is not None
            and current_phrase[-1].ioi > phrase_gap  # Default phrase gap of 1 second
        )
        if need_new_phrase:
            phrases.append(current_phrase)
            current_phrase = []
        current_phrase.append(note)

    # Always append the final phrase, even if it's just one note
    if len(current_phrase) > 0:
        phrases.append(current_phrase)

    return phrases
