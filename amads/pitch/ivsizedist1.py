"""
Provides the `ivsizedist1` function
"""

from amads.core.basics import Score
from amads.core.distribution import Distribution
from amads.pitch.ivdist1 import interval_distribution_1


def interval_size_distribution_1(
    score: Score,
    name: str = "Interval Size Distribution",
    weighted: bool = True,
    miditoolbox_compatible: bool = True,
) -> Distribution:
    """
    Returns the interval size distribution of a musical score.

    Intervals greater than one octave are ignored.

    Parameters
    ----------
    score : Score
        The musical score to analyze
    name : str
        A name for the distribution and plot title.
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
        A 13-element distribution representing proportions of interval sizes.
        The first element corresponds to unison intervals, and the last
        element corresponds to octave intervals. If the score is empty,
        the function returns a Distribution with all elements set to zero.
    """
    id = interval_distribution_1(score, name, weighted, miditoolbox_compatible)
    id = id.data  # we only need the data from the distribution
    isd = [0.0] * 13

    isd[0] = id[12]
    for i in range(1, 13):
        isd[i] = id[i + 12] + id[12 - i]  # merge upward and downward bins
    # note that isd is normalized because it sums to the same value as isd
    x_categories = [str(i) for i in range(13)]
    return Distribution(
        name,
        isd,
        "interval_size",
        [12],
        x_categories,  # type: ignore
        "Interval Size",
        None,
        "Proportion",
    )
