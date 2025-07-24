from shift import shift

from ..core.basics import Score

# TODO: comments!


def trim(score: Score):
    # this function destroys the score in place before returning
    # a list of sorted notes...
    # ! probably better to just get minimum from the iterator instead...
    score_copy = score.deep_copy()
    notes = score_copy.get_sorted_notes()
    # once we obtained the offset... things change...
    onset = notes[0].onset
    score_copy = score.deep_copy()
    return shift(score_copy, "onset", -onset)
