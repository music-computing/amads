"""
Make sense of the relationship between
the notes in
and
the hierarchy of
a metrical cycle.

Uses include identifying notes that traverse metrical levels,
for anaylsis (e.g., as a measure of syncopation)
and notation (e.g., re-notating to reflect the
within-measure notational conventions).

This delivers functionality promised in previous discussions on the music21
list (https://groups.google.com/g/music21list/c/5G-UafJeW94/m/YcEBE0PFAQAJ)
and repo (issue 992, https://github.com/cuthbertLab/music21/issues/992)

Basically, the idea is that
a single note can only cross metrical boundaries
for levels lower than the one it starts on.
If it traverses a metrical boundaries at a higher level, then
it is split at that position into two note-heads to be connected by a tie.


TODO:
- Connect up to scores (work with note and time signature by context).
- Divide the metrical structure logic from the operations

"""

from typing import Optional, Union

import numpy as np

# ------------------------------------------------------------------------------


class ReGrouper:
    """
    Split up notes and rests to reflect the
    within-measure notational conventions
    of metrical hierarchies in Western classical music.

    This class
    takes in a representation of a note in terms of the start position and duration,
    and metrical context (the overall structure, and which part to use), and
    returns a list of start-duration pairs for the broken-up note value.

    The basic premise here is that a single note can only traverse metrical boundaries
    for levels lower than the one it starts on.
    If it traverses the metrical boundary of a higher level, then
    it is split at that position into two note-heads to be connected by a tie.

    There are many variants on this basic set up.
    This class aims to support almost any such variant, while providing easy defaults
    for simple, standard practice.

    The flexibility comes from the definition of a metrical structure.
    Here, everything ultimately runs through a single representation
    of metrical levels in terms of starts expressed by quarter length
    from the start of the measure,
    e.g., levels 0-3 of a time signature like 4/4 would be represented as:
    [[0.0, 4.0],
    [0.0, 2.0, 4.0],
    [0.0, 1.0, 2.0, 3.0, 4.0],
    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]]

    Each split of the note duration serves to move up one metrical level.
    For instance, for the 4/4 example above, a note of duration 2.0 starting at start
    0.25 connects to 0.5 in level 3 (duration = 0.25), then
    0.5 connects to 1.0 in level 2 (duration = 0.5), then
    1.0 connects to 2.0 in level 1 (duration = 1.0), and
    this leaves a duration of 0.25 to start on start 2.0.
    The data is returned as a list of (position, duration) tuples.
    The values for the example would be:
    [(0.25, 0.25),
    (0.5, 0.5),
    (1.0, 1.0),
    (1.0, 0.25)].

    There are three main user options (for advanced use cases only):
    tweak a metrical hierarchy to only consider certain levels (see the `levels` parameter);
    define a metrical structure completely from scratch (`start_hierarchy`);
    determine the handling of splits within a level for metres like 6/8 (`split_same_level`).

    The input parameters are:

    note_start_start:
    the note or rest in question"s starting start.

    note_length:
    the note or rest"s length.

    time_signature (optional):
    the time signature (currently expressed as a string).
    to be converted into a start_hierarchy.

    levels (optional):
    the default arrangement is to use all levels of a time signature"s metrical hierarchy.
    Alternatively, this parameter allows users to select certain levels for in-/exclusion.
    See the starts_from_ts_and_levels function for further explanation.

    pulse_lengths (optional):
    this provides an alternative way of expressing the metrical hierarchy
    in terms of pulse lengths (by quarter length), again
    to be converted into a start_hierarchy.
    See start_list_from_pulse_lengths for further explanation.

    start_hierarchy (optional):
    a final alternative way of expressing the metrical hierarchy
    completely from scratch (ignoring all other parameters and defaults).
    Use this for advanced cases requiring non-standard metrical structures
    including those without 2-/3- grouping, or even nested hierarchies.

    split_same_level:
    in cases of metrical structures with a 3-grouping
    (i.e., two "weak" events between a "strong" in compound signatures like 6/8)
    some conventions chose to split notes within-level as well as between them.
    For instance, with a quarter note starting on the second eighth note (start 0.5) of 6/8,
    some will want to split that into two 1/8th notes, divided on the third eighth note position,
    while others will want to leave this intact.
    The split_same_level option accommodates this:
    it effects the within-level split when set to True and not otherwise (default).

    At least one of
    time_signature,
    levels (with a time_signature),
    pulse_lengths, or
    start_hierarchy
    must be specified.

    These are listed in order from the most standard to the most specialised.
    The time_signature defaults will serve most use cases, and the
    "levels" parameter should be enough for a particular editorial style.
    """

    def __init__(
        self,
        note_start_start: Union[int, float],
        note_length: Union[int, float],
        time_signature: Optional[str] = None,
        levels: Optional[list] = None,
        pulse_lengths: Optional[list] = None,
        start_hierarchy: Optional[list] = None,
        split_same_level: bool = False,
    ):

        # Retrieve or create the metrical structure
        if start_hierarchy:
            self.start_hierarchy = start_hierarchy
        elif pulse_lengths:
            self.start_hierarchy = start_list_from_pulse_lengths(
                pulse_lengths, require_2_or_3_between_levels=False
            )
        elif levels:
            if not time_signature:
                raise ValueError(
                    "To specify levels, please also enter a valid time signature."
                )
            self.start_hierarchy = starts_from_ts_and_levels(time_signature, levels)
        else:  # time_signature, not levels specified
            self.start_hierarchy = starts_from_ts_and_levels(time_signature)

        if not self.start_hierarchy:
            raise ValueError(
                "Cannot create a `start_hierarchy`. "
                "Please enter a valid time signature or equivalent."
            )

        self.note_length = note_length
        self.note_start_start = note_start_start
        self.split_same_level = split_same_level

        # Initialise
        self.start_duration_pairs = []
        self.updated_start = note_start_start
        self.remaining_length = note_length
        self.level_pass()

    # ------------------------------------------------------------------------------

    def level_pass(self):
        """
        Having established the structure of the start_hierarchy,
        this method iterates across the levels of that hierarchy to find
        the current start position, and (through advance_step) the start position to map to.

        This method runs once for each such mapping,
        typically advancing up one (or more) layer of the metrical hierarchy with each call.
        "Typically" because split_same_level is supported where relevant.

        Each iteration creates a new start-duration pair
        stored in the start_duration_pairs list
        that records the constituent parts of the split note.
        """

        for levelIndex in range(len(self.start_hierarchy)):

            if (
                self.remaining_length <= 0
            ):  # sic, here due to the various routes through
                return

            this_level = self.start_hierarchy[levelIndex]

            if self.updated_start in this_level:
                if levelIndex == 0:  # i.e., updated_start == 0
                    self.start_duration_pairs.append(
                        (self.updated_start, self.remaining_length)
                    )
                    return
                else:  # level up. NB: duplicates in nested hierarchy help here
                    if self.split_same_level:  # relevant option for e.g., 6/8
                        self.advance_step(this_level)
                    else:  # usually
                        self.advance_step(self.start_hierarchy[levelIndex - 1])

        if self.remaining_length > 0:  # start not in the hierarchy at all
            self.advance_step(self.start_hierarchy[-1])  # get to the lowest level
            # Now start the process with the metrical structure:
            self.level_pass()

    def advance_step(self, positions_list: list):
        """
        For a start position, and a metrical level expressed as a list of starts,
        finds the next higher value from those levels.
        Used for determining iterative divisions.
        """
        for p in positions_list:
            if p > self.updated_start:
                duration_to_next_position = p - self.updated_start
                if self.remaining_length <= duration_to_next_position:
                    self.start_duration_pairs.append(
                        (self.updated_start, self.remaining_length)
                    )
                    # done but still reduce remaining_length to end the whole process in level_pass
                    self.remaining_length -= duration_to_next_position
                    return
                else:  # self.remaining_length > duration_to_next_position:
                    self.start_duration_pairs.append(
                        (self.updated_start, duration_to_next_position)
                    )
                    # Updated start and position; run again
                    self.updated_start = p
                    self.remaining_length -= duration_to_next_position
                    self.level_pass()  # NB: to re-start from top as may have jumped a level
                    return


