"""Scale event timings in a score by a given factor."""

from ..core.basics import EventGroup


def scale(score, factor=2.0, dim="all", inplace=False):
    """Scale event timings in a score by a given factor.

    Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=88
    Note that if notes are tied, scaling by only onset time or only duration
    will result in tied notes where the offset of the first note is not the
    same as the onset of the second note.

    Parameters
    ----------
    score : EventGroup
        Score object or other EventGroup object to be modified
    factor : float
        Amount to scale by (must be > 0)
    dim : {'onset', 'duration', 'all'}
        Dimension to scale:
        - 'onset': scales the onset times of all events
        - 'duration': scales the durations of all non-EventGroup events (Note, Rest)
        - 'all': scales both onset times and durations
    inplace : bool
        If True, modify the input score in place. If False, return a new score
        object with the scaled timings. (Default value = False)

    Returns
    -------
    EventGroup
        The scaled version of the input score (modified in place)
    """
    # Algorithm: onset times are scaled when all deltas are scaled.
    # Note that setting onsets directly is not straightforward: if
    # you scale the parent onset first (changing the delta) that
    # will change all the children onsets before you get a chance
    # to scale them. If you scale the children first, then they
    # will have incorrect values after you scale the parent.

    if not inplace:
        score = score.copy()
    assert dim in ["all", "onset", "duration"]
    if dim == "all":  # do both in place
        scale(score, factor, "duration", True)
        scale(score, factor, "onset", True)
        return score
    if dim == "onset":
        score.onset *= factor
    else:  # dim must be duration
        score.duration *= factor
    for elem in score.content:
        if isinstance(elem, EventGroup):
            # make the changes in place (inplace=True):
            scale(elem, factor, dim, True)
        elif dim == "onset":
            elem.onset *= factor
        else:  # dim == "duration"
            elem.duration *= factor
    return score
