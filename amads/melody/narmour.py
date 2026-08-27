"""
Predictions from Narmour's implication-realization model

Completely rewrites the original narmour function that Yiwen Zhao first wrote.

Ports the `narmour` function from Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 77.
"""

from collections.abc import Generator
from enum import Enum

import numpy as np

from amads.core.basics import Note, Score


def _simple_int_sign_comparison(val1: int, val2: int) -> bool:
    """
    super simple comparison that checks if the two integer values are of the
    same sign
    """
    return (
        (val1 == 0 and val2 == 0)
        or (val1 > 0 and val2 > 0)
        or (val1 < 0 and val2 < 0)
    )


def _narmour_score_iter_internal(
    score: Score, annotation_str: str
) -> tuple[Generator[Note]] | None:
    """
    note iterator generator specific to narmour principle calculation.
    """
    check_note_iter = score.find_all(Note)
    obtained_notes = [next(check_note_iter, None) for _ in range(3)]
    if not all(isinstance(note, Note) for note in obtained_notes):
        return None
    if not score.ismonophonic():
        return None
    note_iters = (score.find_all(Note),) * 3
    # advance the target iterators forward to where we want
    next(note_iters[1], None)
    next(note_iters[2], None)
    next(note_iters[2], None)

    for note, _ in zip(obtained_notes, range(2)):
        note.set(annotation_str, 0)
    return note_iters


def _registral_direction(score: Score) -> Score | None:
    """
    Calculates registral direction (revised version) as follows:
    if small pitch interval between the first two neighboring notes is at or
    below threshold, annotate with 0
    else, if followed by change in direction, annotate with 1
    and if followed by same direction, annotate with -1
    (Thompson p. 248, Schellenberg 1996)

    The annotated field within each note of the annotated score if successful
    is "narmour_registral_direction"

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.

    Returns
    -------
    Score | None
        Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        None if score does not satisfy the preconditions of having at least
        3 notes and is not monophonic
    """
    annotation_str = "narmour_registral_direction"
    small_interval_threshold = 6
    note_iters = _narmour_score_iter_internal(score, annotation_str)
    if note_iters is None:
        return None
    for notes in zip(*note_iters):
        current_diff = notes[1].midi_num - notes[0].midi_num
        next_diff = notes[2].midi_num - notes[1].midi_num
        if abs(current_diff) <= small_interval_threshold:
            notes[2].set(annotation_str, 0)
        elif abs(
            current_diff
        ) > small_interval_threshold and _simple_int_sign_comparison(
            current_diff, next_diff
        ):
            notes[2].set(annotation_str, 1)
        elif abs(
            current_diff
        ) > small_interval_threshold and not _simple_int_sign_comparison(
            current_diff, next_diff
        ):
            notes[2].set(annotation_str, -1)
        else:
            raise ValueError(f"{current_diff}, {next_diff} are invalid")
    return score


def _registral_return(score: Score) -> Score | None:
    """
    Calculates registral return (revised version) as follows:
    if second realized tone is within 2 semitones of the
    first tone in the implied interval, 1 (or 1.5), others 0.
    Modifier of 1 is used in the version revised by Schellenberg (1996) and
    a better modifier (1.5, which is used) suggested by Schellengerg (1997).

    The annotated field within each note of the annotated score if successful
    is "narmour_registral_return"

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.

    Returns
    -------
    Score | None
        Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        None if score does not satisfy the preconditions of having at least
        3 notes and is not monophonic
    """
    annotation_str = "narmour_registral_return"
    interval_symmetry_check_threshold = 2
    interval_symmetry_modifier = 1.5
    note_iters = _narmour_score_iter_internal(score, annotation_str)
    if note_iters is None:
        return None
    for notes in zip(*note_iters):
        current_diff = notes[1].midi_num - notes[0].midi_num
        next_diff = notes[2].midi_num - notes[1].midi_num
        if abs(current_diff + next_diff) <= interval_symmetry_check_threshold:
            notes[2].set(annotation_str, interval_symmetry_modifier)
        else:
            notes[2].set(annotation_str, 0)
    return score


