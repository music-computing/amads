# pitchmean.py - compute mean or duration-weighted mean of pitch
#

from ..core.basics import Note


def pitch_mean(score, weighted=False):
    """Compute the mean pitch or mean pitch weighted by duration (in beats)
    score is a Score. The pitch mean is computed for all pitches in the score.
    """
    sum = 0
    count = 0
    if weighted:  # no need to merge tied notes
        for note in score.find_all(Note):
            sum += note.keynum * note.duration
            count += note.duration
    else:
        score = score.merge_tied_notes()
        for note in score.find_all(Note):
            sum += note.keynum
            count += 1
    return (sum / count) if sum > 0 else 0
