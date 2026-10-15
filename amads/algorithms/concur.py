"""
Implementation of the concur() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 56

"""

from amads.core.basics import Score


def concur(score: Score, threshold: float = 0.2) -> float:
    """
    Calculates the number of distinct onset "groups," where group
    boundaries are the inter-onset interval greater than threshold
    (in beats or seconds, depending on the current units in the score).

    Equivalently, counts the number of distinct onset "groups", where
    groups are consecutive IOIs less than or equal to threshold. Note
    that the time span of a group is arbitrary since there can be any
    number of consecutive IOIs less than threshold.

    This algorithm and its results are not an exact replication of the
    Matlab MIDI Toolbox concur function.

    Parameters
    ----------
    score : Score
        The score to analyze.

    threshold : float
        IOI in beats greater than this value starts a new group.
        Default value is 0.2.

    Returns
    -------
    float
        The number of distinct onset groups divided by the total number
        of notes.
    """
    # 1. Get all the notes in the score
    notes = score.get_sorted_notes()
    prev_onset = -999  # effectively -infinity so first note starts a group
    count = 0

    # 2. Iterate through the notes and count distinct onset groups
    for note in notes:
        if note.onset - prev_onset > threshold:
            count += 1
        prev_onset = note.onset

    # 3. Calculate the ratio of distinct groups to total notes
    return count / len(notes)
