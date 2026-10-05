"""
Melodic attraction according to Lerdahl (1996)

Completely rewrites the original melodic_attraction function that Yiwen Zhao
first wrote.

Ports the `melattraction` function from Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 70.
"""

from collections.abc import Iterator
from itertools import chain, pairwise, tee

from amads.core.basics import Note, Score
from amads.pitch.key.keymode import keymode
from amads.pitch.key.transpose2c import transpose2c

"""
Anchor weights for each pitch class.

There are two sets of anchor weights, one for a major weight and one for a minor
weight.
The anchor weights are determined as follows (according to Lerdahl) in order
of decreasing weights (note that the weight taken is the highest weight
of the pitch-class in the hierarchy):
- Highest stability is assigned to the tonic root (with a value of 4)
- The tonic triad notes (with a value of 3)
- Diatonic scale notes (with a value of 2)
- Non-diatonic (chromatic) pitches (with a value of 1)
"""
_anchorweights_major = [4, 1, 2, 1, 3, 2, 1, 3, 1, 2, 1, 2]
_anchorweights_minor = [4, 1, 2, 3, 1, 2, 1, 3, 2, 2, 1, 2]


def _int_sign(val: int) -> int:
    """
    Internal function for calculating signage of an integer.

    It is a port of the matlab sign function specific to integers.

    TODO: maybe a good idea to port a set of core matlab functions that may not
    have an analogue in python. This function is a very good example of that.

    Parameters
    ----------
    val : int
        value of the integer

    Returns
    -------
    int
        -1 if val is a negative integer
        0 if val is 0
        1 if val is a positive integer
    """
    if val == 0:
        return 0
    elif val < 0:
        return -1
    else:
        return 1


def _get_lerdahl_attraction(
    source_stability: int, target_stability: int, pitch_distance: int
) -> float:
    """
    Calculate the melodic attraction between two notes using Lerdahl's model.

    Ports the 'stabilitydistance' internal function in the melattraction module
    from miditoolbox1.1

    Parameters
    ----------
    source_stability : int
        The stability of the source note (the corresponding anchorweight of the
        pitch_class to start on)
    target_stability : int
        The stability of the target note (the corresponding anchorweight of the
        pitch_class to move to)
    pitch_distance : int
        The pitch distance (in semitones) between the target note and the source
        note

    Returns
    -------
    float
        Attraction value between 0 and 1
    """

    if pitch_distance == 0:
        return 0  # Avoid division by zero

    # Lerdahl's attraction formula
    return (target_stability / source_stability) * (1 / pitch_distance**2)


def _get_anchorweights(
    transposed_note_iter: Iterator[Note], mode_strs: list[str]
) -> tuple[list[int], Iterator[int]]:
    """
    internal function that gives a generator for obtaining the anchorweights
    for each note in the transposed score obtain

    Parameters
    ----------
    transposed_note_iter : Iterator[Note]
        An iterator that iterates over all the notes in a transposed score
    mode_strs: list[str]
        Mode strings obtained from keymode run on the default Krumhansl-Kessler
        pitch profile

    Returns
    -------
    Iterator[int]
        An iterator that yields the anchorweight of each note as iterated
        through transposed_note_iter
    """
    if any(mode_str == "major" for mode_str in mode_strs):
        anchorweights = _anchorweights_major
    elif any(mode_str == "minor" for mode_str in mode_strs):
        anchorweights = _anchorweights_minor
    else:
        anchorweights = _anchorweights_major

    assert anchorweights is not None
    [transposed_note_iter] = tee(transposed_note_iter, 1)
    anchor_generator = (
        anchorweights[note.pitch_class] for note in transposed_note_iter
    )
    return anchorweights, anchor_generator


def _get_pitch_directions(
    transposed_note_iter: Iterator[Note],
) -> Iterator[int]:
    """
    Yields the pitch direction change (up, down, or same) between each
    successive pair of notes in a melody.

    Parameters
    ----------
    transposed_note_iter : Iterator[Note]
        An independent iterator that iterates over all the notes in a
        transposed score

    Returns
    -------
    Iterator[int]
        An iterator that yields the pitch directions for each pair of notes
        in the transposed score
    """
    [transposed_note_iter] = tee(transposed_note_iter, 1)
    signed_pitch_proximity_gen = (
        next_note.midi_num - current_note.midi_num
        for current_note, next_note in pairwise(transposed_note_iter)
    )
    return (_int_sign(val) for val in signed_pitch_proximity_gen)


def _get_directed_motion_indices(
    transposed_note_iter: Iterator[Note],
) -> Iterator[int]:
    """
    Yields the directed motion indices for the independent transposed note
    iterator.

    Parameters
    ----------
    transposed_note_iter : Iterator[Note]
        An independent iterator that iterates over all the notes in a
        transposed score

    Returns
    -------
    Iterator[int]
        An iterator that yields directed motion indices for the independent
        transposed note iterator.
    """
    [transposed_note_iter] = tee(transposed_note_iter, 1)
    pitch_direction_iter = _get_pitch_directions(transposed_note_iter)
    pitch_direction_iter, zero_motion_checker = tee(pitch_direction_iter)
    edge_case = range(1)
    directed_motions = (
        1 - 2 * abs(_int_sign(next_direction - current_direction))
        for current_direction, next_direction in pairwise(pitch_direction_iter)
    )
    directed_motions = chain(edge_case, directed_motions)

    return (
        (elem if check != 0 else 0)
        for elem, check in zip(directed_motions, zero_motion_checker)
    )


