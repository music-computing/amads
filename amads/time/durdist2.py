"""
Distribution of duration pairs in a Score.

Author: [Yiming Huang, Roger Dannenberg]

Date: [2024-12-04]

Description:
    Compute the second-order duration distribution of notes in a musical score.

Dependencies:
    - amads
    - math

Usage:
    [Add basic usage examples or import statements]

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=59
"""

import math
from typing import List, Union

from ..core.basics import Note, Score
from ..core.distribution import Distribution
from ..pitch.ismonophonic import ismonophonic


def update_dd(
    dd: List[List[float]],
    bin_boundaries: Union[None, List[float]],
    prev_bin: int,
    note: Note,
) -> int:
    """Updates the duration distribution matrix based on the given notes.

    Serves as a helper function for `duration_distribution_2`.

    Args:
        dd (List[List[float]]): The duration distribution matrix to be updated.
        bin_boundaries (Union[None, List[float]]): The boundaries of the bins
            or None to use default bins.
        prev_bin (int): The previous bin index.
        note (Note): The note to be processed.

    Returns:
        int bin number for Note if Note was used to add a count to dd, else None
        (which become prev_bin on the next call and is used to control whether
        the *next* note provides a count to dd).
    """
    if bin_boundaries:
        for bin, boundary in enumerate(bin_boundaries):
            if note.duration <= boundary:
                break
        else:
            bin = len(bin_boundaries) - 1
    else:
        if note.duration <= 0:
            return None
        bin = round(2 * math.log2(note.duration)) + 4
        if bin < 0 or bin > 8:
            return None

    if prev_bin is not None:
        dd[prev_bin][bin] += 1
    return bin


def duration_distribution_2(
    score: Score,
    name: str = "Duration Pairs Distribution",
    bin_centers: Union[list[float], None] = None,
) -> Distribution:
    """
    Returns the 2nd-order duration distribution of a musical score.

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

    The result is a NxN matrix where N is the number of bins. The matrix is
    m[row][col] = proportion of notes where duration indicated by row is
    followed by duration indicated by col.

    Args:
        score (Score): The musical score to analyze.
        name (str): A name for the distribution and plot title.
        bin_centers (Union[list[float], None]): bin centers (optional)

    Returns:
        Distribution: containing 9x9 matrix of the distribution of note
        durations. The matrix (data attribute of the Distribution object)
        has m[row][col] = proportion of notes where duration indicated by
        row is followed by duration indicated by col.


    Raises:
        Exception: If the score is not monophonic (e.g. contains chords)
    """
    if not ismonophonic(score):
        raise ValueError("Score must be monophonic")

    bin_boundaries = None
    if bin_centers:
        dd = [[0] * len(bin_centers) for _ in range(len(bin_centers))]
        bin_boundaries = [
            math.sqrt(bin_centers[i] * bin_centers[i + 1])
            for i in range(len(bin_centers) - 1)
        ]
        x_categories = [f"{bin_centers[i]:.2f}" for i in range(len(bin_centers))]
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
        dd = [[0] * 9 for _ in range(9)]

    for container in score.note_containers():
        prev_bin = None
        for note in container.find_all(Note):
            prev_bin = update_dd(dd, bin_boundaries, prev_bin, note)

    # TODO: I believe if score has tied notes, they will be treated
    # separately rather than joined to form a single duration. I do
    # not think we need two cases here since score.find_all() will
    # find all notes either way. -RBD

    # normalize
    total = sum([sum(row) for row in dd])
    if total > 0:
        dd = [[i / total for i in row] for row in dd]

    return Distribution(
        name,
        dd,
        "duration_pairs",
        [len(dd), len(dd)],
        x_categories,
        "Duration (to)",
        x_categories,
        "Duration (from)",
    )