# ------------------------------------------------------------------------------


def start_hierarchy_from_ts(ts_str: str, minimum_pulse: int = 64):
    """
    Create a start hierarchy for almost any time signature
    directly from a string (e.g., "4/4") without dependencies.
    Returns a list of lists with start positions by level.

    The following examples index the most interesting level:

    >>> start_hierarchy_from_ts("4/4")[1]  # note the half cycle division
    [0.0, 2.0, 4.0]


    >>> start_hierarchy_from_ts("6/8")[1]  # note the macro-beat division
    [0.0, 1.5, 3.0]


    Numerators like 5 and 7 are supported.
    Use the total value only to avoid segmentation about the denominator level:

    >>> start_hierarchy_from_ts("5/4")[1]  # note no 2+3 or 3+2 level division
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]

    Or use numerator addition in the form "X+Y/Z" to clarify this level ...

    >>> start_hierarchy_from_ts("2+3/4")[1]  # note the 2+3 division
    [0.0, 2.0, 5.0]

    >>> start_hierarchy_from_ts("2+2+3/8")[1]  # note the 2+2+3 division
    [0.0, 1.0, 2.0, 3.5]

    >>> start_hierarchy_from_ts("2+2+2+3/8")[1]  # note the 2+2+2+3 division
    [0.0, 1.0, 2.0, 3.0, 4.5]

    Only standard denominators are supported:
    i.e., time signatures in the form X/ one of
    1, 2, 4, 8, 16, 32, or 64.
    No so-called "irrational" meters yet (e.g., 2/3), sorry!

    Likewise the minimum_pulse must be set to one of these values
    (default = 64 for 64th note) and not be longer than the meter.

    TODO:
    Whole signatures added together in the form "P/Q+R/S"
    (split by "+" before "/").
    """

    # Prep and checks
    numerator, denominator = ts_str.split("/")
    numerators = [int(x) for x in numerator.split("+")]
    denominator = int(denominator)
    # TODO ?regex for more than one "/", e.g., `4/4 + 3/8` = split by `+` first

    supported_denominators = [1, 2, 4, 8, 16, 32, 64]
    if denominator not in supported_denominators:
        raise ValueError(
            "Invalid time signature denominator; chose from one of:"
            f" {supported_denominators}."
        )
    if minimum_pulse not in supported_denominators:
        raise ValueError(
            "Invalid minimum_pulse: it should be expressed as a note value, from one of"
            f" {supported_denominators}."
        )

    # Prep. "hiddenLayer"/s
    hidden_layer_mappings = (
        ([4], [2, 2]),
        ([6], [3, 3]),
        ([9], [3, 3, 3]),  # alternative groupings need to be set out, e.g., 2+2+2+3
        ([12], [[6, 6], [3, 3, 3, 3]]),  # " e.g., 2+2+2+3
        ([15], [3, 3, 3, 3, 3]),  # " e.g., 2+2+2+3
        ([6, 9], [[6, 9], [3, 3, 3, 3, 3]]),  # TODO generalise
        ([9, 6], [[6, 6], [3, 3, 3, 3, 3]]),
    )

    for h in hidden_layer_mappings:
        if numerators == h[0]:
            numerators = h[1]

    if isinstance(numerators[0], list):
        sum_num = sum(numerators[0])
    else:
        sum_num = sum(numerators)

    measure_length = sum_num * 4 / denominator

    # Now ready for each layer in order:

    # 1. top level = whole cycle (always included as entry[0])
    start_hierarchy = [[0.0, measure_length]]

    # 2. "hidden" layer/s
    if len(numerators) > 1:  # whole cycle covered.
        if isinstance(numerators[0], list):
            for level in numerators:
                starts = starts_from_beat_pattern(level, denominator)
                start_hierarchy.append(starts)
        else:
            starts = starts_from_beat_pattern(numerators, denominator)
            start_hierarchy.append(starts)

    # 3. Finally, everything at the denominator level and shorter:
    this_denominator_power = supported_denominators.index(denominator)
    max_denominator_power = supported_denominators.index(minimum_pulse)

    for this_denominator in supported_denominators[
        this_denominator_power : max_denominator_power + 1
    ]:
        this_ql = 4 / this_denominator
        starts = starts_from_lengths(measure_length, this_ql)
        start_hierarchy.append(starts)

    return start_hierarchy


