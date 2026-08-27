from amads.core.basics import Note, Score, Measure
from amads.core.distribution import Distribution
from amads.core.histogram import Histogram1D

from fractions import Fraction

__author__ = "Anirudh Subramanian"

def onset_distribution(
    score: Score,
    quarters_per_measure: int = 4,
    divisions: int = 4,
    name: str = "Distribution of note onsets",
) -> Distribution:
    """
    Returns a distribution of onsets of Notes relative to the onset of
    their corresponding Measure.
    
    If the onset of a Note lies between two divisions of a quarter note,
    the onset rounds down to the nearest division of a quarter note (i.e.
    the floor of the onset time).
    
    Onsets are weighted by the duration of the corresponding Note because
    longer notes are better percieved by listeners (Thompson, 1994). Tied
    notes are merged into single notes, so a tied note only counts as one
    onset and is weighted by its tied duration.

    Parameters
    ----------
    score : Score
        The musical score to analyze.
    quarters_per_measure : int
        The number of quarter notes in a single measure. This value is
        used to determine the bins of the Distribution, so it should equal
        the length of the longest measure if measures are of unequal
        lengths.
    divisions : int
        The number of subdivisions of a single quarter note to quantize
        onset time to.
    name : str
        The name of the Distribution (purely stylistic)
        
    Returns
    -------
    Distribution
        containing and describing the distribution of note onsets.
    
    References
    ----------
    Thompson, W. F. (1994). Sensitivity to combinations of musical
        parameters: Pitch with duration, and pitch pattern with durational
        pattern. Perception & Psychophysics, 56, 363-374.
    """

    score = score.merge_tied_notes()

    num_bins = int(quarters_per_measure * divisions)

    # num_bins + 1 is used to define highest value for bin boundary
    boundaries = [Fraction(i / divisions) for i in range(num_bins + 1)]

    h = Histogram1D(
        bin_centers=boundaries[:-1],
        bin_boundaries=boundaries,
        ignore_extrema=False
    )

    for m in score.find_all(Measure):
        for n in m.find_all(Note):
            h.add_point(n.onset - m.onset, weight=n.duration)
    
    return Distribution(
        name=name,
        data=h.bins,
        distribution_type="onset_within_measure",
        dimensions=[len(h.bins)],
        x_categories=boundaries[:-1],
        x_label="Location within measure (quarter notes)",
        y_categories=None,
        y_label="Total duration (quarter notes)"
    )