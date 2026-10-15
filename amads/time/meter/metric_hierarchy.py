"""
Locations of the notes in a score within the metric hierarchy

Ports the `metrichierarchy` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 75.
"""

import math
from collections.abc import Iterator

import numpy as np

from amads.core.basics import Note, Score
from amads.time.meter.meter_autocorrelation import meter_autocorrelation


def _onset_meter_estimate(
    score: Score, miditoolbox_compatible: bool = True
) -> Iterator[tuple[float, Note]]:
    """
    Returns an iterator for meter estimation according to the note onset
    and duration.

    Parameters
    ----------
    score : Score
        A Score object to estimate the onset meter.
    miditoolbox_compatible : bool
        Whether or not our calculatiosn are compatible with the original
        miditoolbox version.

    Returns
    -------
    Iterator[tuple[float, Note]]
        An iterator that yields the meter estimate value and the corresponding
        note in the order they are presented in score.find_all(Note)
    """
    meter_estimate = meter_autocorrelation(score)

    # each meter has 4 quarter notes per meter estimate
    meter_accumulator = np.zeros(4 * meter_estimate)

    for note in score.find_all(Note):
        if miditoolbox_compatible:
            # correction needs to be made because notes in miditoolbox NMATs
            # start at onset 1...
            note_onset = (note.onset + 1) % meter_estimate
        else:
            note_onset = note.onset % meter_estimate
        ind = (round(note_onset * 4)) % (4 * meter_estimate)
        meter_accumulator[ind] += note.duration

    max_ind = np.argmax(meter_accumulator)

    if miditoolbox_compatible:
        return (
            ((note.onset + 1 - max_ind * 0.25) % meter_estimate, note)
            for note in score.find_all(Note)
        )
    else:
        return (
            ((note.onset - max_ind * 0.25) % meter_estimate, note)
            for note in score.find_all(Note)
        )


def metric_hierarchy(
    score: Score, miditoolbox_compatible: bool = True
) -> Score | None:
    """
    Each note in the score belongs to a metric hierarchy measured from 0 to 5,
    where 5 is the strongest and 0 is the weakest in the hierarchy.
    This function computes the metric hierarchy value of each note in the score
    and annotates the note with its hierarchy under the label "metric_hierarchy".

    Intuitively, the metric hierarchy reflects how strong the "beat" of a note
    is in the score.

    Parameters
    ----------
    score : Score
        A Score object containing the notes to estimate metric hierarchy.
    miditoolbox_compatible : bool
        Whether or not our calculatiosn are compatible with the original
        miditoolbox version.

    Returns
    -------
    Score | None
        Annotated score, where each note is annotated with its corresponding
        metric hierarchy under the "metric_hierarchy" label.
    """
    if next(score.find_all(Note), None) is None:
        return None
    estimate_iter = _onset_meter_estimate(score, miditoolbox_compatible)
    # easy accumulation after getting onset meter estimate.
    for estimate, note in estimate_iter:
        # count the number of times the estimate hits the boundary?
        current_hierarchy = math.isclose(estimate, 0, rel_tol=0, abs_tol=1e-6)
        for _ in range(4):
            current_hierarchy += math.isclose(
                estimate, round(estimate), rel_tol=0, abs_tol=1e-6
            )
            estimate *= 2
        note.set("metric_hierarchy", current_hierarchy)
    return score
