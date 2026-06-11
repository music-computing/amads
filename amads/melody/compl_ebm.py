__author__ = "Yiwen Zhao"

import math
from enum import Enum
from itertools import chain
from typing import List, Optional, Tuple

import numpy as np

import amads.pitch.key.profiles as prof
from amads.algorithms.entropy import entropy
from amads.core.basics import Note, Score
from amads.pitch.ivdist1 import interval_distribution_1
from amads.pitch.key.keymode import keymode
from amads.pitch.pcdist1 import duraccent, pitch_class_distribution_1
from amads.time.durdist1 import duration_distribution_1
from amads.time.notedensity import note_density


class ComplEBMOption(Enum):
    # only pitch complexity is calculated
    PITCH = "p"
    # only rhythm complexity is calculated
    RHYTHM = "r"
    # optimal linearly weighted mix of pitch and rhythm complexity
    OPTIMAL_MIX = "o"


# This global variable eludes me
_GLOBAL_MEAN_VALUE = 5


def _temp_tonality(
    score: Score, profile: prof.KeyProfile = prof.krumhansl_kessler
) -> Score:
    """
    Temporary tonality function for when tonality gets fully implemented
    """
    mode_attributes = keymode(score, profile=prof.krumhansl_kessler)
    profile_coefs = profile[mode_attributes[0]].data
    for note in score.find_all(Note):
        pitch_class = note.pitch_class()
        note.set(profile.name + "_tonality", profile_coefs[pitch_class])
    return score


# TODO: this function can probably be generalized to all functions
def _temp_extract_tonality(
    score: Score, profile: prof.KeyProfile = prof.krumhansl_kessler
) -> Optional[List[float]]:
    """
    extracts tonality elements from an already annotated score
    """
    tonality_list = []
    # auxiliary variable to check if all notes are annotated or only some
    check_counter = 0
    for note in score.find_all(Note):
        property = profile.name + "_tonality"
        note_tonality = note.get(property=property, default=None)
        ++check_counter
        if note_tonality is None:
            if check_counter > 0:
                raise ValueError(
                    "corrupted score has partial tonality annotation"
                )
            return None
        tonality_list.append(note_tonality)
    return tonality_list


def _compute_pitch_components(
    score: Score, profile: prof.KeyProfile
) -> Optional[Tuple[float, float, float, float]]:
    """Calculate pitch-related complexity components."""
    # Extract pitch values
    pitches = np.array([note.keynum for note in score.find_all(Note)])
    if len(pitches) < 2:
        return None

    # Calculate pitch-related features

    # 1. average pitch-interval size
    intervals = np.diff(pitches)
    mean_interval = np.mean(intervals)

    # 2. relative entropy of pitch-class distribution
    score_pcdist = pitch_class_distribution_1(
        score, miditoolbox_compatible=True
    )
    pcdist_entropy = entropy(score_pcdist.data, miditoolbox_compatible=True)

    # 3. relative entropy of interval distribution
    score_ivdist = interval_distribution_1(score, miditoolbox_compatible=True)
    ivdist_entropy = entropy(score_ivdist.data, miditoolbox_compatible=True)

    # 4. mean tonality (weighted by accented duration)
    annotated_score = _temp_tonality(score, profile)

    property = profile.name + "_tonality"
    try:
        tonality_iter = (
            duraccent(note) * note.get(property=property, default=None)
            for note in annotated_score.find_all(Note)
        )
        mean_tonality = sum(tonality_iter) / len(pitches)
    except TypeError:
        raise RuntimeError(
            "invalid results from tonality function "
            "(not all notes have been annotated with tonality)"
        )

    # Combine features with empirically derived weights
    return mean_interval, pcdist_entropy, ivdist_entropy, 1 / mean_tonality


