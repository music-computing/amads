from typing import List

from amads.core.basics import Note, Part, Score


def fantastic_segmenter(score: Score, phrase_gap: float, units: str) -> List[Score]:
    """Segment melody into phrases based on IOI gaps.
    Parameters
    ----------
    score : Score
        Score object containing melody to segment
    phrase_gap : float
        The minimum IOI gap to consider a new phrase
    units : str
        The units of the phrase gap, either "seconds" or "quarters"

    Returns
    -------
    list[Score]
        List of Score objects representing phrases
    """
    if units == "seconds":
        raise NotImplementedError(
            "Seconds are not yet implemented, see issue #75: "
            "https://github.com/music-computing/amads/issues/75"
        )

    if units == "quarters":
        # Extract notes from score
        flattened_score = score.flatten(collapse=True)
        notes = list(flattened_score.find_all(Note))
        # Calculate IOIs
        for i, note in enumerate(notes):
            # first note has no IOI by convention
            if i > 0:
                note.ioi = note.onset - notes[i - 1].onset
            else:
                note.ioi = None

        phrases = []
        current_phrase = []
        for note in notes:
            # Check whether we need to make a new phrase
            need_new_phrase = (
                len(current_phrase) > 0
                and note.ioi
                is not None  # Check current note's IOI instead of previous note
                and note.ioi > phrase_gap  # Default phrase gap of 1 quarter note
            )
            if need_new_phrase:
                # Create new score for the phrase
                phrase_score = Score()
                part = Part()
                start_time = current_phrase[0].onset
                # Adjust note timings relative to phrase start
                for phrase_note in current_phrase:
                    new_note = phrase_note.deep_copy()
                    new_note.onset -= start_time
                    part.insert(new_note)
                phrase_score.insert(part)
                phrases.append(phrase_score)
                current_phrase = []
            current_phrase.append(note)

        # Append final phrase
        if len(current_phrase) > 0:
            phrase_score = Score()
            part = Part()
            start_time = current_phrase[0].onset
            for phrase_note in current_phrase:
                new_note = phrase_note.deep_copy()
                new_note.onset -= start_time
                part.insert(new_note)
            phrase_score.insert(part)
            phrases.append(phrase_score)

        return phrases
