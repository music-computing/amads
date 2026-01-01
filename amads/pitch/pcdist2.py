"""
This module provides the `pitch_class_distribution_2` function.

Implements the Midi Toolbox `pcdist2` function.

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=81.
"""

from typing import cast

from amads.core.basics import Note, Part, Score
from amads.core.distribution import Distribution
from amads.core.histogram import Histogram2D
from amads.pitch.pcdist1 import duraccent


def update_pcd(pcd: list[list[float]], notes: list[Note], weighted: bool):
    """Updates the pitch-class distribution matrix based on the given notes.

    Serves as a helper function for `pitch_class_distribution_2`

    Args:
        pcd (list[list[float]]): The pitch-class distribution matrix to be
                                 updated.
        notes (list[Note]): The list of notes to process.
        weighted (bool, optional): If True, the pitch-class distribution is
                                   weighted by note durations.
    """
    prev = None
    for note in notes:
        if prev:
            pc_curr = note.pitch_class
            pc_prev = prev.pitch_class

            if weighted:
                pcd[pc_prev][pc_curr] += prev.duration * note.duration
            else:
                pcd[pc_prev][pc_curr] += 1

        prev = note


def pitch_class_distribution_2(
    score: Score,
    name: str = "Pitch Class Distribution",
    weighted: bool = True,
    miditoolbox_compatible: bool = False,
) -> Distribution:
    """Returns the 2nd order pitch-class distribution of a musical score.

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
        If True, bins are initialized with 1e-12 to avoid division by
        zero. If False and all bins are zero, division is avoided and
        the resulting bins remain all zero. Default is False.

    Returns
    -------
    Distribution
        A 12x12 distribution representing the transition probabilities of
        each pitch class (C, C#, D, D#, E, F, F#, G, G#, A, A#, B). If the
        score is empty, the function returns a distribution with all
        elements set to zero.
    """
    score = cast(Score, score.merge_tied_notes())
    if weighted:
        score.convert_to_seconds()  # need seconds for duraccent calculation
    initial_value = 1e-12 if miditoolbox_compatible else 0.0
    bin_centers = [float(i) for i in range(12)]  # 25 bins from -12 to +12
    x_categories = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]
    h = Histogram2D(bin_centers, None, "linear", False, initial_value)

    # do not count transitions from one part to the next
    for p in score.find_all(Part):
        part: Part = cast(Part, p)
        prev_bin = None
        prev_pc = None
        prev_dur = None
        for n in part.find_all(Note):
            note: Note = cast(Note, n)
            pc = note.pitch_class
            if weighted and prev_pc is not None:
                dur = duraccent(note)
                w = prev_dur + dur  # type: ignore
                prev_dur = dur
            else:
                w = 1.0
            prev_bin = h.add_point_2d(prev_pc, pc, w, prev_bin)
            prev_pc = pc

    # normalize
    h.normalize()

    return Distribution(
        name,
        h.bins,
        "pitch_class_transition",
        [12, 12],
        x_categories,  # type: ignore
        "Current Pitch Class",
        x_categories,  # type: ignore
        "Previous Pitch Class",
    )