def starts_from_ts_and_levels(
    ts_str: str,  # TODO Union[str, meter.time_signature] or similar
    levels: Union[list, None] = None,
    use_music21: bool = False,
):
    """
    Gets starts from a time signature and a list of levels.
    Records the starts associated with each level as a list,
    and return a list of those lists.

    Levels are defined by the hierarchies recorded in the time signature.
    The 0th level for the full cycle (start 0.0 and full measure length) is always included.
    "1" stands for the 1st level below that of the full metrical cycle
    (e.g., a half cycle of 4/4 and similar time signtures like 2/2).
    "2" is the next level down, (quarter cycle) and so on.

    The function arranges a list of levels in increasing order:
    level 0 is always included, and
    the maximum permitted level (depth) is 6.

    Level choices do not need to be successive:
    e.g., in 4/4 a user could choose [1, 3],
    with 1 standing for the half note level,
    3 for the eight note level,
    and skipping in intervening level 2 (quarter note).

    This function provides a hard-coded workaround that"s called when use_music21=False (default).
    Note also the inclusion of the full cycle length here (useful in ReGrouper).
    >>> starts_from_ts_and_levels("6/8", [1, 2], use_music21=False)
    [[0.0, 3.0], [0.0, 1.5, 3.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]]

    The music21 beamSequence method may also be useful here (i.e., integrating the two).
    See discussion on music21, issue 992.
    """
    if levels is None:
        levels = [0, 1, 2, 3]

    if max(levels) > 6:
        raise ValueError("6 is the maximum level depth supported.")
    levels = sorted(levels)  # smallest first
    if 0 not in levels:  # likely, and not a problem
        levels = [0] + levels  # Always have level 0 as first entry

    starts_by_level = []

    if use_music21:
        from music21 import meter

        ms = meter.MeterSequence(ts_str)
        ms.subdivideNestedHierarchy(max(levels))
        for level in levels:
            starts_this_level = [x[0] for x in ms.getLevelSpan(level)]
            starts_by_level.append(starts_this_level)
    else:
        full_hierarchy = start_hierarchy_from_ts(ts_str)
        for level in levels:
            starts_by_level.append(full_hierarchy[level])

    return starts_by_level


