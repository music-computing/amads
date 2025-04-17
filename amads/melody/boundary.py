"""
This function implements the local boundary detection model
by Cambouropoulos (1997)

Function input:
    Musical score (as specified in basics.py)

Function output:
    (note start, strength) list
    note that since we are dealing with a monophonic score, each start
    corresponds to only 1 unique note, we can ensure that each output
    corresponds to a unique monophonic piece of music

Here's a few questions that we need to answer before deciding
on what our output should be...
(1) How do we represent causal relationship within our current score/part
structure?
(2) How do we encode additional information within the confines of the inherent
structure of the score? how do we do so in an extensible manner (preferably
external to the Score itself?)
Note that the matlab version has a column matrix of strengths, where the
row position of each weight corresponds to the row position of the note
in the score matrix...

What additional structure do we need to port the matlab version faithfully?
The problems are 2-fold:
(1) we have a partial ordering in our version of the score, instead of
the total ordering done in the matlab version.
(2) we don't have a way to correspond information to each score element
(e.g. note, measure, chord, etc.)

Things we need from basics.py:
(1) each event should have not only a parent, but also the ability to obtain
immediate successors and predecessors within the current containing object.

How about, we have a column matrix with weak references to the notes in the
argument score?
Note here that we can't segment the output into individual scores, because
there are no clear defined boundaries, only "soft" boundaries.
Another problem is, is it appropriate for each of these segmentation algorithms
to have wildly different output structures?
For that matter, what should we do with standardizing output structure?
Note to strength dictionary? Too complex.
Since we are only dealing with monophonic scores in these algorithms, we can
leverage the fact that each note start has a unique note in the score and
emit start and strength pairs...
"""

from ..core.basics import Score
from ..pitch.ismonophonic import ismonophonic


def boundary(score: Score):
    """
    Given a score, returns the following:
    (1) If score is not monophonic, we raise an exception
    (2) If score has notes, we return a a list of tuples containing
    note start and its corresponding strength, respectively
    """
    if not ismonophonic(score):
        raise ValueError("Score must be monophonic")

    notes = score.get_sorted_notes()

    # profiles
    pp = [abs(pair[1].keynum - pair[0].keynum) for pair in zip(notes, notes[1:])]
    po = [pair[1].onset - pair[0].onset for pair in zip(notes, notes[1:])]
    pr = [max(0, pair[1].onset - pair[0].offset) for pair in zip(notes, notes[1:])]

    def list_degrees(profile):
        ret_list = [
            abs(pair[1] - pair[0]) / (1e-6 + pair[1] + pair[0])
            for pair in zip(profile, profile[1:])
        ]
        ret_list.append(0)
        return ret_list

    # degrees of change
    rp = list_degrees(pp)
    ro = list_degrees(po)
    rr = list_degrees(pr)

    def list_strengths(profile, degrees):
        degrees_sum = [0]
        for degree_pair in zip(degrees, degrees[1:]):
            degrees_sum.append(degree_pair[0] + degree_pair[1])
        strengths = [pair[0] * pair[1] for pair in zip(profile, degrees_sum)]
        max_strength = max(strengths)
        if max_strength > 0.1:
            strengths = [x / max_strength for x in strengths]
        return strengths

    sp = list_strengths(pp, rp)
    so = list_strengths(po, ro)
    sr = list_strengths(pr, rr)

    b = [1]
    for sp_elem, so_elem, sr_elem in zip(sp, so, sr):
        b.append(0.25 * sp_elem + 0.5 * so_elem + 0.25 * sr_elem)
    assert len(b) == len(notes)

    return [(note.onset, boundary) for (note, boundary) in zip(notes, b)]