def _closure(score: Score) -> Score | None:
    """
    Closure occurs when registral direction changes, or when a large interval
    is followed by a smaller interval (i.e. smaller by more than 3 semitones
    if registral direction is the same, or smaller by two semitones otherwise).
    All events that satisfy this condition are assigned a score of 1, and all
    other events are assigned a score of 0.

    The annotated field within each note of the annotated score if successful
    is "narmour_closure"

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.

    Returns
    -------
    Score | None
        Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        None if score does not satisfy the preconditions of having at least
        3 notes and is not monophonic
    """
    annotation_str = "narmour_closure"
    note_iters = _narmour_score_iter_internal(score, annotation_str)
    if note_iters is None:
        return None
    for notes in zip(*note_iters):
        current_diff = notes[1].midi_num - notes[0].midi_num
        next_diff = notes[2].midi_num - notes[1].midi_num
        sign_compare_diffs = _simple_int_sign_comparison(
            current_diff, next_diff
        )
        diff_of_diffs = abs(current_diff) - abs(next_diff)
        if not sign_compare_diffs:
            if diff_of_diffs < 3:
                notes[2].set(annotation_str, 1)
            else:
                notes[2].set(annotation_str, 2)
        else:
            if diff_of_diffs > 3:
                notes[2].set(annotation_str, 1)
            else:
                notes[2].set(annotation_str, 0)

    return score


def _intervallic_difference(score: Score) -> Score | None:
    """
    This states that small implicative intervals (i.e. perfect fourth or less)
    imply similarly-sized realized intervals whereas large implicative
    intervals imply comparatively smaller intervals.
    'Similarly-sized' realized intervals after a small interval are defined as
    the same size +- three semitones if the realized interval does not change
    registral direction, otherwise they are defined as the same size +-two
    semitones.
    All events fulfilling these conditions are assigned a score of 1 whereas
    other events are assigned a value of 0.
    Derived from Schellenberg, 1997, p. 296-297).

    The annotated field within each note of the annotated score if successful
    is "narmour_intervallic_difference"

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.

    Returns
    -------
    Score | None
        Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        None if score does not satisfy the preconditions of having at least
        3 notes and is not monophonic
    """
    annotation_str = "narmour_intervallic_difference"
    small_interval_threshold = 6
    note_iters = _narmour_score_iter_internal(score, annotation_str)
    if note_iters is None:
        return None
    for notes in zip(*note_iters):
        current_diff = notes[1].midi_num - notes[0].midi_num
        next_diff = notes[2].midi_num - notes[1].midi_num
        sign_compare_diffs = _simple_int_sign_comparison(
            current_diff, next_diff
        )
        diff_of_diffs = abs(current_diff) - abs(next_diff)
        if current_diff < small_interval_threshold:
            if (not sign_compare_diffs and abs(diff_of_diffs) < 3) or (
                sign_compare_diffs and abs(diff_of_diffs) < 4
            ):
                notes[2].set(annotation_str, 1)
            else:
                notes[2].set(annotation_str, 0)
        elif current_diff > small_interval_threshold:
            if abs(current_diff) >= abs(next_diff):
                notes[2].set(annotation_str, 1)
            else:
                notes[2].set(annotation_str, 0)
        else:
            notes[2].set(annotation_str, 0)
    return score


def _proximity(score: Score) -> Score | None:
    """
    Linear coding of pitch proximity.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.

    Returns
    -------
    Score | None
        Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        None if score does not satisfy the preconditions of having at least
        2 notes and is not monophonic
    """
    annotation_str = "narmour_proximity"

    check_note_iter = score.find_all(Note)
    obtained_notes = [next(check_note_iter, None) for _ in range(2)]
    if not all(isinstance(note, Note) for note in obtained_notes):
        return None
    if not score.ismonophonic():
        return None
    note_iters = (score.find_all(Note),) * 2
    first_note = next(note_iters[1], None)
    first_note.set(annotation_str, 0)
    for notes in note_iters:
        current_diff = notes[1].midi_num - notes[0].midi_num
        notes[1].set(annotation_str, abs(current_diff))

    return score


