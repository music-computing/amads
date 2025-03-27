"""
Distribution of durations of notes in a Score.

Author: [Yiming Huang, Roger Dannenberg]
Date: [2024-12-04]

Description:
    Compute

Dependencies:
    - [List any key dependencies]

Usage:
    [Add basic usage examples or import statements]

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=58
"""

import math
from typing import Union

from ..core.basics import Note, Score
from ..core.distribution import Distribution


def duration_distribution_1(
    score: Score,
    name: str = "Duration Distribution",
    bin_centers: Union[list[float], None] = None,
) -> Distribution:
    """
    Returns the distribution of note durations in a Score.

    Each duration is assigned to one of 9 bins.
    The default centers of the bins are on a logarithmic scale as follows:
        component    bin center (in units of quarters)
        0            1/4 (sixteenth)
        1            sqrt(2)/4
        2            1/2 (eighth)
        3            sqrt(2)/2
        4            1 (quarter)
        5            sqrt(2)
        6            2 (half)
        7            2*sqrt(2)
        8            4 (whole)
    Durations below sqrt(2)/8 quarters (just above a sixteenth triplet) and
    greater than sqrt(2) * 4 quarters (about 5.65685 beats) are ignored.

    If `bin_centers` is provided, the centers of the bins are set to the
    values in `bin_centers` and rounding is done on a log scale, i.e. the
    boundary between x1 and x2 (bin centers) is sqrt(x1 * x2). Any duration
    below the lower boundary is assigned to the first bin, and any duration
    above the upper boundary is assigned to the last bin.

    Args:
        score (Score): The musical score to analyze.
        name (str): A name for the distribution and plot title.
        bin_centers (Union[list[float], None]): bin centers (optional)

    Returns:
        Distribution: containing and describing the distribution of note durations.
    """

    if bin_centers:
        dd = [0] * len(bin_centers)
        bin_boundaries = [
            math.sqrt(bin_centers[i] * bin_centers[i + 1])
            for i in range(len(bin_centers) - 1)
        ]
        x_categories = [f"{bin_centers[i]:.2f}" for i in range(len(bin_centers))]
        for note in score.find_all(Note):
            for i, boundary in enumerate(bin_boundaries):
                if note.duration <= boundary:
                    dd[i] += 1
                    break
            else:
                dd[-1] += 1
    else:
        x_categories = [
            "sixteenth",
            "0.35",
            "eighth",
            "0.71",
            "quarter",
            "1.41",
            "half",
            "2.83",
            "whole",
        ]
        dd = [0] * 9
        for note in score.find_all(Note):
            # The following algorithm comes from the original MATLAB implementation
            # https://github.com/miditoolbox/1.1/blob/master/miditoolbox/durdist1.m
            if note.duration != 0:
                bin = round(2 * math.log2(note.duration)) + 4
                if 0 <= bin <= 8:
                    dd[bin] += 1

    # normalize
    total = sum(dd)
    if total > 0:
        dd = [i / total for i in dd]

    return Distribution(
        name, dd, "duration", [9], x_categories, "Duration", None, "Proportion"
    )
