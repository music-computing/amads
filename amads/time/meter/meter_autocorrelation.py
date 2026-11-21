"""
Autocorrelation-based estimate of meter

Ports the 'meter' function from miditoolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 73-74
"""

import math
from collections.abc import Iterator

import numpy as np

from amads.core.basics import Note, Score
from amads.melody.melodic_accent import melodic_accent

# number of divisions for quarter notes
_quarter_division = 4
# minimal number of intervals
_max_lag = 8


def _internal_ceil(num: float) -> float:
    """
    A modified ceiling function. The problem we have encountered is floating
    point rounding error might cause ceiling to adopt an incorrect value
    compared to the miditoolbox version.
    To fix this, we decide to use this internal ceiling function by introducing
    a little leeway so that any float (let's call y) slightly past a whole float
    (let's call x) gets counted as said whole float.

    Basically if (y - x) < a small delta, our internal ceiling function counts
    y = x, whereas the other behavior for the ceiling function remains unchanged
    when compared to math.ceil().

    Parameters
    ----------
    num : float
        float to apply our modified internal ceiling operation to.
    Returns
    -------
    float
        The modified ceiling of num
    """
    if math.isclose(num, math.floor(num)):
        return math.floor(num)
    else:
        return math.ceil(num)


def _onset_based_value_autocorrelation(
    onset_weight_array: np.array,
) -> np.array:
    """
    Performs autocorrelation on the weight accumulated onset array.
    Facilitates finding metrical peaks among the autocorrelated values.

    Parameters
    ----------
    onset_weight_array: np.array
        The onset-based array with the accumulated values

    Returns
    -------
    np.array
        Subset of autocorrelation array containing all the metrical
        autocorrelated values.
    """
    corr_result = np.correlate(
        onset_weight_array, onset_weight_array, mode="full"
    )
    start_ind = (corr_result.size + 1) // 2
    end_ind = min(corr_result.size, start_ind + _quarter_division * _max_lag)

    autocorrelation = np.zeros(_quarter_division * _max_lag + 1)

    autocorrelation[: end_ind - start_ind + 2] = corr_result[
        start_ind : end_ind + 1
    ]

    return autocorrelation[2::2]


def _onset_value_accumulator(
    value_note_iter: Iterator[tuple[Note, float | int]], max_onset: float
) -> np.array:
    """
    The iterator returns note value pairs of a score according to the
    order of notes iterated in score.find_all(Note).

    This function sets up an array based off of the total onsets of the notes
    within a score (supplied as max_onset). Then, it accumulates the values
    into the array according to quarter note divisions of the maximum onset.

    Parameters
    ----------
    value_note_iter: Iterator
        This iterator supplies a note and its corresponding value to
        accumulate
    max_onset: float
        Maximum note onset for all the notes in the iterator.

    Returns
    -------
    np.array
        The numpy array with the accumulated values
    """
    vlen = _quarter_division * max(2 * _max_lag, _internal_ceil(max_onset) + 2)
    onset_weights = np.zeros(vlen)
    for note, val in value_note_iter:
        ind = round(note.onset * _quarter_division) % vlen
        onset_weights[ind] += val
    return onset_weights


def meter_autocorrelation(
    score: Score, option: str | None = None
) -> int | None:
    """
    Autocorrelation-based estimate of meter.

    Returns an estimate based off of matching autocorrelation-based peaks
    of certain meter heuristics of the score.
    Based on temporal structure and on Thomassen's melodic accent.

    m = 2 for simple duple, m = 3 for simple triple or compound

    The default weighted option uses the note duration heuristic.
    The 'optimal' weighted option use both the melodic accent heuristic and
    constant value (1) heuristic, weighted by a linear combination
    (discriminant) function with weights derived from a collection of 12000
    folk melodies.

    Parameters
    ----------
    score : Score
        score to estimate meter
    option : str | None
        "Optimal" for a mix of melodic accents and constant heuristics.
        None if default, note duration heuristic.

    Returns
    -------
    int | None
        None if score does not meet the requirements for the computation
        2 for simple duple
        3 for simple triple or compound.

    Raises
    ------
    ValueError
        If option is not of the correct type or label.


    References
    ----------
        Brown, J. (1993). Determination of the meter of musical scores by
            autocorrelation. Journal of the Acoustical Society of America,
            94(4), 1953-1957.
        Toiviainen, P., & Eerola, T. (2006). Autocorrelation in meter induction:
            the role of accent structure. Journal of the Acoustical Society of
            America, 119(2), 1164-1170.
    """
    assert score

    score.convert_to_quarters()
    max_onset = max(note.onset for note in score.find_all(Note))
    if option is None:
        note_value_iter = (
            (note, note.duration) for note in score.find_all(Note)
        )
        result = _onset_based_value_autocorrelation(
            _onset_value_accumulator(note_value_iter, max_onset)
        )
        return 2 if result[3] >= result[5] else 3
    elif option.lower() == "optimal":
        if not score.ismonophonic():
            return None
        vanilla_iter = ((note, 1) for note in score.find_all(Note))
        vanilla_result = _onset_based_value_autocorrelation(
            _onset_value_accumulator(vanilla_iter, max_onset)
        )
        annotated_score = melodic_accent(score)
        annotated_str = "melodic_accent"
        melodic_accent_iter = (
            (note, note.get(annotated_str, None))
            for note in annotated_score.find_all(Note)
        )
        melodic_accent_result = _onset_based_value_autocorrelation(
            _onset_value_accumulator(melodic_accent_iter, max_onset)
        )

        # TODO: find out what these numbers mean.
        discriminant = (
            -1.042
            + 0.318 * vanilla_result[2]
            + 5.240 * vanilla_result[3]
            - 0.63 * vanilla_result[5]
            + 0.745 * vanilla_result[7]
            - 8.122 * vanilla_result[11]
            + 4.160 * vanilla_result[15]
        )
        discriminant += (
            0
            + -0.978 * melodic_accent_result[2]
            + 1.018 * melodic_accent_result[3]
            - 1.657 * melodic_accent_result[5]
            + 1.419 * melodic_accent_result[7]
            - 2.205 * melodic_accent_result[11]
            + 1.568 * melodic_accent_result[15]
        )

        return 2 if discriminant >= 0 else 3
    else:
        raise ValueError(f"invalid option {option}! Must be 'Optimal' or None!")
