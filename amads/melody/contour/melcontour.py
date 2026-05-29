"""
Melodic contour of a subsampling of a monophonic Score

Date: [2025-01-24]

Description:
    Compute the sequence of pitches of a subsampling of pitches from a
    monophonic score

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=71

Reference(s):
    Eerola, T., Himberg, T., Toiviainen, P., & Louhivuori, J. (2006).
        Perceived complexity of Western and African folk melodies by Western
        and African listeners. Psychology of Music, 34(3), 341-375.
"""

import math

import numpy as np
from itertools import count
from typing import Optional, List

from amads.core.basics import Note, Score
from amads.pitch.ismonophonic import ismonophonic


def _autoCorrelateContour(contour_input: list[Note]) -> Optional[list[float]]:
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
    pitches = [note.key_num for note in contour_input]
    # adjust pitch information based off of matlab implementation
    pitch_array = np.array(pitches, dtype=float)
    pitch_array -= np.mean(pitch_array)
    pitch_array /= math.sqrt(np.dot(pitch_array, pitch_array))
    # note that with the "full" option, np.correlate gives the exact same output
    # as matlab's xcorr function
    correlation_array = np.correlate(pitch_array, pitch_array, "full")
    return list(correlation_array)


def melodySamplingContour(score: Score, res: float) -> Optional[List[Note]]:
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
    score
        Monophonic input score (class from core.basics for storing music scores)
    res
        Sampling resolution (in beats, see core.basics for more details)

    Returns
    -------
    Optional[list[Note]]
        None if the score is empty.
        A time-series list where each element is a reference to the note object
        with an onset closest to that specific time step (index * resolution).

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/melcontour.m
    """
    # this algorithm can only operate on monophonic melodies
    if not ismonophonic(score):
        raise ValueError("Score must be monophonic")
    # make a flattened and collapsed copy of the original score

    sample_iter = score.find_all(Note)
    current_note = next(sample_iter, None)
    if not current_note:
        return None
    next_note = next(sample_iter, None)

    sampling_list = []

    for sample_time in count(start=0, step=res):
        if sample_time < current_note.onset:
            continue
        while next_note and next_note.onset <= sample_time:
            current_note = next_note
            next_note = next(sample_iter, None)
        # TODO: record current_note for the associated time sample
        sampling_list.append(current_note)
        # record pitch for current sample time
        if not next_note:
            break

    return sampling_list


def melodySamplingCorrelation(score: Score, res: float) -> Optional[List[float]]:
    return _autoCorrelateContour(melodySamplingContour(score, res))
