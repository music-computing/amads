
# once this is done, we at least have a starting point to adjust the function
# signatures as desired
from amads.core.basics import Score, Note
from typing import List, Tuple

def mel_accent(score: Score) -> Tuple[Score, List[Tuple[float]]]:
    """
    Returns: Score, List[Tuple[float]]
    Flattened score with accent annotations on each note under the attribute name
    "mel_accent_val".

    A list of melodic accent salience parameter tuples, each corresponding (in
    relative order) to pairs of subsequent pitches in the flattened score (in
    the same order).
    """
    if not score.ismonophonic():
        raise ValueError("melody accents only applicable to monophonic scores")

    flattened_score = score.flatten()
    note_iter = flattened_score.find_all(Note)

    note1, note2, note3 = None, None, None
    try:
        note1 = next(note_iter)
        note2 = next(note_iter)
        note3 = next(note_iter)
    except StopIteration:
        if not note1:
            raise ValueError("melody accents only applicable to nonempty scores")
        if not note2 or not note3:
            return 0

    accent_list = []
    while note3 != None:
        diff1 = note2.pitch - note1.pitch
        diff2 = note3.pitch - note2.pitch
        if diff1 == 0 and diff2 == 0:
            accent_list.append((0.00001, 0.0))
        elif diff1 != 0 and diff2 == 0:
            accent_list.append((1.0, 0.0))
        elif diff1 == 0 and diff2 != 0:
            accent_list.append((0.00001, 1))
        elif diff1 > 0 and diff2 < 0:
            accent_list.append((0.83, 0.17))
        elif diff1 < 0 and diff2 > 0:
            accent_list.append((0.71, 0.29))
        elif diff1 > 0 and diff2 > 0:
            accent_list.append((0.33, 0.67))
        elif diff1 < 0 and diff2 < 0:
            accent_list.append((0.5, 0.5))
            assert 0
        else:
            raise RuntimeError("something is very wrong with program state")

    return flattened_score, accent_list