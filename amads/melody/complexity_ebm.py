"""
Expectation-based model for melodic complexity.

Ports the `complebm` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 54.
"""

import math
from enum import Enum
from itertools import chain, dropwhile, islice, pairwise
from statistics import mean, stdev

from amads.algorithms.entropy import entropy
from amads.core.basics import Note, Score
from amads.pitch.ivdist1 import interval_distribution_1
from amads.pitch.key.tonality import tonality
from amads.pitch.pcdist1 import duraccent, pitch_class_distribution_1
from amads.time.durdist1 import duration_distribution_1
from amads.time.meter.meter_accent import meter_accent
from amads.time.notedensity import note_density


class ComplexityEBMOption(Enum):
    """
    Calculation options for complexity_ebm invocation

    Attributes
    ----------
    PITCH : str, class attribute
        only pitch components are included in the complexity calculation
        with predetermined weights
    RHYTHM : str, class attribute
        only rhythm components are included in the complexity calculation
        with predetermined weights
    OPTIMAL_MIX : List[str], class attribute
        both pitch and rhythm components are included in the complexity
        calculation with predetermined weights
    """

    PITCH = "p"
    RHYTHM = "r"
    OPTIMAL_MIX = "o"


# Global mean of essen (don't know what this mean is of though)
_GLOBAL_MEAN_VALUE = 5


def _compute_pitch_components(
    score: Score,
) -> tuple[float, float, float, float] | None:
    """
    Calculate pitch-related complexity components.

    Parameters
    ----------
    score : Score
        A monophonic Score object containing the melody to analyze.

    Returns
    -------
    Optional[Tuple[float, float, float, float]]
        Pitch components that are used in the expectation-based model for
        melodic complexity. Namely, returns (in the following order):
        (1) average pitch-interval size
        (2) relative entropy of pitch-class distribution
        (3) relative entropy of pitch-interval distribution
        (4) mean tonality of all the notes in the score
        (weighted by Parncutt's durational accent)

        Returns None for empty scores or single notes.
    """
    # check if there are at least 2 notes in the score
    if len(list(islice(score.find_all(Note), 2))) < 2:
        return None

    # Calculate pitch-related features

    # 1. average pitch-interval size
    pitches_pairwise = pairwise(note.midi_num for note in score.find_all(Note))
    mean_interval = mean(next - current for current, next in pitches_pairwise)

    # 2. relative entropy of pitch-class distribution
    score_pcdist = pitch_class_distribution_1(
        score, miditoolbox_compatible=True
    )
    pcdist_entropy = entropy(score_pcdist.data, miditoolbox_compatible=True)

    # 3. relative entropy of pitch-interval distribution
    score_ivdist = interval_distribution_1(score, miditoolbox_compatible=True)
    ivdist_entropy = entropy(score_ivdist.data, miditoolbox_compatible=True)

    original_timestate = score.units_are_quarters
    if original_timestate:
        score.convert_to_seconds()

    # 4. mean tonality (weighted by accented duration)
    tonality_list = tonality(score)

    tonality_iter = (
        duraccent(note) * tonality_val
        for note, tonality_val in zip(score.find_all(Note), tonality_list)
    )
    mean_tonality = mean(tonality_iter)
    if original_timestate:
        score.convert_to_quarters()

    # Combine features with empirically derived weights
    return mean_interval, pcdist_entropy, ivdist_entropy, mean_tonality


