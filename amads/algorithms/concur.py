"""
Implementation of the concur() function from the Matlab MIDI Toolbox

Original Document: https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, Page 56

"""

from amads.core.basics import Score


def concur(score: Score, threshold: float = 0.2) -> float:
    """
    Calculates the number of distinct note onset times as a fraction of
    the total number of note onsets. Onsets within a certain threshold beats
    are grouped and counted as a single onset.

    This algorithm and its results are not an exact replication of the
    Matlab MIDI Toolbox concur function.

    Parameters
    ----------
    score : Score
        The score to analyze.

    threshold : float
        Maximum beat difference between two onsets to be grouped together.
        Default value is 0.2.

    Returns
    -------
    float
        The number of distinct onset groups divided by the total number of notes.
    """
    # 1. Get all the notes in the score
    notes = score.get_sorted_notes()

    # If there are no notes, return 0.0
    if not notes:
        return 0.0

    groups = 1

    # 2. Iterate through the notes and count how many distinct onset groups there are
    for i in range(1, len(notes)):
        if notes[i].onset - notes[i - 1].onset > threshold:
            groups += 1

    # 3. Calculate the ratio of distinct onsets to total onsets
    return groups / len(notes)