def start_list_from_pulse_lengths(
    pulse_lengths: list,
    measure_length: Union[float, int, None] = None,
    require_2_or_3_between_levels: bool = False,
):
    """
    Convert a list of pulse lengths into a corresponding list of lists
    with start positions per metrical level.
    All values (pulse lengths, start positions, and measure_length)
    are all expressed in terms of quarter length.

    The measure_length is not required - if not provided it's taken to be the longest pulse length.

    >>> qsl = start_list_from_pulse_lengths(pulse_lengths=[4, 2, 1, 0.5])

    >>> qsl[0]
    [0.0, 4.0]

    >>> qsl[1]
    [0.0, 2.0, 4.0]

    >>> qsl[2]
    [0.0, 1.0, 2.0, 3.0, 4.0]

    >>> qsl[3]
    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

    This does not work for ("nonisochronous") pulse streams of varying duration
    in time signatures like 5/x, 7/x
    (e.g., the level of 5/4 with dotted/undotted 1/2 notes).

    It is still perfectly fine to use this for the pulse streams
    within those meters that are regular, equally spaced ("isochronous")
    (e.g., the 1/4 note level of 5/4).

    The list of pulse lengths is set in decreasing order.

    If `require_2_or_3_between_levels` is True (default), this functions checks that
    each level is either a 2 or 3 multiple of the next.

    By default, the measure_length is taken by the longest pulse length.
    Alternatively, this can be user-defined to anything as long as it is
    1) longer than the longest pulse and
    2) if `require_2_or_3_between_levels` is True then exactly 2x or 3x longer.
    """

    pulse_lengths = sorted(pulse_lengths)[::-1]  # largest number first

    if not measure_length:
        measure_length = float(pulse_lengths[0])

    else:
        if pulse_lengths[0] > measure_length:
            raise ValueError("_pulse lengths cannot be longer than the measure_length.")

    if require_2_or_3_between_levels:
        for level in range(len(pulse_lengths) - 1):
            if pulse_lengths[level] / pulse_lengths[level + 1] not in [2, 3]:
                raise ValueError(
                    "The proportion between consecutive levels is not 2 or 3 in "
                    f"this case: {pulse_lengths[level]}:{pulse_lengths[level + 1]}."
                )

    start_list = []

    for pulse_length in pulse_lengths:
        starts = starts_from_lengths(measure_length, pulse_length)
        start_list.append(starts)

    return start_list


