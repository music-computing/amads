"""
This module implements the segment gestalt function
by Tenney & Polansky (1980)

We can broadly categorise the algorithm's limitations to 2 categories:

 1. Soft restrictions

 2. Hard restrictions on what scores we can take, either because
    the algorithm exhibits undefined behavior when these scores are given,
    or because it isn't designed for said restrictions.

With these categories in mind, we have the following limitations.
The algorithm does not consider these things within its scope
(given a monophonic input):

 1. the monophonic music may have stream segregation
    (i.e. 1 stream of notes can be interpreted as 2 or
    more separate interspersed entities)

 2. does not consider harmony or shape (see beginning of section 2
    for the OG paper for more details)

 3. does not give semantic meaning (we're still stuck giving
    arbitrary ideals to arbitrary things)

The algorithm has the following restriction to the score:

 - the score must be monophonic (perception differences)
    If we consider polyphonic scores, we will need a definition of what
    a substructure is for said score (in said algorithm) with respect to
    how we carve the note strutures. Since, in this algorithm, we don't
    consider stream segregation and other features that require larger
    context clues, we can just simply define a score substructure
    “temporally” as a contiguous subsequence of notes. Hence, it is safe
    to assume that the current algorithm is undefined when it comes to
    polyphonic music.

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
"""

from operator import lt
from typing import List, cast

from amads.core.basics import Note, Part, Score


def _calculate_interim_pitch_means(notes, cl_indices):
    means = []
    for start, last in zip(cl_indices, cl_indices[1:]):

        pitch_sum = 0
        dur_sum = 0
        for note in notes[start:last]:
            pitch_sum += note.key_num * note.duration
            dur_sum += note.duration
        means.append(pitch_sum / dur_sum)
    return means


def _construct_score_list(notes, intervals):
    """
    given an iterator of intervals and a global list of notes,
    we construct a list of scores containing the notes specified within the intervals
    """
    score_list = []
    for interval in intervals:
        new_score = Score()
        new_part = Part(new_score)
        for note in notes[interval[0] : interval[1]]:
            note.insert_copy_into(new_part)
        score_list.append(new_score)


def _calculate_segdist(
    clang_boundary_notes,
    next_clang_boundary_start,
    current_pitch_mean,
    next_pitch_mean,
):
    """
    calculates the segment distances from a list of notes that belong
    to a singular clang based off of its constituent notes, the current pitch mean
    """

    first_note, last_note = clang_boundary_notes
    next_first_note = next_clang_boundary_start
    local_seg_dist = 0.0
    # be careful of the indices when calculating segdist here
    local_seg_dist += abs(next_pitch_mean - current_pitch_mean)
    # first first distance
    local_seg_dist += next_first_note.onset - first_note.onset
    # first of next clang to last of current clang distance
    local_seg_dist += abs(next_first_note.key_num - last_note.key_num)
    local_seg_dist += 2 * (next_first_note.onset - last_note.onset)
    return local_seg_dist


def _find_peaks(target_list, comp=lt):
    """
    returns a list of indices identifying peaks in the list
    according to a comparison
    """
    peaks = []

    _min_diff = 1e-11

    for i, (prev, current, next) in enumerate(
        zip(target_list, target_list[1:], target_list[2:])
    ):
        if comp(_min_diff, current - prev) and comp(_min_diff, current - next):
            peaks.append(i + 2)
    return peaks


def _annotate_score(score, clang_onset_iterator, segment_onset_iterator):
    """
    annotates the score when there is a clang onset and/or segment onset
    by setting has_clang_onset and/or has_segment_onset to True
    and False otherwise
    """
    clang_val = next(clang_onset_iterator, None)
    seg_val = next(segment_onset_iterator, None)
    for note in score.find_all(Note):
        note.set("has_clang_onset", False)
        note.set("has_segment_onset", False)
        if clang_val == note.onset:
            note.set("has_clang_onset", True)
            clang_val = next(clang_onset_iterator, None)
        if seg_val == note.onset:
            note.set("has_segment_onset", True)
            seg_val = next(segment_onset_iterator, None)

    return score


def segment_gestalt(score: Score) -> Score:
    """
    Given a monophonic score, returns clang and segment boundary onsets

    Parameters
    ----------
    score: Score
        The score to be segmented

    Returns
    -------
    Score
    The same score that was passed in, but it is annotated with clang boundaries
    by attaching two boolean attributes "has_clang_onset" and
    "has_segment_onset" to each note in the score, where they are True
    if the note is a clang or onset, respectively, and False otherwise.


    Raises
    ------
    Exception
        if the score is not monophonic
    """
    if not score.ismonophonic():
        raise Exception("score not monophonic, input is not valid.")

    score.convert_to_quarters()
    # No matter what I do I will need to collapse the notes.
    # If I don't collapse the nodes, I will need node onsets...
    notes: List[Note] = cast(
        List[Note], score.flatten(collapse=True).list_all(Note)
    )

    if len(notes) <= 0:
        return _annotate_score(score, iter([]), iter([]))

    cl_values = []
    # calculate clang distances here
    for current_note, next_note in zip(notes[:-1], notes[1:]):
        pitch_diff = next_note.key_num - current_note.key_num
        onset_diff = next_note.onset - current_note.onset
        cl_values.append(2 * onset_diff + abs(pitch_diff))

    # combines the boolean map and the scan function that was done in matlab
    if len(cl_values) < 3:
        return _annotate_score(score, iter([]), iter([]))

    clang_soft_peaks = _find_peaks(cl_values)

    cl_indices = [0]
    # think about this and whether or not there's an off-by-one
    cl_indices.extend(clang_soft_peaks)
    # this is added for convenience
    cl_indices.append(len(notes))

    clang_onsets = (notes[i + 1].onset for i in clang_soft_peaks)

    if len(clang_soft_peaks) <= 2:
        return _annotate_score(score, clang_onsets, iter([]))

    # calculate segment boundaries
    # we need to basically follow segment_gestalt.m
    # (1) calculate individual clang pitch means
    mean_pitches = _calculate_interim_pitch_means(notes, cl_indices)

    # (2) calculate segment distances
    seg_dist_values = []
    # calculating segment distance...
    for start_idx, next_idx, mean, next_mean in zip(
        cl_indices, cl_indices[1:], mean_pitches, mean_pitches[1:]
    ):
        current_start = start_idx
        current_end = next_idx - 1
        clang_boundary_notes = (notes[current_start], notes[current_end])
        # Note that, this will not be executed when we hit our convenience value
        # in next_idx because the next_mean won't exist
        next_clang_start = notes[next_idx]

        local_segdist = _calculate_segdist(
            clang_boundary_notes, next_clang_start, mean, next_mean
        )

        seg_dist_values.append(local_segdist)
    if len(seg_dist_values) < 3:
        return _annotate_score(score, clang_onsets, iter([]))

    seg_soft_peaks = _find_peaks(seg_dist_values)
    assert seg_soft_peaks[-1] < len(notes)
    # do we need to add 1 here? where do we add 1
    # worry about indices here
    # TODO: worry about this a bit.
    seg_indices = [cl_indices[idx] + 1 for idx in seg_soft_peaks]

    segment_onsets = (notes[i].onset for i in seg_indices)

    # mark the fields in the original score.
    return _annotate_score(score, clang_onsets, segment_onsets)
