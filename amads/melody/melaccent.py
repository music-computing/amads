
# TODO: blurb and citations!
# once this is done, we at least have a starting point to adjust the function
# signatures as desired
from amads.core.basics import Score, Note
from typing import List, Tuple

def melaccent(score: Score) -> Score:
    """
    TODO: some optimization needed, also comments
    Returns: Score, List[Tuple[float]]
    Flattened score with accent annotations on each note under the attribute name
    "accent_val".
    """
    if not score.has_instanceof(Note):
        raise ValueError("nonempty scores only")
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
    while not note3:
        diff1 = note2.pitch - note1.pitch
        diff2 = note3.pitch - note2.pitch
        note1 = note2
        note2 = note3
        note3 = next(note_iter)
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
        else:
            raise RuntimeError("something is very wrong with program state")

    # setting another iterator on notes
    output_note_iter = flattened_score.find_all(Note)
    # first note
    note = next(output_note_iter)
    note.accent_val = 1
    # second note
    note = next(output_note_iter)
    note.accent_val = accent_list[0][0]
    for tuple1, tuple2 in zip(accent_list, accent_list[1:]):
        previous_accent_val = 1 if tuple1[1] == 0 else tuple1[1]
        next_accent_val = 1 if tuple1[1] == 0 else tuple2[0]
        note = next(output_note_iter)
        note.accent_val = previous_accent_val * next_accent_val

    return flattened_score