def _compute_rhythm_components(
    score: Score,
) -> tuple[float, float, float, float] | None:
    """
    Calculate rhythm-related complexity components.

    Parameters
    ----------
    score : Score
        A monophonic Score object containing the melody to analyze.

    Returns
    -------
    Optional[Tuple[float, float, float, float]]
        Rhythm and time-based components that are used in the expectation-based
        model for melodic complexity. Namely, returns (in the following order):
        (1) relative entropy of duration distribution (see durdist1.py for more
        details)
        (2) note density
        (3) rhythmic variation throughout the score
        (can potentially be its own function)
        (4) meter accent of the score

        Returns None for empty scores or single notes.
    """
    # check if there are at least 2 notes in the score
    if len(list(islice(score.find_all(Note), 2))) < 2:
        return None

    # Extract duration values
    # 1. duration distribution entropy
    durdist_data = duration_distribution_1(
        score, miditoolbox_compatible=True
    ).data
    durdist_entropy = entropy(durdist_data, miditoolbox_compatible=True)

    # 2. Note Density
    note_dens = note_density(score, timetype="seconds")

    # 3. rhythmic variation throughout the score
    original_timestate = score.units_are_quarters
    if original_timestate:
        score.convert_to_seconds()
    value_iter = (
        math.log(note.duration) if note.duration > 0 else math.nan
        for note in score.find_all(Note)
    )

    rhythm_variation = stdev(dropwhile(lambda a: math.isnan(a), value_iter))

    if original_timestate:
        score.convert_to_quarters()

    # 4. meter accent
    score_meter_accent = meter_accent(score)

    return durdist_entropy, note_dens, rhythm_variation, score_meter_accent


def complexity_ebm(
    score: Score,
    method: ComplexityEBMOption = ComplexityEBMOption.OPTIMAL_MIX,
) -> float:
    """
    Calculate the expectancy-based model of melodic complexity.

    This function implements the complexity model from Eerola & North (2000),
    which can analyze either pitch-related components, rhythm-related components,
    or their optimal combination. The output is calibrated against the Essen
    collection (mean=5, std=1).

    The miditoolbox version contains a bug in the optimal ('o') option, where the
    entropy of the pitch-class distribution (through pcdist1) was calculated
    as entropy of the interval distribution (through ivdist1).

    Parameters
    ----------
    score : Score
        A monophonic Score object containing the melody to analyze.
    method : ComplEBMOption
        The method to use for complexity calculation:
        - ComplexityEBMOption.PITCH: pitch-related components only
        - ComplexityEBMOption.RHYTHM: rhythm-related components only
        - ComplexityEBMOption.OPTIMAL_MIX: linear combination of pitch
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
        Eerola, T. & North, A. C. (2000). Expectancy-Based Model of Melodic
            Complexity. In Proceedings of the Sixth International Conference on
            Music Perception and Cognition.
        Schaffrath, H. (1995). The Essen folksong collection in kern format.
    """

    if not score.ismonophonic():
        return None

    # Calculate complexity based on selected method
    match method:
        case ComplexityEBMOption.PITCH:
            # the linear weights assigned to the different pitch components
            # in pitch complexity
            weights = (0.3, 1, 0.8, -1)
            offset = -0.2407
            divisor = 0.9040  # standard deviation of pitches (in Essen)?
            pitch_components = _compute_pitch_components(score)
            if pitch_components is None:
                return None
            complexity = offset + sum(
                weight * component
                for weight, component in zip(weights, pitch_components)
            )
            complexity /= divisor
        case ComplexityEBMOption.RHYTHM:
            # the linear weights assigned to the different pitch components
            # in rhythm complexity
            weights = (0.7, 0.2, 0.5, 0.5)
            offset = -0.7841
            divisor = 0.3637  # standard deviation of durations (in Essen)?
            rhythm_components = _compute_rhythm_components(score)
            if rhythm_components is None:
                return None
            complexity = offset + sum(
                weight * component
                for weight, component in zip(weights, rhythm_components)
            )
            complexity /= divisor
        case ComplexityEBMOption.OPTIMAL_MIX:
            pitch_weights = (0.2, 1.5, 1.3, -1)
            rhythm_weights = (0.5, 0.4, 0.9, 0.8)
            offset = -1.9025
            divisor = 1.5034

            pitch_components = _compute_pitch_components(score)
            rhythm_components = _compute_rhythm_components(score)
            if pitch_components is None or rhythm_components is None:
                return None

            component_values = chain(pitch_components, rhythm_components)
            component_weights = chain(pitch_weights, rhythm_weights)

            complexity = offset + sum(
                weight * component
                for weight, component in zip(
                    component_weights, component_values
                )
            )
            complexity /= divisor
        case _:
            return None

    calibrated_complexity = complexity + _GLOBAL_MEAN_VALUE

    return calibrated_complexity