def _consonance(pitches: np.ndarray) -> np.ndarray:
    """
    Narmour's model under the consonance principle:
    if consonant with previous tone (see Krumhansl 1995
    "Effects of musical context on similarity and expectancy",
    Systematische musikwissenschaft or Krumhansl (1990), p. 57.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.

    Returns
    -------
    Score | None
        Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        None if score does not satisfy the preconditions of having at least
        3 notes and is not monophonic
    """
    # Consonance ratings from Krumhansl (1995)
    CONSONANCE_RATINGS = {
        0: 1.0,  # unison
        3: 0.6,  # minor third
        4: 0.8,  # major third
        5: 0.7,  # perfect fourth
        7: 0.9,  # perfect fifth
        8: 0.6,  # minor sixth
        9: 0.7,  # major sixth
        12: 0.9,  # octave
    }

    expectations = np.full(len(pitches), np.nan)
    for i in range(2, len(pitches)):
        interval = abs(pitches[i] - pitches[i - 1]) % 12
        expectations[i] = CONSONANCE_RATINGS.get(interval, 0.1)
    return expectations


class NarmourOption(Enum):
    """
    The specific principles and/or corrections to calculate for narmour.

    Attributes
    ----------
    REGISTRAL_DIRECTION: (Schellenberg 1997)
    REGISTRAL_RETURN: (Schellenberg 1997)
    INTERVALLIC_DIFFERENCE: intervallic difference
    PROXIMITY: (Schellenberg 1997)
    CONSONANCE: (Krumhansl 1995)
    """

    REGISTRAL_DIRECTION = "rd"
    REGISTRAL_RETURN = "rr"
    INTERVALLIC_DIFFERENCE = "id"
    CLOSURE = "cl"
    PROXIMITY = "pr"
    CONSONANCE = "co"


def narmour(score: Score, principle: NarmourOption) -> Score:
    """
    Calculate prediction values for a trait in Narmour's Implication-realization
    model, and annotates the individual notes with their corresponding
    predictions. The annotated field can be accessed through the
    <principle> + "_narmour" from a note in the score (e.g.
    "registral_direction_narmour for the registral_direction trait").

    This function implements various principles from Narmour's (1990) model
    of melodic expectancy, including revisions by Schellenberg (1997) and
    Krumhansl (1995).

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.
    principle : NarmourOption
        The specific principle options to calculate.

    Returns
    -------
    Score | None
        Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        None if score does not satisfy the preconditions of having at least
        3 notes and is not monophonic

    References
    ----------
    .. [1] Narmour, E. (1990). The Analysis and cognition of basic melodic
           structures: The Implication-realization model. Chicago: University
           of Chicago Press.
    .. [2] Schellenberg, E. G. (1997). Simplifying the implication-realization
           model of melodic expectancy. Music Perception, 14, 295-318.
    .. [3] Krumhansl, C. L. (1995). Effects of musical context on similarity
           and expectancy. Systematische musikwissenschaft, 3, 211-250.
    """

    # Calculate expectations based on selected principle
    principle_functions = {
        NarmourOption.REGISTRAL_DIRECTION: _registral_direction,
        NarmourOption.REGISTRAL_RETURN: _registral_return,
        NarmourOption.INTERVALLIC_DIFFERENCE: _intervallic_difference,
        NarmourOption.CLOSURE: _closure,
        NarmourOption.PROXIMITY: _proximity,
        NarmourOption.CONSONANCE: _consonance,
    }

    principle_func = principle_functions.get(principle)
    if principle_func is None:
        return None

    return principle_func(score)