def _get_proximity(transposed_note_iter: Iterator[Note]) -> Iterator[int]:
    """
    Returns an iterator that yields the absolute pitch difference for pairwise notes.

    Parameters
    ----------
    transposed_note_iter : Iterator[Note]
        A tee iterator that iterates over all the notes in a transposed score

    Returns
    -------
    Iterator[int]
        An iterator that yields the pitch proximity of each successive pair
        of notes in the transposed score.
    """
    yield 0
    [transposed_note_iter] = tee(transposed_note_iter, 1)
    for prev, current in pairwise(transposed_note_iter):
        yield abs(current.midi_num - prev.midi_num)


def melodic_attraction(score: Score, key: int | None = None) -> Score | None:
    """
    Calculate melodic attraction for each note according to Lerdahl (1996).
    Return the transposed score, where every note is annotated with the
    melodic attraction values (between 0 and 1).
    The annotated field within each note of the annotated transposed score if
    successful is "melodic_attraction."

    The algorithm works as follows:
    Each tone in key has a certain anchoring strength ("weight") in tonal pitch
    space. Melodic attraction strength is dependent on the anchor values dependent
    on the pitch-classes in a two-note window, while is affected by the distance
    between tones.

    The algorithm has two extensions (also ported from miditoolbox):
    Extension 1: attraction is modified not only by subsequent neighbor but also
    on the pitch's other potential neighbors (this is realized in the way
    Lerdahl suggested, not only limiting the attraction to one neighbor but to
    all possible neighbors within a specific window).
    Extension 2: directed motion also affects melodic attraction (this is done somewhat
    differently than in Lerdahl's paper due to modification of the first extension).

    One thing of note is that, our implementation makes extensive use of
    generators, because the author found it to be the easiest way to keep track
    of all the components while minimizing the amount of data structures needed
    to keep track of score notes.

    TODO: Should we include parameter space for more pitch profiles?

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze
    key : int, optional
        MIDI pitch number representing the key. If None, first note is used as tonic

    Returns
    -------
    Score
        Transpose of the original score to C-major, where all the notes are
        annotated with attraction values between 0 and 1

    References
    ----------
        Lerdahl, F. (1996). Calculating tonal tension. Music Perception, 13(3), 319-363.
    """

    if next(score.find_all(Note), None) is None:
        return None
    if not score.ismonophonic():
        return None

    transposed_score = transpose2c(score)
    if transposed_score is None:
        return None
    mode_strs = keymode(transposed_score)
    if mode_strs is None:
        return None

    note_gen = transposed_score.find_all(Note)
    # generate 4 independent tee iterators to generate the new feature iterators
    tee_note_gens = tee(note_gen, 4)

    anchorweights, anchorweights_gen = _get_anchorweights(
        tee_note_gens[0], mode_strs
    )
    direct_motion_gen = _get_directed_motion_indices(tee_note_gens[1])
    proximity_gen = _get_proximity(tee_note_gens[2])

    throwaway_aw_gen, anchorweights_gen = tee(anchorweights_gen)
    first_anchorweight = next(throwaway_aw_gen, None)
    if first_anchorweight is None:
        return None

    # set first note value to 0.0 as in miditoolbox
    annotation_str = "melodic_attraction"
    first_note_gen, transposed_score_iter = tee(tee_note_gens[3])
    first_note = next(first_note_gen, None)
    assert first_note is not None
    first_note.set(annotation_str, 0.0)

    iterators = []
    iterators.append(pairwise(anchorweights_gen))
    iterators.append(direct_motion_gen)
    iterators.append(pairwise(proximity_gen))
    iterators.append(pairwise(transposed_score_iter))

    for anchors, motion_val, proximities, notes in zip(*iterators):
        if anchors[0] >= anchors[1]:
            anchoring_val = 0
        else:
            anchoring_val = _get_lerdahl_attraction(
                anchors[0], anchors[1], proximities[1]
            )
        # pitch window for finding a more stable alternative
        # pitch difference x >= -4 and x < 5
        stable_candidates_window = (-4, 5)

        # check condition for neighbors
        neighbors = [
            anchorweights[(i + notes[0].pitch_class) % 12]
            for i in range(*stable_candidates_window)
        ]

        neighbor_checks = [
            first_anchorweight < neighbor
            for i, neighbor in enumerate(neighbors)
        ]
        neighbor_checks[len(neighbor_checks) // 2] = False

        correction = 0
        # algorithmic extensions that were present in midi_toolbox
        if any(check for check in neighbor_checks):
            original_anchor = notes[1].midi_num - notes[0].midi_num
            new_anchor = neighbor_checks.index(True)
            # checks if the anchor is within the stable candidates window
            if (
                original_anchor < stable_candidates_window[1]
                and original_anchor >= stable_candidates_window[0]
                and new_anchor != original_anchor
            ):
                neighbor_checks[new_anchor] = False
            best_alternative = 0
            sum_of_alternatives = 0.0
            all_alternative_attraction = []
            for i, (neighbor, check) in enumerate(
                zip(neighbors, neighbor_checks)
            ):
                if check:
                    alternative_anchor = neighbor
                    assert alternative_anchor > 0
                    assert anchors[0] > 0
                    distance = abs(i + stable_candidates_window[0])
                    alternative_attraction = _get_lerdahl_attraction(
                        anchors[0], alternative_anchor, distance
                    )
                    sum_of_alternatives += alternative_attraction
                    all_alternative_attraction.append(alternative_attraction)
                    best_alternative = max(
                        best_alternative, alternative_attraction
                    )

            correction = (
                sum_of_alternatives - best_alternative
            ) * 0.5 + best_alternative

        anchoring_val -= correction
        attraction = (motion_val + anchoring_val + 1) / 5
        # clips attraction to be within 0.0 and 1.0
        attraction = max(min(attraction, 1.0), 0.0)
        notes[1].set(annotation_str, attraction)

    return transposed_score
