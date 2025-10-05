"""
Melodic contour of a subsampling of a monophonic Score

Date: [2025-01-24]

Description:
    Compute the sequence of pitches of a subsampling of pitches from a
    monophonic score

Usage:
    [Add basic usage examples or import statements]

Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=71

Reference(s):
    Eerola, T., Himberg, T., Toiviainen, P., & Louhivuori, J. (2006).
        Perceived complexity of Western and African folk melodies by Western
        and African listeners. Psychology of Music, 34(3), 341-375.
"""

import math

import numpy as np

from ...core.basics import Note, Score
from ...pitch.ismonophonic import ismonophonic


def melodySamplingContour(score: Score, res: float) -> list[tuple[float, int]]:
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
    list[tuple[float, float]]
        list of tuples of onset and midi keypitch correspondences
        (you can perceive as (sampling_tick, pitch))

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/melcontour.m

    Examples
    --------
    [Unfortunately, still having problem resolving score construction]
    """
    # this algorithm can only operate on monophonic melodies
    if not ismonophonic(score):
        raise ValueError("Score must be monophonic")
    # make a flattened and collapsed copy of the original score
    flattened_score = score.flatten(collapse=True)

    # extracting note references here from our flattened score
    # we can probably run a new iterator based off of find_all and "yield from",
    # but that's probably something I want to do later, not now.
    notes = list(flattened_score.find_all(Note))

    if not notes:
        raise ValueError("Score is empty")

    # Note that the first sampling "tick" only starts at zero on the onset
    # of the first note
    sampling_tick = 0.0
    sampling_end = float(notes[-1].end - notes[0].start)

    sampled_note_idx = 0

    # to avoid running past the last note, we insert an extra note at time infinity
    # we are going to refer to this as the canary value below.
    notes.append(Note(1, None, None, None, float("infinity")))

    contour_list = []
    while sampling_tick <= sampling_end:
        # we want to find the closest note with an onset closest to the current
        # sampling tick
        current_note_range = range(sampled_note_idx, len(notes))
        next_note_range = range(sampled_note_idx + 1, len(notes))
        for note_idx, next_note_idx in zip(current_note_range, next_note_range):
            # the next note to the last note up to a sampling resolution tick
            # will always be the first note after the sampling resolution tick
            # by definition
            if (
                notes[note_idx].start <= sampling_tick + notes[0].start
                and notes[next_note_idx].start > sampling_tick + notes[0].start
            ):
                sampled_note_idx = note_idx
                break
            assert notes[note_idx].start <= sampling_tick + notes[0].start

        # assert that the canary value appended to the end hasn't been selected.
        # this is mostly just a sanity check
        assert notes[sampled_note_idx].start != float("infinity")
        # add relevant tuple
        contour_list.append((sampling_tick, notes[sampled_note_idx].keynum))
        sampling_tick += res

    return contour_list


def autocorrelatecontour(contour_output: list[tuple[float, int]]):
    """
    Calculates the autocorrelation of a contour output

    Parameters
    ----------
    contour_output
        output of melcontour

    Returns
    -------
    list[tuple[float, float]]
        list of tuples of onset differences between contour output and
        autocorrelation values

    Notes
    -----
    Implementation based on the original MATLAB code from:
    https://github.com/miditoolbox/1.1/blob/master/miditoolbox/melcontour.m

    Examples
    --------

    """
    # unpack output of melcontour
    sample_tuple, pitch_tuple = zip(*contour_output)
    # adjust pitch information based off of matlab implementation
    pitch_array = np.array(pitch_tuple, dtype=float)
    pitch_array -= np.mean(pitch_array)
    pitch_array /= math.sqrt(np.dot(pitch_array, pitch_array))
    # note that with the "full" option, np.correlate gives the exact same output
    # as matlab's xcorr function
    correlation_array = np.correlate(pitch_array, pitch_array, "full")
    # essentially, we want all values
    # [-sampling_end, -sampling_end + res ... 0 ... sampling_end]
    # with a step size of res here
    # sampling_end in this list is truncated towards the nearest multiple of res
    sample_array = np.array(sample_tuple, dtype=float)
    lag_array = np.concatenate((-sample_array[:0:-1], sample_array))
    assert lag_array.shape == correlation_array.shape
    # repack correspondence
    return list(zip(list(lag_array), list(correlation_array)))
