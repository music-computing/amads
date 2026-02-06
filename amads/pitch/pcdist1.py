"""
Pitch class distribution analysis.

Implements the Midi Toolbox `pcdist1` function.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=80.
"""

import math
from typing import cast

from amads.core.basics import Note, Score
from amads.core.distribution import Distribution
from amads.core.histogram import Histogram1D
from amads.core.pitch import CHROMATIC_NAMES


def duraccent(note: Note) -> float:
    """
    Calculate Parncutt's durational accent (1994) for a note.

    Based on Matlab MIDI Toolbox implementation.

    References
    ----------

    - Parncutt, R. (1994). A perceptual model of pulse salience and
      metrical accent in musical rhythms. *Music Perception*. 11(4), 409-464.

    Parameters
    ----------
    note : Note
        The note for which to calculate the durational accent.

    Returns
    -------
    float
        The durational accent value.
    """
    accent = 1 - math.exp(-note.duration / 0.5) ** 2
    return accent


def pitch_class_distribution_1(
    score: Score,
    name: str = "Pitch Class Distribution",
    weighted: bool = True,
    miditoolbox_compatible: bool = False,
) -> Distribution:
    """
    Calculate the pitch-class distribution of a note collection.

    Parameters
    ----------
    score : Score
        The musical score to analyze
    name : str
        Name for the distribution; plot title if plotted.
    weighted : bool, optional
        If True, weight the pitch-class distribution by note durations
        in seconds that are modified according to Parncutt's durational
        accent model (1994), by default True.
    miditoolbox_compatible : bool
        Matlab MIDI Toolbox avoids zero division by dividing counts
        by the total count plus (1e-12 times the number of bins).
        True enables this behavior. Default is False, which simply skips
        division when the total count is zero (this also returns a
        zero matrix when the count is zero).

    Returns
    -------
    Distribution
        A 12-element distribution representing the probabilities of each
        pitch class (C, C#, D, D#, E, F, F#, G, G#, A, A#, B). If the score
        is empty, the function returns a list with all elements set to zero.
    """
    score = cast(Score, score.merge_tied_notes())
    if weighted:
        score.convert_to_seconds()  # need seconds for duraccent calculation
    initial_value = 1e-12 if miditoolbox_compatible else 0.0
    bin_centers = [float(i) for i in range(12)]  # 25 bins from -12 to +12
    xcategories = CHROMATIC_NAMES
    h = Histogram1D(bin_centers, None, "linear", False, initial_value)

    for note in score.find_all(Note):
        note = cast(Note, note)
        h.add_point(
            round(note.pitch_class) % 12, duraccent(note) if weighted else 1.0
        )

    if miditoolbox_compatible:  # miditoolbox "normalization"
        total = sum(h.bins) + len(h.bins) * 1e-12
        h.bins = [b / total for b in h.bins]
    else:  # normalize normally
        h.normalize()

    # xcategories is List[str], but Distribution takes int | float | str
    return Distribution(
        name,
        h.bins,
        "pitch_class",
        [12],
        xcategories,  # type: ignore
        "Pitch Class",
        None,
        "Proportion",
    )
