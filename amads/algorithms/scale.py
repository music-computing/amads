"""Scale event timings in a score by a given factor."""

from ..core.basics import EventGroup


def scale(score, factor=2.0, dim="all"):
    """Scale event timings in a score by a given factor.

    Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=88

    Parameters
    ----------
    score : EventGroup
        Score object or other EventGroup object to be modified
    factor : float
        Amount to scale by (must be > 0)
    dim : {'start', 'duration', 'all'}
        Dimension to scale:
        - 'start': scales the start times of all events
        - 'duration': scales the durations of all non-EventGroup events (Note, Rest)
        - 'all': scales both start times and durations

    Returns
    -------
    EventGroup
        The scaled version of the input score (modified in place)
    """
    assert dim in ["all", "onset", "duration"]
    if dim == "all":
        scale(score, factor, "duration")
        scale(score, factor, "onset")
        return score
    for elem in score.content:
        if isinstance(elem, EventGroup):
            scale(elem, factor, dim)
            if dim == "onset":
                elem.onset *= factor
        else:
            if dim == "duration":
                elem.duration *= factor
            elif dim == "onset":
                elem.onset *= factor
            else:
                raise ValueError(f"Invalid dimension: {dim}")
        score.duration = max(score.duration, elem.offset)
    return score
