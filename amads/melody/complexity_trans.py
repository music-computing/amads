"""
Complexity of pitch-class transitions within a score.

Ports the `compltrans` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 55.
"""

from typing import Optional

import numpy as np

from amads.algorithms.nnotes import nnotes
from amads.core.basics import Note, Score
from amads.core.distribution import Distribution
from amads.core.pitch import CHROMATIC_NAMES, NUM_PITCH_CLASSES

"""
Simonton's pitch-transition probabilities (summarized from 15618 classical music
themes) from his 1984 paper. Deviating from the original paper is, all other
transitions that fall within minor or major scale (plus F#G and GF#) is set to
probability of 0.05.
"""
_simonton_transitions = [
    [0.053, 0, 0.044, 0.005, 0.022, 0, 0, 0.032, 0.005, 0, 0.005, 0.032],
    [0, 0, 0, 0.005, 0, 0, 0, 0, 0.005, 0, 0.005, 0],
    [0.0300, 0, 0.0110, 0.0140, 0.0240, 0, 0, 0, 0.0050, 0, 0.0050, 0],
    [
        0.05,
        0.05,
        0.18,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
    ],
    [0.016, 0, 0.03, 0.005, 0.03, 0.028, 0, 0.026, 0.005, 0, 0.005, 0],
    [0, 0, 0, 0.005, 0.021, 0, 0, 0.021, 0.005, 0, 0.005, 0],
    [0, 0, 0, 0.005, 0, 0, 0, 0.005, 0.005, 0, 0.005, 0],
    [
        0.049,
        0,
        0,
        0.005,
        0.029,
        0.031,
        0.005,
        0.067,
        0.005,
        0.029,
        0.005,
        0,
    ],
    [
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.011,
        0.005,
        0.005,
        0.005,
        0.005,
    ],
    [0, 0, 0, 0.005, 0, 0, 0, 0.02, 0.005, 0, 0.005, 0.012],
    [
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
        0.005,
    ],
    [0.023, 0, 0, 0.005, 0, 0, 0, 0, 0.005, 0.011, 0.005, 0],
]

"""
Distribution object for Simonton (1984) pitch class transition probabilities,
analyzed from 15,618 classical themes.
"""
simonton_transition_dist = Distribution(
    name="Simonton (1984)",
    data=_simonton_transitions,
    distribution_type="pitch_class_transition",
    dimensions=(NUM_PITCH_CLASSES, NUM_PITCH_CLASSES),
    x_categories=CHROMATIC_NAMES,
    x_label="Starting Pitch Class",
    y_categories=CHROMATIC_NAMES,
    y_label="Ending Pitch Class",
)


def complexity_trans(score: Score) -> Optional[float]:
    """
    Calculate Simonton's complexity originality score based on 2nd order
    pitch-class transition probabilities derived from classical themes.

    This function implements Simonton's (1984, 1994) measure of melodic
    originality using transition probabilities derived from analysis of
    15,618 classical themes. Higher values indicate more original/unusual
    melodic transitions.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.

    Returns
    -------
    float
        Melodic originality score scaled between 0 and 10.
        Higher values indicate higher melodic originality.
        Returns 0 for empty scores or sequences shorter than 3 notes.

    References
    ----------
    .. [1] Simonton, D. K. (1984). Melodic structure and note transition
           probabilities: A content analysis of 15,618 classical themes.
           Psychology of Music, 12, 3-16.
    .. [2] Simonton, D. K. (1994). Computer content analysis of melodic
           structure: Classical composers and their compositions.
           Psychology of Music, 22, 31-43.
    """
    if not score.ismonophonic():
        return None
    num_notes = nnotes(score)
    if num_notes < 2:
        return None

    note_iter = score.find_all(Note)
    next_note_iter = score.find_all(Note)
    if next(next_note_iter, None) is None:
        return None
    pitch_transition_sums = np.zeros(simonton_transition_dist.dimensions)
    for note, next_note in zip(note_iter, next_note_iter):
        assert isinstance(note, Note) and isinstance(next_note, Note)
        current_pc = note.pitch_class
        next_pc = next_note.pitch_class
        print(f"{current_pc}, {next_pc}")
        pitch_transition_sums[current_pc, next_pc] += 1

    simonton_dist_data = np.array(simonton_transition_dist.data)
    assert simonton_dist_data.shape == pitch_transition_sums.shape

    # takes the weighted average of transition probabilities with our data
    # and change the result's sign.
    weighted_transition_avg = np.sum(simonton_dist_data * pitch_transition_sums)
    weighted_transition_avg /= (num_notes - 1) * -1
    # scaled from 0-10 (10=complex)
    # numbers copied directly from the matlab version (in compltrans.m).
    scaled_transition_weight = (weighted_transition_avg + 0.0530) * 188.68

    return scaled_transition_weight
