"""
Measure of phenomenal accent synchrony in a melody.

Completely reimplements Yiwen Zhao's original port.

Ports the `meteraccent` function from Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 74.
"""

from statistics import mean

from amads.core.basics import Note, Score
from amads.melody.melodic_accent import melodic_accent
from amads.pitch.pcdist1 import duraccent
from amads.time.meter.metric_hierarchy import metric_hierarchy


def meter_accent(score: Score, miditoolbox_compatible: bool = True) -> float:
    """
    Measure of phenomenal accent synchrony in a melody.

    This function measures how well different types of musical accents
    (durational, pitch, and metrical) align with each other. Higher
    synchrony indicates stronger alignment between different accent types.

    Returns a measure of phenomenal accent synchrony. It consists of durational
    accents, pitch accents and accentuation from inferred metrical hierarchy.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.
    miditoolbox_compatible: bool
        Whether we want our calculated results to be compatible with the
        miditoolbox version

    Returns
    -------
    float
        Accent synchrony value

    References
    ----------
        Eerola, T., Himberg, T., Toiviainen, P., & Louhivuori, J. (2006).
            Perceived complexity of Western and African folk melodies by Western
            and African listeners. Psychology of Music, 34(3), 341-375.
        Jones, M. R. (1987). Dynamic pattern structure in music: Recent theory
            and research. Perception and Psychophysics, 41, 621-634.
    """

    if next(score.find_all(Note), None) is None:
        return None
    if not score.ismonophonic():
        return None

    score = melodic_accent(score)
    if score is None:
        return None
    score = metric_hierarchy(score, miditoolbox_compatible)
    if score is None:
        return None

    score_meter_state = score.units_are_seconds
    if not score_meter_state:
        score.convert_to_seconds()

    accent_mean = mean(
        note.get("metric_hierarchy")
        * note.get("melodic_accent")
        * duraccent(note)
        for note in score.find_all(Note)
    )

    if not score_meter_state:
        score.convert_to_quarters()

    return -1 * accent_mean
