"""
Pitch interval analysis.

Implements the Midi Toolbox `ivdist1` function

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=63
"""

from typing import cast

from amads.core.basics import Note, Part, Score
from amads.core.distribution import Distribution
from amads.core.histogram import Histogram1D
from amads.pitch.pcdist1 import duraccent


def interval_distribution_1(
    score: Score,
    name: str = "Interval Distribution",
    weighted: bool = True,
    miditoolbox_compatible: bool = True,
) -> Distribution:
    """
    Returns the interval distribution of a musical score.

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
        Matlab MIDI Toolbox avoids zero division by dividing counts
        by the total count plus 1e-12 times the number of counts.
        True enables this behavior. Default is False, which simply skips
        division when the total count is zero (this also returns a
        zero matrix when the count is zero).

    Returns
    -------
    Distribution
        A 25-bin distribution representing the probabilities of each pitch
        interval. The bins are spaced at semitone distances with the first
        bin representing the downward octave and the last bin representing
        the upward octave. If the score is empty, the function returns a
        list with all elements set to zero.

    Raises
    ------
    ValueError
        If the score is not monophonic (e.g. contains chords)
    """
    if not score.ismonophonic():
        raise ValueError("Error: Score must be monophonic")

    score = cast(Score, score.merge_tied_notes())
    if weighted:
        score.convert_to_seconds()

    initial_value = 1e-12 if miditoolbox_compatible else 0.0
    bin_centers = [float(i - 12) for i in range(25)]  # 25 bins from -12 to +12
    bin_boundaries = [i - 12 - 0.5 for i in range(26)]  # boundaries
    x_categories = [str(c) for c in bin_centers]
    h = Histogram1D(bin_centers, bin_boundaries, "linear", True, initial_value)

    for p in score.find_all(Part):
        part: Part = cast(Part, p)
        prev_pitch = None
        prev_dur = None
        for n in part.find_all(Note):
            note: Note = cast(Note, n)
            if prev_pitch is not None:
                iv = round(note.key_num - prev_pitch)
                if miditoolbox_compatible:
                    iv = (abs(iv) % 12) * ((iv > 0) - (iv < 0))
                # otherwise, diff may be ignored by h.add_point
                if weighted:
                    dur = duraccent(note)
                    # prev_dur cannot be None here since prev_pitch is not None
                    h.add_point(iv, prev_dur + dur)  # type: ignore
                    prev_dur = dur
                else:
                    h.add_point(iv, 1.0)
            prev_pitch = note.key_num
            if weighted and prev_dur is None:
                prev_dur = duraccent(note)

    # normalize
    h.normalize()

    return Distribution(
        name,
        h.bins,
        "interval",
        [len(h.bins)],
        x_categories,  # type: ignore
        "Interval (semitones)",
        None,
        "Proportion",
    )