# ------------------------------------------------------------------------------

# Subsidiary one-level converters


def starts_from_lengths(
    measure_length: Union[float, int],
    pulse_length: Union[float, int],
    include_measure_length: bool = True,
    use_numpy: bool = True,
):
    """
    Convert a pulse length and measure length into a list of starts.
    All expressed in quarter length.
    If `include_measure_length` is True (default) then each level ends with the full cycle length
    (i.e., the start of the start of the next cycle).
    """
    if use_numpy:
        starts = [float(i) for i in np.arange(0, measure_length, pulse_length)]
    else:  # music21 avoids numpy right?
        current_index = 0
        starts = []
        while current_index < measure_length:
            starts.append(float(current_index))  # float for type consistency
            current_index += pulse_length

    if include_measure_length:
        return starts + [measure_length]
    else:
        return starts


def starts_from_beat_pattern(
    beat_list: list, denominator: Union[float, int], include_measure_length: bool = True
):
    """
    Converts a list of beats
    like [2, 2, 2]
    or [3, 3]
    or indeed
    [6, 9]
    into a list of starts.
    """
    starts = []
    count = 0
    for x in beat_list:
        this_start = count * 4 / denominator
        starts.append(this_start)
        count += x
    if include_measure_length:  # include last value
        this_start = count * 4 / denominator
        starts.append(this_start)
    return starts


# ------------------------------------------------------------------------------

# Examples of the start hierarchy structures.
# For reference and testing.
# Down to 1/32 note level [0, 0.125 ... ] in each case
# TODO preference for this explicit listing or in the form e.g., [float(x) for x in range(8)]
# TODO here or move to resources?

