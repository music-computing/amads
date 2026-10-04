"""
Predictions from Narmour's implication-realization model

Completely rewrites the original narmour function that Yiwen Zhao first wrote.

Ports the `narmour` function from Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 77.
"""

from collections import deque
from collections.abc import Iterator
from enum import Enum
from itertools import islice, pairwise, tee

from amads.core.basics import Note, Score


def _simple_int_sign_comparison(val1: int, val2: int) -> bool:
    """
    super simple comparison that checks if the two integer values are of the
    same sign

    Parameters
    ----------
    val1: int
        Integer to compare signage
    val2: int
        Integer to compare signage

    Returns
    -------
    bool
        True if both integers are of the same sign (or are both 0)
        False otherwise
    """
    return (
        (val1 == 0 and val2 == 0)
        or (val1 > 0 and val2 > 0)
        or (val1 < 0 and val2 < 0)
    )


def _sliding_window(iterator: Iterator, n: int) -> Iterator:
    """
    Collect data of an iterator into a sliding window of fixed length.
    Returns the data in overlapping fixed-length chunks or blocks.
    e.g. sliding_window(iter('ABCDEFG'), 3) → ABC BCD CDE DEF EFG

    Parameters
    ----------
    iterator: Iterator
        iterator to return sliding window of.
    n: int
        length of the sliding window

    Yields
    -------
    An n-tuple of consecutive elements from the original iterator
    """
    window = deque(islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)


def _narmour_preprocess_score_internal(
    score: Score, annotation_str: str
) -> Iterator[tuple[Note]] | None:
    """
    Does a few checks that are relevant to certain narmour options,
    and returns an iterator useful for calculating those features.

    Parameters
    ----------
    score: Score
        score to be preprocessed. Must be monophonic and has at least 3 notes.
    annotation_str:
        string annotation label

    Returns
    -------
    Iterator[tuple[Note]] | None
        returns a sliding-window note iterator of length 3 specific to some
        narmour features if the internal requirements are passed
        Otherwise None
    """
    note_iter = score.find_all(Note)
    note_iter, first_slice_iter = tee(note_iter)
    minimum_score_length = 3
    obtained_notes = list(islice(first_slice_iter, minimum_score_length))
    if len(obtained_notes) != minimum_score_length:
        return None
    if not score.ismonophonic():
        return None
    # code pattern obtained from sliding_window itertools documentation
    for note in obtained_notes[:2]:
        note.set(annotation_str, 0)

    return _sliding_window(note_iter, 3)


