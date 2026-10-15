# pitchmean.py - compute mean or duration-weighted mean of pitch
#

from amads.core.basics import Note


def pitch_mean(score, weighted=False):
    """Compute the mean pitch or mean pitch weighted by duration (in quarters)

    Parameters
    ----------
    score : Score
        The pitch mean is computed for all pitches in the score. Groups of
        two or more tied notes are counted as one pitch occurrence.
    weighted : bool
        If true, pitches are weighted by their durations.
    """
    sum = 0
    count = 0
    for note in score.find_all(Note):
        w = note.duration if weighted else 1
        sum += note.midi_num * w
        count += w
    return (sum / count) if sum > 0 else 0
