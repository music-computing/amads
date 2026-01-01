"""
Distribution of durations in a Score.
Provides the `ivdirdist1` function

Can emulate the `ivdurdist1` function in Midi Toolbox.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=64
"""

from amads.core.basics import Score
from amads.core.distribution import Distribution
from amads.pitch.ivdist1 import interval_distribution_1


def interval_direction_distribution_1(
    score: Score,
    name: str = "Interval Direction Distribution",
    weighted: bool = True,
    miditoolbox_compatible: bool = True,
) -> Distribution:
    """
    Returns the proportion of upward intervals for each interval size

    Currently, intervals greater than an octave will be ignored.

    Parameters
    ----------
    score : Score
        The music Score object to analyze
    name : str
        A name for the resulting distribution (title in distribution plot)
    weighted : bool, optional
        If True, the interval distribution is weighted by note durations
        in seconds that are modified according to Parncutt's durational
        accent model (1994), by default True.
    miditoolbox_compatible : bool
        Matlab MIDI Toolbox avoids zero division by dividing counts
        by the total count plus 1e-12 times the number of counts.
        True enables this behavior. Default is False, which simply skips
        division when the total count is zero (this also returns a
        zero matrix when the count is zero).

    Returns
    -------
    Distribution
        A 12-element distribution representing the proportion of
        upward intervals for each interval size. The components
        are spaced at semitone distances with the first component
        representing a minor second (not unison) and the last
        component the octave. If the score is empty, the function
        returns a list with all elements set to zero.
    """

    id = interval_distribution_1(score, name, weighted, miditoolbox_compatible)
    id = id.data  # we only need the data from the distribution
    idd = [0.0] * 12

    for i in range(12):
        # id[i + 13] is the upward interval
        # id[11 - i] is the downward interval
        if (id[i + 13] + id[11 - i]) != 0:
            idd[i] = id[i + 13] / (id[i + 13] + id[11 - i])
        else:
            idd[i] = 0

    x_categories = [str(i) for i in range(1, 13)]
    return Distribution(
        name,
        idd,
        "interval_direction",
        [12],
        x_categories,  # type: ignore
        "Interval Size",
        None,
        "Proportion",
    )
