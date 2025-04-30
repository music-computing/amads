from collections import Counter
from typing import Dict

import numpy as np

from amads.algorithms.mtype_tokenizer import FantasticTokenizer
from amads.algorithms.ngrams import NGramCounter
from amads.core.basics import Note, Score
from amads.melody.contour.huron_contour import HuronContour
from amads.melody.contour.interpolation_contour import InterpolationContour
from amads.melody.contour.parsons_contour import ParsonsContour
from amads.melody.contour.polynomial_contour import PolynomialContour
from amads.melody.contour.step_contour import StepContour
from amads.melody.segment import fantastic_segmenter

__author__ = "David Whyatt"


def fantastic_pitch_features(score: Score) -> Dict:
    """Extract pitch features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract pitch features from.

    Returns
    -------
    Dict
        A dictionary of pitch features.
        Dictionary keys:
            - pitch_range: The range of pitches in the melody.
            - pitch_std: The standard deviation of the pitches in the melody.
            - pitch_entropy: A variant of the Shannon entropy of the pitches in the melody.
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    pitches = [note.pitch.num for note in notes]

    pitch_range = max(pitches) - min(pitches)
    pitch_std = np.std(pitches)

    # Calculate pitch entropy using Shannon's formula
    # First get frequency distribution of pitches
    pitch_counts = Counter(pitches)
    total_pitches = len(pitches)

    # Calculate relative frequencies
    pitch_freqs = {p: count / total_pitches for p, count in pitch_counts.items()}

    # Calculate entropy using the formula from the FANTASTIC toolbox
    pitch_entropy = -sum(f * np.log2(f) for f in pitch_freqs.values()) / np.log2(24)

    return {
        "pitch_range": pitch_range,
        "pitch_std": pitch_std,
        "pitch_entropy": pitch_entropy,
    }


def fantastic_pitch_interval_features(score: Score) -> Dict:
    """Extract pitch interval features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract pitch interval features from.

    Returns
    -------
    Dict
        A dictionary of pitch interval features.
        Dictionary keys:
            - absolute_interval_range: The range of absolute pitch intervals in the melody.
            - mean_absolute_interval: The mean of the absolute pitch intervals in the melody.
            - std_absolute_interval: The standard deviation of the absolute pitch intervals in the melody.
            - modal_interval: The modal absolute pitch interval in the melody.
            - interval_entropy: A variant of the Shannon entropy of the absolute pitch intervals in the melody.
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    pitches = [note.pitch.num for note in notes]
    # Fantastic defines intervals by looking forwards
    intervals = [pitches[i + 1] - pitches[i] for i in range(len(pitches) - 1)]
    # and then always uses the absolute value
    abs_intervals = [abs(interval) for interval in intervals]

    absolute_interval_range = max(abs_intervals) - min(abs_intervals)
    mean_absolute_interval = np.mean(abs_intervals)
    std_absolute_interval = np.std(abs_intervals)
    modal_interval = max(set(abs_intervals), key=abs_intervals.count)

    # Calculate interval entropy using Shannon's formula
    # First get frequency distribution of intervals
    interval_counts = Counter(abs_intervals)
    total_intervals = len(abs_intervals)

    # Calculate relative frequencies
    interval_freqs = {
        i: count / total_intervals for i, count in interval_counts.items()
    }

    # Calculate entropy using the formula from the FANTASTIC toolbox
    # Note that the maximum number of different intervals is instead 23 here
    interval_entropy = -sum(f * np.log2(f) for f in interval_freqs.values()) / np.log2(
        23
    )

    return {
        "absolute_interval_range": absolute_interval_range,
        "mean_absolute_interval": mean_absolute_interval,
        "std_absolute_interval": std_absolute_interval,
        "modal_interval": modal_interval,
        "interval_entropy": interval_entropy,
    }


def fantastic_duration_features(score: Score) -> Dict:
    """Extract duration features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract duration features from.

    Returns
    -------
    Dict
        A dictionary of duration features.
        Dictionary keys:
    """

    raise NotImplementedError("Not implemented yet")
    # Fantastic mixes between duration in seconds and metrical tatums
    # Until issue #75 is resolved, we will not implement this function for now


def fantastic_global_features(score: Score) -> Dict:
    """Extract global extension features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract global extension features from.

    Returns
    -------
    Dict
        A dictionary of global extension features.
        Dictionary keys:
    """

    raise NotImplementedError("Not implemented yet")
    # As before, until issue #75 is resolved, we will not implement this function


def fantastic_step_contour_features(score: Score) -> Dict:
    """Extract step contour features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract step contour features from.

    Returns
    -------
    Dict
        A dictionary of step contour features.
        Dictionary keys:
            - global_variation: The global variation of the step contour.
            - global_direction: The global direction of the step contour.
            - local_variation: The local variation of the step contour.
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Extract pitches and times for contour calculation
    pitches = [note.pitch.num for note in notes]
    durations = [note.duration for note in notes]

    sc = StepContour(pitches, durations)

    return {
        "global_variation": sc.global_variation,
        "global_direction": sc.global_direction,
        "local_variation": sc.local_variation,
    }


def fantastic_interpolation_contour_features(score: Score) -> Dict:
    """Extract interpolation contour features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract interpolation contour features from.

    Returns
    -------
    Dict
        A dictionary of interpolation contour features.
        Dictionary keys:
            - global_direction: The global direction of the interpolation contour.
            - mean_gradient: The mean gradient of the interpolation contour.
            - gradient_std: The standard deviation of the gradient of the interpolation contour.
            - direction_changes: The number of direction changes in the interpolation contour.
            - class_label: The class label of the interpolation contour.
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Extract pitches and times for contour calculation
    pitches = [note.pitch.num for note in notes]
    times = [note.onset for note in notes]

    # Calculate contour
    ic = InterpolationContour(pitches, times, method="fantastic")

    return {
        # Interpolation contour features
        "global_direction": ic.global_direction,
        "mean_gradient": ic.mean_gradient,
        "gradient_std": ic.gradient_std,
        "direction_changes": ic.direction_changes,
        "class_label": ic.class_label,
    }