def _registral_direction(score: Score) -> Score | None:
    """
    Calculates registral direction (revised version) as follows:
    if small pitch interval between the first two neighboring notes is at or
    below threshold, annotate with 0
    else, if followed by change in direction, annotate with 1
    and if followed by same direction, annotate with -1
    (Thompson p. 248, Schellenberg 1996)

    Implements the REGISTRAL_DIRECTION option.

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
    notes_window_iter = _narmour_preprocess_score_internal(
        score, annotation_str
    )
    if notes_window_iter is None:
        return None
    for notes in notes_window_iter:
        current_diff = notes[1].midi_num - notes[0].midi_num
        next_diff = notes[2].midi_num - notes[1].midi_num
        if current_diff <= small_interval_threshold:
            notes[2].set(annotation_str, 0)
        elif (
            current_diff > small_interval_threshold
            and _simple_int_sign_comparison(current_diff, next_diff)
        ):
            notes[2].set(annotation_str, 1)
        elif (
            current_diff > small_interval_threshold
            and not _simple_int_sign_comparison(current_diff, next_diff)
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

    Implements the REGISTRAL_RETURN option.

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
    notes_window_iter = _narmour_preprocess_score_internal(
        score, annotation_str
    )
    if notes_window_iter is None:
        return None
    for notes in notes_window_iter:
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

    Implements the CLOSURE option.

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
    notes_window_iter = _narmour_preprocess_score_internal(
        score, annotation_str
    )
    if notes_window_iter is None:
        return None
    for notes in notes_window_iter:
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

    Implements the INTERVALLIC_DIFFERENCE option.

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
    notes_window_iter = _narmour_preprocess_score_internal(
        score, annotation_str
    )
    if notes_window_iter is None:
        return None
    for notes in notes_window_iter:
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

    Implements the PROXIMITY option.

    The annotated field within each note of the annotated score if successful
    is "narmour_proximity"

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
    if not score.ismonophonic():
        return None

    note_iter = score.find_all(Note)
    check_note_iter, note_iter = tee(note_iter)
    obtained_notes = list(islice(check_note_iter, 2))
    if len(obtained_notes) != 2:
        return None
    obtained_notes[0].set(annotation_str, 0)
    for notes in pairwise(note_iter):
        current_diff = notes[1].midi_num - notes[0].midi_num
        notes[1].set(annotation_str, abs(current_diff))

    return score


def _consonance(score: Score) -> Score | None:
    """
    Narmour's model under the consonance principle:
    if consonant with previous tone (see Krumhansl 1995
    "Effects of musical context on similarity and expectancy",
    Systematische musikwissenschaft or Krumhansl (1990), p. 57.

    Implements the CONSONANCE option.

    The annotated field within each note of the annotated score if successful
    is "narmour_consonance"

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
    CONSONANCE_RATINGS = [
        10,
        1,
        4.16,
        6.03,
        7.25,
        8.03,
        5.76,
        9.16,
        6.32,
        7.76,
        5.66,
        3.8,
    ]
    annotation_str = "narmour_consonance"

    note_iter = score.find_all(Note)
    note_iter, check_note_iter = tee(note_iter)
    obtained_notes = list(islice(check_note_iter, 2))
    if len(obtained_notes) != 2:
        return None
    if not score.ismonophonic():
        return None
    obtained_notes[0].set(annotation_str, CONSONANCE_RATINGS[0])

    for notes in pairwise(note_iter):
        rating_idx = abs(notes[1].midi_num - notes[0].midi_num) % 12
        consonance_rating = CONSONANCE_RATINGS[rating_idx]
        notes[1].set(annotation_str, consonance_rating)

    return score


class NarmourOption(Enum):
    """
    The specific principles and/or corrections to calculate for narmour.

    The string values for all of these options contain their corresponding
    note label string for when the call to narmour succeeds in processing a
    score.

    Attributes
    ----------
    REGISTRAL_DIRECTION : (Schellenberg 1997)
        Original 'rd' option from midi toolbox
    REGISTRAL_RETURN : (Schellenberg 1997)
        Original 'rr' option from midi toolbox
    INTERVALLIC_DIFFERENCE : intervallic difference
        Original 'id' option from midi toolbox
    CLOSURE : closure
        Original 'cl' option from midi toolbox
    PROXIMITY : (Schellenberg 1997)
        Original 'pr' option from midi toolbox
    CONSONANCE : (Krumhansl 1995)
        Original 'co' option from midi toolbox
    """

    REGISTRAL_DIRECTION = "narmour_registral_direction"
    REGISTRAL_RETURN = "narmour_registral_return"
    INTERVALLIC_DIFFERENCE = "narmour_intervallic_difference"
    CLOSURE = "narmour_closure"
    PROXIMITY = "narmour_proximity"
    CONSONANCE = "narmour_consonance"


def narmour(score: Score, principle: NarmourOption) -> tuple[Score, str] | None:
    """
    Calculate prediction values for a trait in Narmour's Implication-realization
    model, and annotates the individual notes with their corresponding
    predictions. The annotated field can be accessed through the
    <principle> + "_narmour" from a note in the score (e.g.
    "registral_direction_narmour for the registral_direction trait").

    This function implements various principles from Narmour's (1990) model
    of melodic expectancy, including revisions by Schellenberg (1997) and
    Krumhansl (1995).

    Please see the comments for the internal functions detailing what each
    flavor of narmour is doing.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.
    principle : NarmourOption
        The specific principle options to calculate.

    Returns
    -------
    tuple[Score, str] | None
        Returns 2 things if successful:
        (1) Score where each note is annotated with a value calculated according
        to the desired narmour principle.
        (2) annotation string used to annotate the values obtained by that
        particular narmour option.
        Else:
        None if score does not satisfy the preconditions of being monophonic
        or if the score does not satisfy the preconditions necessary to calculate
        the specified feature.

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
    feature_functions = {
        NarmourOption.REGISTRAL_DIRECTION: _registral_direction,
        NarmourOption.REGISTRAL_RETURN: _registral_return,
        NarmourOption.INTERVALLIC_DIFFERENCE: _intervallic_difference,
        NarmourOption.CLOSURE: _closure,
        NarmourOption.PROXIMITY: _proximity,
        NarmourOption.CONSONANCE: _consonance,
    }

    feature_func = feature_functions.get(principle)
    if feature_func is None:
        return None
    annotation_str = principle.value
    result = feature_func(score)
    if result is None:
        return None

    return (result, annotation_str)
