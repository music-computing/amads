"""
Melodic contour of a subsampling of a monophonic Score

Compute the sequence of pitches of a subsampling of pitches from a
monophonic score

Ports the 'melcontour' function from miditoolbox.

https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 72-73
"""

import math
from itertools import count

import numpy as np

from amads.core.basics import Note, Score


def _autoCorrelateContour(contour_input: list[Note]) -> list[float] | None:
    """
    Calculates the autocorrelation of a contour output

    Parameters
    ----------
    contour_output
        output of melcontour

    Returns
    -------
    list[float]
        list of tuples of onset differences between contour output and
        autocorrelation values

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/melcontour.m
    """

    # unpack output of melcontour
    pitches = [note.midi_num for note in contour_input]
    # adjust pitch information based off of matlab implementation
    pitch_array = np.array(pitches, dtype=float)
    pitch_array -= np.mean(pitch_array)
    pitch_array /= math.sqrt(np.dot(pitch_array, pitch_array))
    # note that with the "full" option, np.correlate gives the exact same output
    # as matlab's xcorr function
    correlation_array = np.correlate(pitch_array, pitch_array, "full")
    return list(correlation_array)


def melodySamplingContour(
    score: Score, res: float, res_type: str = "rel"
) -> list[Note] | None:
    """
    Calculates a sequence of the pitches of the last note onset up to
    each sampling resolution tick
    For instance, given a monophonic score of 4 notes where the notes are sorted
    by onset:
    [note1, note2, note3, note4]

    A sampling resolution of 2.0 will yield:
    [(0.0, note1.keynum), (2.0, note3.keynum)]

    A sampling resolution of 0.5 will yield:
    [(0.0, note1.keynum), (0.5, note1.keynum), (1.0, note2.keynum), ... ]

    Parameters
    ----------
    score : Score
        Monophonic input score (class from core.basics for storing music scores)
    res : float | int
        Sampling resolution (in beats, see core.basics for more details)
    res_type : str
        Type of the sampling resolution.
        if res_type == 'abs', res is defined as the sampling interval in beats
        if res_type == 'rel', res is defined as the number of sampling points

    Returns
    -------
    Optional[list[Note]]
        None if the score is empty.
        A time-series list where each element is a reference to the note object
        with an onset closest to that specific time step (index * resolution).

    References
    ----------
        Eerola, T., Himberg, T., Toiviainen, P., & Louhivuori, J. (2006).
            Perceived complexity of Western and African folk melodies by Western
            and African listeners. Psychology of Music, 34(3), 341-375.

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/melcontour.m
    """
    # this algorithm can only operate on monophonic melodies
    if not score.ismonophonic():
        raise ValueError("Score must be monophonic")

    if res_type != "abs" and res_type != "rel":
        raise ValueError(
            f"invalid sampling resolution type {res_type}! Must be either 'abs' or 'rel"
        )

    if res_type == "rel":
        res = (score.duration) / res

    sample_iter = score.find_all(Note)
    current_note = next(sample_iter, None)
    if not current_note:
        return None
    next_note = next(sample_iter, None)

    sampling_list = []

    for sample_time in count(start=0, step=res):
        if sample_time >= score.duration:
            break
        if sample_time < current_note.onset - score.onset:
            continue
        while next_note and next_note.onset - score.onset <= sample_time:
            current_note = next_note
            next_note = next(sample_iter, None)
        # record current_note for the associated time sample
        sampling_list.append(current_note)
        # record pitch for current sample time
        if not next_note:
            break

    return sampling_list


def melodySamplingCorrelation(
    score: Score, res: float, res_type: str = "rel"
) -> list[float] | None:
    """
    Performs autocorrelation on the output computed by melodySamplingContour.

    Parameters
    ----------
    score
        Monophonic input score (class from core.basics for storing music scores)
    res
        Sampling resolution (in beats, see core.basics for more details)
    res_type : str
        Type of the sampling resolution.
        if res_type == 'abs', res is defined as the sampling interval in beats
        if res_type == 'rel', res is defined as the number of sampling points

    Returns
    -------
    list[float] | None
        None if the score is empty.
        A time-series list of autocorrelations of melodySamplingContour.

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/melcontour.m
    """
    sampling_result = melodySamplingContour(score, res, res_type)
    if not sampling_result:
        return None
    return _autoCorrelateContour(sampling_result)
