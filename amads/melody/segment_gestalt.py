"""
This function implements the segment gestalt function
by Tenney & Polansky (1980)

We can broadly categorise the algorithm's limitations to 2 categories:
(1) Soft restrictions
(2) Hard restrictions on what scores we can take, either because
the algorithm exhibits undefined behavior when these scores are given,
or because it isn't designed for said restrictions.

With these categories in mind, we have the following limitations.
The algorithm does not consider these things within its scope
(given a monophonic input):
(1) the monophonic music may have stream segregation
(i.e. 1 stream of notes can be interpreted as 2 or more separate interspersed
entities)
(2) does not consider harmony or shape
(see beginning of section 2 for the OG paper for more details)
(3) does not give semantic meaning (we're still stuck giving arbitrary ideals
to arbitrary things)

The algorithm has the following restrictions to the score:
(1) the score must be monophonic (perception differences)
If we consider polyphonic scores, we will need a definition of what
a substructure is for said score (in said algorithm) with respect to how we
carve the note strutures.
Since, in this algorithm, we don't consider stream
segregation and other features that require larger context clues,
we can just simply define a score substructure "temporally" as a contiguous
subsequence of notes
Hence, it is safe to assume that the current algorithm is undefined when
it comes to polyphonic music.

Function input:
    Musical score (as specified in basics.py)

Function output:
    None if no clangs can be formed
    else, 2-tuple of:
    Note here that the clangs and segments will *probably* be represented
    by a collection of scores each...
    (0) sorted list of starts denoting clangs boundaries
    (1) sorted list of starts denoting segments segment boundaries

Some thoughts (and questions):
(1) Should our output preserve the internal structure of the score
for segments and clangs?
Probably not. Keep in mind we're dealing with monophonic score structures.
we just need to provide sufficient information that allows a caller to
potentially verify the result and use it elsewhere, hence we simply
return 2 lists of separate scores.

Legit think having a separate representation that can index into individual
notes will be immensely helpful.
But, I'm certain there has to be something I'm missing to decide otherwise
(if I had to guess, ambiguity of how musical scores themselves are presented to
the musician is chief among them, and maintaining that ambiguity in our internal
representation is also paramount)

Also legit think we need well-defined rules to split and merge scores...

On a completely separate and unrelated note, there are 2 pitchmeans with,
the *exact* same implementation and 2 filenames...
"""

from operator import lt

from ..core.basics import Part, Score
from ..pitch.ismonophonic import ismonophonic
from ..pitch.pitch_mean import pitch_mean


def construct_score_list(notes, intervals):
    """
    given an iterator of intervals and a global list of notes,
    we construct a list of scores containing the notes specified within the intervals
    """
    score_list = []
    for interval in intervals:
        new_score = Score()
        new_part = Part(new_score)
        for note in notes[interval[0] : interval[1]]:
            note.deepcopy_into(new_part)
        score_list.append(new_score)
    return score_list


def find_peaks(target_list, comp=lt):
    """
    returns a list of indices identifying peaks in the list
    according to a comparison
    """
    peaks = []
    for i, triplet in enumerate(zip(target_list, target_list[1:], target_list[2:])):
        if comp(triplet[0], triplet[1]) and comp(triplet[2], triplet[1]):
            peaks.append(i + 1)
    return peaks


def segment_gestalt(score: Score) -> tuple[list[float], list[float]]:
    """
    Given a score, returns the following:
    (1) If score is not monophonic, we raise an exception
    (2) If score is monophonic, we return a 2-tuple of lists for clang boundary
    starts and segment boundary starts, respectively
    """
    if not ismonophonic(score):
        raise Exception("score not monophonic, input is not valid.")

    notes = score.flatten(collapse=True).content

    if len(notes) <= 0:
        return ([], [])

    cl_values = []
    # calculate clang distances here
    for note_pair in zip(notes[:-1], notes[1:]):
        pitch_diff = note_pair[1].num - note_pair[0].num
        onset_diff = note_pair[1].onset - note_pair[0].onset
        cl_values.append(2 * onset_diff + abs(pitch_diff))

    # combines the boolean map and the scan function that was done in matlab
    if len(cl_values) < 3:
        return ([], [])

    clang_soft_peaks = find_peaks(cl_values)
    cl_indices = [0]
    # worry about indices here
    # starting index here
    # 1 past the end so we can construct score list easier
    cl_indices.extend([idx + 1 for idx in clang_soft_peaks])
    cl_indices.append(len(notes))

    clang_onsets = list(map(lambda i: (notes[i].onset), cl_indices[:-1]))

    if len(clang_onsets) <= 2:
        return (clang_onsets, [])

    # we can probably split the clangs here and organize them into scores
    clang_scores = construct_score_list(notes, zip(cl_indices[:-1], cl_indices[1:]))
    # calculate segment boundaries
    # we need to basically follow segment_gestalt.m
    # (1) calculate individual clang pitch means
    mean_pitches = [pitch_mean(score, weighted=True) for score in clang_scores]

    # (2) calculate segment distances
    seg_dist_values = []
    # calculating segment distance...
    for i in range(len(clang_scores) - 1):
        local_seg_dist = 0.0
        # be careful of the indices when calculating segdist here
        local_seg_dist += abs(mean_pitches[i + 1] - mean_pitches[i])
        # first first distance
        local_seg_dist += notes[cl_indices[i + 1]].onset - notes[cl_indices[i]].onset
        # first of next clang to last of distance
        local_seg_dist += abs(
            notes[cl_indices[i + 1]].num - notes[cl_indices[i + 1] - 1].num
        )
        local_seg_dist += 2 * (
            notes[cl_indices[i + 1]].onset - notes[cl_indices[i + 1] - 1].onset
        )
        seg_dist_values.append(local_seg_dist)
    if len(seg_dist_values) < 3:
        return (clang_onsets, [])

    seg_soft_peaks = find_peaks(seg_dist_values)
    assert seg_soft_peaks[-1] < len(cl_indices) - 1
    seg_indices = [0]
    # do we need to add 1 here? where do we add 1
    # worry about indices here
    seg_indices.extend([cl_indices[idx + 1] for idx in seg_soft_peaks])
    seg_indices.append(len(notes))

    segment_onsets = list(map(lambda i: (notes[i].onset), seg_indices[:-1]))
    return (clang_onsets, segment_onsets)
