# pitchmean.py - compute mean or duration-weighted mean of pitch
#

from ..core.basics import Note


def pitch_mean(score, weighted=False):
    """Compute the mean pitch or mean pitch weighted by duration (in beats)
    score is a Score. The pitch mean is computed for all pitches in the score.
    """
    sum = 0
    count = 0
    if weighted:  # no need to merge tied notes. Rather than merging tied
        # notes, we use pitch * tied_duration = = pitch * (dur_1 + dur_2)
        # = pitch * dur_1 + pitch * dur_2, so we can just treat the
        # components of tied notes separately.
        for note in score.find_all(Note):
            sum += note.num * note.duration
            count += note.duration
    else:
        # Our problem is that we want to count only the first of any tied-note
        # group. We could use merge_tied_notes() to do this, but it is work to
        # make a new scoore and copy all notes. Instead, we keep a set of
        # tied-to notes and ignore any note encountered that is in the set.
        tied_to = set()
        for note in score.find_all(Note):
            if note.tie is not None:
                tied_to.add(note.tie)
            if note not in tied_to:
                sum += note.num
                count += 1
    return (sum / count) if sum > 0 else 0