def fantastic_parsons_contour_features(
    score: Score, character_dict: Dict = None, initial_asterisk: bool = False
) -> Dict:
    """Extract Parsons contour features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract Parsons contour features from.

    Returns
    -------
    Dict
        A dictionary of Parsons contour features.
        Dictionary keys:
            - interval_sequence: The interval sequence of the melody.
            - interval_sequence_sign: A representation of the direction of the interval sequence
                using -1, 0, and 1 to represent down, repeat, and up intervals respectively.
            - as_string: The Parsons contour as a string, using the characters u, r, and d
                to represent up, repeat, and down intervals respectively.
    """

    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    pitches = [note.pitch.num for note in notes]
    pc = ParsonsContour(
        pitches, character_dict=character_dict, initial_asterisk=initial_asterisk
    )

    return {
        "interval_sequence": pc.interval_sequence,
        "interval_sequence_sign": pc.interval_sequence_sign,
        "as_string": pc.as_string,
    }


def fantastic_polynomial_contour_features(score: Score) -> Dict:
    """Extract polynomial contour features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract polynomial contour features from.

    Returns
    -------
    Dict
        A dictionary of polynomial contour coefficients.
        Dictionary keys:
            - coefficients: The coefficients of the polynomial contour.
    """

    pc = PolynomialContour(score)

    return {
        "coefficients": pc.coefficients,
    }


def fantastic_huron_contour_features(score: Score) -> Dict:
    """Extract Huron contour features from a melody.

    Parameters
    ----------
    score : Score
        The score to extract Huron contour features from.

    Returns
    -------
    Dict
        A dictionary of Huron contour features.
        Dictionary keys:
            - first_pitch: The first pitch of the melody.
            - mean_pitch: The mean pitch of the melody.
            - last_pitch: The last pitch of the melody.
            - first_to_mean: The difference between the first and mean pitch.
            - mean_to_last: The difference between the mean and last pitch.
            - contour_class: The class of the Huron contour.
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    pitches = [note.pitch.num for note in notes]
    times = [note.onset for note in notes]

    hc = HuronContour(pitches, times)

    return {
        "first_pitch": hc.first_pitch,
        "mean_pitch": hc.mean_pitch,
        "last_pitch": hc.last_pitch,
        "first_to_mean": hc.first_to_mean,
        "mean_to_last": hc.mean_to_last,
        "contour_class": hc.contour_class,
    }


def fantastic_count_mtypes(
    score: Score, segment: bool, phrase_gap: float, units: str
) -> NGramCounter:
    """Count M-Types in a melody.

    Parameters
    ----------
    score : Score
        The score to count M-Types in.
    segment : bool
        Whether to segment the melody into phrases.
    phrase_gap : float
        The minimum IOI gap to consider a new phrase.
    units : str
        The units of the phrase gap, either "seconds" or "quarters".

    Returns
    -------
    NGramCounter
        An NGramCounter object containing the counts of M-Types.
        This allows for the computation of the complexity measures, either
        by accessing the properties of the NGramCounter object or by using
        the `fantastic_mtype_summary_features` function.
    """
    if segment:
        segments = fantastic_segmenter(score, phrase_gap, units)
    else:
        segments = [score]

    counter = NGramCounter()
    tokenizer = FantasticTokenizer()

    all_tokens = []
    for phrase in segments:
        tokens = tokenizer.tokenize(phrase)
        all_tokens.extend(tokens)

    counter.count_ngrams(all_tokens, n=[1, 2, 3, 4, 5])

    return counter


def fantastic_mtype_summary_features(
    score: Score, segment: bool, phrase_gap: float, units: str
) -> Dict:
    """Count M-Types in a melody and compute summary features.
    This function provides an easy way to get all the complexity measures
    at once.

    Parameters
    ----------
    score : Score
        The score to count M-Types in.
    segment : bool
        Whether to segment the melody into phrases.
    phrase_gap : float
        The minimum IOI gap to consider a new phrase.
    units : str
        The units of the phrase gap, either "seconds" or "quarters".

    Returns
    -------
    Dict
        A dictionary of summary features.
        Dictionary keys:
            - mean_entropy: The mean entropy of the M-Types.
            - mean_productivity: The mean productivity of the M-Types.
            - yules_k: The mean Yules K statistic.
            - simpsons_d: The mean Simpson's D statistic.
            - sichels_s: The mean Sichels S statistic.
            - honores_h: The mean Honores H statistic.
    """
    mtype_counts = fantastic_count_mtypes(score, segment, phrase_gap, units)

    return {
        "mean_entropy": mtype_counts.mean_entropy,
        "mean_productivity": mtype_counts.mean_productivity,
        "yules_k": mtype_counts.yules_k,
        "simpsons_d": mtype_counts.simpsons_d,
        "sichels_s": mtype_counts.sichels_s,
        "honores_h": mtype_counts.honores_h,
    }
