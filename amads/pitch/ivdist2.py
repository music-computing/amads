"""
Pitch interval transition analysis.

Implements the Midi Toolbox `ivdist2` function

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=64
"""

from typing import cast

from amads.core.basics import Note, Part, Score
from amads.core.distribution import Distribution
from amads.core.histogram import Histogram2D
from amads.pitch.pcdist1 import duraccent


def interval_distribution_2(
    score: Score,
    name: str = "Interval Transition Distribution",
    weighted: bool = True,
    miditoolbox_compatible: bool = True,
) -> Distribution:
    """
    Returns the 2nd-order interval distribution of a musical score.

    Currently, intervals greater than an octave will be ignored.

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
        miditoolbox_compatible introduces four changes to emulate `ivdist2`
        in Midi Toolbox: (1) avoid zero division by initializing bins to
        1e-12 (as opposed to simply skipping division when all bins are
        zero), (2) assume octave (but not direction) equivalence, so the
        intervals +1 and +13 update the same bin (as opposed to ignoring
        intervals larger than an octave), (3) a zero interval (unison) is
        inserted at the beginning of the sequence, (4) the weight is the
        sum of the modified durations of the second interval (as opposed to
        taking the sum of the modified durations of all three notes).

    Returns
    -------
    Distribution
        A 25x25 distribution where where (i,j) represents the normalized
        probabilities of transitioning from interval i to interval j.
        The bins are spaced at semitone distances with the first bin
        representing the downward octave and the last bin representing
        the upward octave. If the score is empty, the function returns
        a list with all elements set to zero.

    Raises
    ------
    ValueError
        If the score is not monophonic (e.g. contains chords)
    """
    if not score.ismonophonic():
        raise ValueError("Error: Score must be monophonic")

    score = cast(Score, score.merge_tied_notes())
    if weighted:
        score.convert_to_seconds()  # need seconds for duraccent function

    initial_value = 1e-12 if miditoolbox_compatible else 0.0
    bin_centers = [float(i - 12) for i in range(25)]  # 25 bins from -12 to +12
    bin_boundaries = [i - 12 - 0.5 for i in range(26)]  # boundaries
    x_categories = [str(c) for c in bin_centers]
    y_categories = x_categories
    h = Histogram2D(bin_centers, bin_boundaries, "linear", True, initial_value)
    for p in score.find_all(Part):
        part: Part = cast(Part, p)
        dur = 0.0  # (this value is never used)
        prev_iv = 0 if miditoolbox_compatible else None  # previous interval
        prev_pitch = None
        prev_dur = 0
        prev_prev_dur = 0
        prev_bin = None
        for n in part.find_all(Note):
            note: Note = cast(Note, n)
            if weighted:
                dur = duraccent(note)
            if prev_pitch is not None:
                iv = round(note.key_num - prev_pitch)
                if miditoolbox_compatible:
                    iv = (abs(iv) % 12) * ((iv > 0) - (iv < 0))
                if weighted:
                    dur = duraccent(note)
                    w = prev_dur + dur
                    if not miditoolbox_compatible:
                        w += prev_prev_dur
                    prev_bin = h.add_point_2d(prev_iv, iv, w, prev_bin)
                    prev_prev_dur = prev_dur
                else:
                    prev_bin = h.add_point_2d(prev_iv, iv, 1.0, prev_bin)
                prev_iv = None if prev_bin is None else iv
            prev_pitch = note.key_num
            prev_dur = dur
    return Distribution(
        name,
        h.bins,
        "interval_transition",
        [25, 25],
        x_categories,  # type: ignore
        "Interval (from)",
        y_categories,  # type: ignore
        "Interval (to)",
    )
