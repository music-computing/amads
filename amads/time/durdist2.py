"""
Distribution of duration pairs in a Score.
Provides the `duration_distribution_2` function.

Can emulate the `ivdurdist2` function in Midi Toolbox.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=59
"""

from typing import Optional, Union, cast

from amads.core.basics import Note, Part, Score
from amads.core.distribution import Distribution
from amads.core.histogram import Histogram2D, centers_to_boundaries

_author_ = ["Yiming Huang", "Roger Dannenberg"]


def duration_distribution_2(
    score: Score,
    name: str = "Duration Pairs Distribution",
    bin_centers: Optional[list[float]] = None,
    ignore_extrema: Union[bool, str] = "unspecified",
    miditoolbox_compatible: bool = False,
) -> Distribution:
    r"""
    Returns the 2nd-order duration distribution of a musical score.

     Each duration is assigned to one of 9 bins.
    The default centers of the bins are on a logarithmic scale as follows:

    | component | bin center (in units of quarters) |
    |-----------|-----------------------------------|
    | 0         | 1/4 (sixteenth)                   |
    | 1         | sqrt(2)/4                         |
    | 2         | 1/2 (eighth)                      |
    | 3         | sqrt(2)/2                         |
    | 4         | 1 (quarter)                       |
    | 5         | sqrt(2)                           |
    | 6         | 2 (half)                          |
    | 7         | 2*sqrt(2)                         |
    | 8         | 4 (whole)                        |

    These centers can be overridden by providing a list of bin centers.

    If `midi_toolbox_compatible` is True, the behavior is the same as in
    the Midi Toolbox `durdist1` function, with each bin count increased by
    1e-12 to avoid division by zero, and values below $sqrt(2)/8$ quarters
    (just above a sixteenth triplet) and greater than $sqrt(2) \cdot 4$ quarters
    (about 5.65685) are ignored. Also, an error is raised if either
    `bin_centers` or `ignore_extrema` are specified.

    If `midi_toolbox_compatible` is False (default), the normal behavior
    is as follows. If `bin_centers` is not provided, the default centers
    listed above are used. Values below the lowest or above the highest
    bins are assigned to those bins appropriately.

    One remaining case is where you want to ignore values outside the
    range of the bins. This can be done by setting `ignore_extrema` to
    True. If `bin_centers` is not provided, the default bins are used,
    and the extreme boundaries are set to $sqrt(2)/8$ quarters and
    $sqrt(2) \cdot 4$ quarters respectively. If `bin_centers` is provided,
    they must include an additional lower bin and upper bin center value
    so that upper and lower boundaries can be computed as
    $sqrt(bin\\_centers[0] * bin\\_centers[1])$ and
    $sqrt(bin\\_centers[-2] * bin\\_centers[-1])$ respectively. Since values
    beyond the boundaries are ignored, the result will have
    $len(bin\\_centers) - 2$ bins.

    <small>**Authors**: Yiming Huang, Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The musical score to analyze.
    name : str
        A name for the distribution and plot title.
    bin_centers : Union[list[float], None])
        bin centers (optional) (see description for details).
    ignore_extrema : bool
        If True, values outside the range of the bins are ignored
        (see description for details).
    miditoolbox_compatible : bool
        Matlab MIDI Toolbox avoids zero division by dividing counts
        by the total count plus 1e-12 times the number of counts.
        True enables this behavior as well as ignoring extreme values
        and setting the bins as described above. Default is False.
        If True, `bin_centers` and `ignore_extrema` must not be set.

    Returns
    -------
    Distribution
        containing and describing the distribution of note durations.

    Raises
    ------
    ValueError: If the score is not monophonic (e.g. contains chords) or
        if the miditoolbox is True and either `bin_centers` or
        `ignore_extrema` optional parameters are set or
        `ignore_extrema` is true and less than 3 bin centers are provided.
    """
    if miditoolbox_compatible:
        if bin_centers is not None or ignore_extrema != "unspecified":
            raise ValueError(
                "When miditoolbox_compatible is True, "
                "bin_centers and ignore_extrema must not be set."
            )
    if not score.ismonophonic():
        raise ValueError("Score must be monophonic")

    if ignore_extrema == "unspecified":
        ignore_extrema = miditoolbox_compatible
    initial_value = 1e-12 if miditoolbox_compatible else 0.0
    x_categories = None

    if not bin_centers:
        bin_boundaries = [2 ** ((i - 0.5) / 2.0) for i in range(-4, 6)]
        bin_centers = [2 ** (i / 2.0) for i in range(-4, 5)]
        ignore_extrema = True
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
    elif ignore_extrema:
        if len(bin_centers) < 3:
            raise ValueError(
                "When ignore_extrema is True and "
                "bin_centers is provided, at least "
                "three bin centers must be provided."
            )
        bin_boundaries = centers_to_boundaries(bin_centers, "log")
        bin_centers = bin_centers[1:-1]
    else:
        bin_boundaries = None

    if not x_categories:
        x_categories = [
            f"{bin_centers[i]:.2f}" for i in range(len(bin_centers))
        ]

    h = Histogram2D(
        bin_centers, bin_boundaries, "log", ignore_extrema, initial_value
    )  # type: ignore

    # TODO: what does matlab do with polyphony? This processes
    # each part separately (no interval from last note in one part
    # to the first note in the next part). This is probably
    # unnecessary since we already require monophonic input.

    # Ignore notes that are tied from previous notes by keeping track
    # of them in a set:
    tied_notes = set()
    for p in score.find_all(Part):
        part: Part = cast(Part, p)
        prev_dur = None
        prev_bin = None
        for n in part.find_all(Note):
            note: Note = cast(Note, n)
            if note in tied_notes:
                # skip tied notes
                continue
            if note.tie:
                # add tied notes to set so we can skip them later
                tied_notes.add(note)
            dur = note.duration
            prev_bin = h.add_point_2d(prev_dur, dur, 1.0, prev_bin)
            prev_dur = dur
            if prev_bin is None:
                prev_dur = None
    # normalize
    h.normalize()

    return Distribution(
        name,
        h.bins,
        "duration_pairs",
        [len(h.bins), len(h.bins)],
        x_categories,  # type: ignore
        "Duration (to)",
        x_categories,  # type: ignore
        "Duration (from)",
    )
