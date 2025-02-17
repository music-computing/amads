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

    Examples
    --------
    >>> scaled_score = scale(score.copy(), factor=2, dim='start')  # scales start by factor of 2
    >>> scaled_score = scale(score.copy(), factor=0.5, dim='duration')  # shortens durations by factor of 2
    """
    if dim == "all":
        scale(score, factor, "duration")
        scale(score, factor, "start")
        return score
    for elem in score.content:
        if isinstance(elem, EventGroup):
            scale(elem, factor, dim)
            if dim == "start":
                elem.start *= factor
        else:
            if dim == "duration":
                elem.duration *= factor
            elif dim == "start":
                elem.start *= factor
        score.duration = max(score.duration, elem.end)
    return score