def _compute_rhythm_components(
    score: Score,
) -> Optional[Tuple[float, float, float, float]]:
    """Calculate rhythm-related complexity components."""
    notes = score.get_sorted_notes()
    if len(notes) < 2:
        return 0

    # Extract duration values
    # 1. duration distribution entropy
    durdist_data = duration_distribution_1(
        score, miditoolbox_compatible=True
    ).data
    durdist_entropy = entropy(durdist_data, miditoolbox_compatible=True)

    # 2. Note Density
    note_dens = note_density(score, timetype="seconds")

    # 3. rhythmic variation throughout the score
    original_timestate = score.units_are_quarters()
    if original_timestate:
        score.convert_to_seconds()
    assert score.units_are_seconds()
    value_iter = (
        math.log(note.duration) if note.duration > 0 else math.nan
        for note in score.find_all(Note)
    )
    rhythm_variation = np.nanstd(np.array(value_iter))
    if original_timestate:
        score.convert_to_quarters()

    # 4. meter accent
    # TODO: get meter accent implemented...
    score_meter_accent = 0

    return durdist_entropy, note_dens, rhythm_variation, score_meter_accent


def compl_ebm(
    score: Score,
    profile: prof.Profile = prof.KrumhanslKessler,
    method: ComplEBMOption = ComplEBMOption.OPTIMAL_MIX,
) -> float:
    """
    Calculate the expectancy-based model of melodic complexity.

    This function implements the complexity model from Eerola & North (2000),
    which can analyze either pitch-related components, rhythm-related components,
    or their optimal combination. The output is calibrated against the Essen
    collection (mean=5, std=1).

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.
    profile : prof.Profile
        The Key Profile for which to measure tonality from.
    method : ComplEBMOption
        The method to use for complexity calculation:
        - ComplEBMOption.PITCH: pitch-related components only
        - ComplEBMOption.RHYTHM: rhythm-related components only
        - ComplEBMOption.OPTIMAL_MIX: linear combination of pitch
        complexity and rhythm complexity with predetermined weights
        (default; as to what it's supposed to be optimal in, that beats me...)

    Returns
    -------
    float
        Complexity value calibrated relative to the Essen Collection.
        Higher values indicate higher complexity.
        Returns 0 for empty scores or single notes.

    References
    ----------
    .. [1] Eerola, T. & North, A. C. (2000). Expectancy-Based Model of Melodic
           Complexity. In Proceedings of the Sixth International Conference on
           Music Perception and Cognition.
    .. [2] Schaffrath, H. (1995). The Essen folksong collection in kern format.

    Examples
    --------
    >>> score = Score.from_melody([60, 64, 67])
    >>> complexity = compl_ebm(score, ComplEBMOption.PITCH)
    >>> print(complexity)
    4.8
    """

    # Flatten and collapse the score into a single sequence of notes
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Handle empty scores or single notes
    if len(notes) < 2:
        return None

    # Calculate complexity based on selected method
    match method:
        case ComplEBMOption.PITCH:
            # the linear weights assigned to the different pitch components
            # in pitch complexity
            weights = (0.3, 1, 0.8, 1)
            offset = -0.2407
            divisor = 0.9040  # standard deviation of pitches (in Essen)?
            pitch_components = _compute_pitch_components(score, profile)
            complexity = offset + sum(
                weight * component
                for weight, component in zip(weights, pitch_components)
            )
            complexity /= divisor
        case ComplEBMOption.RHYTHM:
            # the linear weights assigned to the different pitch components
            # in rhythm complexity
            weights = (0.7, 0.2, 0.5, 0.5)
            offset = -0.7841
            divisor = 0.3637  # standard deviation of durations (in Essen)?
            rhythm_components = _compute_rhythm_components(score)
            complexity = offset + sum(
                weight * component
                for weight, component in zip(weights, rhythm_components)
            )
            complexity /= divisor
        case ComplEBMOption.OPTIMAL_MIX:
            pitch_weights = (0.2, 1.5, 1.3, -1)
            rhythm_weights = (0.5, 0.4, 0.9, 0.8)
            offset = -1.9025
            divisor = 1.5034

            pitch_components = _compute_pitch_components(score, profile)
            rhythm_components = _compute_rhythm_components(score)

            component_values = chain(pitch_components, rhythm_components)
            component_weights = chain(pitch_weights, rhythm_weights)

            complexity = offset + sum(
                weight * component
                for weight, component in zip(
                    component_weights, component_values
                )
            )
            complexity /= divisor
            assert 0
        case _:
            return None

    calibrated_complexity = complexity + _GLOBAL_MEAN_VALUE

    return calibrated_complexity