start_hierarchy_examples = {
    "2/2": [
        [0.0, 4.0],
        [0.0, 2.0, 4.0],
        [0.0, 1.0, 2.0, 3.0, 4.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
        ],
    ],
    "3/2": [
        [0.0, 6.0],
        [0.0, 2.0, 4.0, 6.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
            5.25,
            5.5,
            5.75,
            6.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
            5.125,
            5.25,
            5.375,
            5.5,
            5.625,
            5.75,
            5.875,
            6.0,
        ],
    ],
    "4/2": [
        [0.0, 8.0],
        [0.0, 4.0, 8.0],
        [0.0, 2.0, 4.0, 6.0, 8.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [
            0.0,
            0.5,
            1.0,
            1.5,
            2.0,
            2.5,
            3.0,
            3.5,
            4.0,
            4.5,
            5.0,
            5.5,
            6.0,
            6.5,
            7.0,
            7.5,
            8.0,
        ],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
            5.25,
            5.5,
            5.75,
            6.0,
            6.25,
            6.5,
            6.75,
            7.0,
            7.25,
            7.5,
            7.75,
            8.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
            5.125,
            5.25,
            5.375,
            5.5,
            5.625,
            5.75,
            5.875,
            6.0,
            6.125,
            6.25,
            6.375,
            6.5,
            6.625,
            6.75,
            6.875,
            7.0,
            7.125,
            7.25,
            7.375,
            7.5,
            7.625,
            7.75,
            7.875,
            8.0,
        ],
    ],
    "2/4": [
        [0.0, 2.0],
        [0.0, 1.0, 2.0],
        [0.0, 0.5, 1.0, 1.5, 2.0],
        [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
        ],
    ],
    "3/4": [
        [0.0, 3.0],
        [0.0, 1.0, 2.0, 3.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
        ],
    ],
    "4/4": [
        [0.0, 4.0],
        [0.0, 2.0, 4.0],
        [0.0, 1.0, 2.0, 3.0, 4.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
        ],
    ],
    "6/8": [
        [0.0, 3.0],
        [0.0, 1.5, 3.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
        ],
    ],
    "9/8": [
        [0.0, 4.5],
        [0.0, 1.5, 3.0, 4.5],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
        ],
    ],
    "12/8": [
        [0.0, 6.0],
        [0.0, 3.0, 6.0],
        [0.0, 1.5, 3.0, 4.5, 6.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
            5.25,
            5.5,
            5.75,
            6.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
            5.125,
            5.25,
            5.375,
            5.5,
            5.625,
            5.75,
            5.875,
            6.0,
        ],
    ],
    "2+3/4": [
        [0.0, 5.0],
        [0.0, 2.0, 5.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
        ],
    ],
    "3+2/4": [
        [0.0, 5.0],
        [0.0, 3.0, 5.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
        ],
    ],
    "2+2+3/4": [
        [0.0, 7.0],
        [0.0, 2.0, 4.0, 7.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
            5.25,
            5.5,
            5.75,
            6.0,
            6.25,
            6.5,
            6.75,
            7.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
            5.125,
            5.25,
            5.375,
            5.5,
            5.625,
            5.75,
            5.875,
            6.0,
            6.125,
            6.25,
            6.375,
            6.5,
            6.625,
            6.75,
            6.875,
            7.0,
        ],
    ],
    "3+2+2/4": [
        [0.0, 7.0],
        [0.0, 3.0, 5.0, 7.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
            5.25,
            5.5,
            5.75,
            6.0,
            6.25,
            6.5,
            6.75,
            7.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
            5.125,
            5.25,
            5.375,
            5.5,
            5.625,
            5.75,
            5.875,
            6.0,
            6.125,
            6.25,
            6.375,
            6.5,
            6.625,
            6.75,
            6.875,
            7.0,
        ],
    ],
    "2+3+2/4": [
        [0.0, 7.0],
        [0.0, 2.0, 5.0, 7.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0],
        [
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
            4.0,
            4.25,
            4.5,
            4.75,
            5.0,
            5.25,
            5.5,
            5.75,
            6.0,
            6.25,
            6.5,
            6.75,
            7.0,
        ],
        [
            0.0,
            0.125,
            0.25,
            0.375,
            0.5,
            0.625,
            0.75,
            0.875,
            1.0,
            1.125,
            1.25,
            1.375,
            1.5,
            1.625,
            1.75,
            1.875,
            2.0,
            2.125,
            2.25,
            2.375,
            2.5,
            2.625,
            2.75,
            2.875,
            3.0,
            3.125,
            3.25,
            3.375,
            3.5,
            3.625,
            3.75,
            3.875,
            4.0,
            4.125,
            4.25,
            4.375,
            4.5,
            4.625,
            4.75,
            4.875,
            5.0,
            5.125,
            5.25,
            5.375,
            5.5,
            5.625,
            5.75,
            5.875,
            6.0,
            6.125,
            6.25,
            6.375,
            6.5,
            6.625,
            6.75,
            6.875,
            7.0,
        ],
    ],
}


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
