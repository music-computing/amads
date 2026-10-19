from amads.core.basics import Score, Note
from amads.pitch.pcdist1 import duraccent

import numpy as np

__author__ = "Anirudh Subramanian"

def onset_autocorr(
    score: Score,
    divisions: int = 4,
    max_lag: int = 8,
):
    """
    Returns autocorrelation of Note onsets weighted by duration.

    Onsets are quantized to the nearest division of a quarter note and
    weighted by Parncutt's durational accent (Parncutt, 1994).

    Autocorrelation values are normalized by dividing the autocorrelation
    at each time lag by the autocorrelation at zero time lag. This scales
    the autocorrelation values such that the value at zero lag, where the
    self-similarity of the score is maximized, is 1.

    Parameters
    ----------
    score : Score
        The score to compute autocorrelation
    divisions : int
        The number of divisions of a single quarter note to quantize
        onsets
    max_lag : int
        The maximum time lag, in quarter notes, for autocorrelation
        (inclusive)
    
    Return
    ------
    list[int]
        Autocorrelation values at time lag 0, ... `max_lag` in steps of
        `division`
    
    References
    ----------
    Brown, J. (1992). Determination of meter of musical scores by
        autocorrelation. Journal of the acoustical society of America, 94
        (4), 1953-1957.
    Parncutt, R. (1994). A perceptual model of pulse salience and metrical
        accent in musical rhythms. Music Perception, 11(4), 409-464.
    Toiviainen, P., & Eerola, T. (2006). Autocorrelation in meter
        induction: the role of accent structure. Journal of the Acoustical
        Society of America, 119(2), 1164-1170.
    """

    score = score.merge_tied_notes()

    notes = [n for n in score.find_all(Note)]
    max_onset = max(n.onset for n in notes)

    length = divisions * max(2 * max_lag, round(max_onset) + 1)
    time_series = [0.0] * length

    for n in notes:
        index = round(n.onset * divisions)
        time_series[index] += duraccent(n)

    autocorr = np.correlate(time_series, time_series, mode='full')
    mid = autocorr.size // 2
    autocorr = autocorr[mid : mid + max_lag * divisions + 1] # max_lag is inclusive
    autocorr = autocorr / autocorr[0] # normalize
    autocorr = autocorr.tolist()

    return autocorr