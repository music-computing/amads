"""
This module serves to map out metrical hierarchies in a number of different ways and
to express the relationship between
the notes in
and
the hierarchy of
a metrical cycle.

Uses include identifying notes that traverse metrical levels,
for analysis (e.g., as a measure of syncopation)
and notation (e.g., re-notating to reflect the
within-measure notational conventions).
"""

from typing import Optional, Union

# ------------------------------------------------------------------------------


class MetricalHierarchy:
    """
    This class serves to create standard, interoperable representations
    of metrical hierarchy,
    centred on a single representation
    of metrical levels in terms of starts expressed by quarter length
    from the start of the measure,
    and (optionally) other representations.

    At least one of the parameters (below) must be specified.
    These are listed in order of override, e.g., if a full `start_hierarchy` is specified, all else are ignored.

    For a 'quick start', the `time_signature` defaults will serve most use cases, and
    that along with `levels` should be cover almost all.

    Parameters
    ----------
    start_hierarchy
        Users can specify the `start_hierarchy` directly
        and completely from scratch (ignoring all other parameters and defaults).
        Use this for advanced, non-standard metrical structures
        including those without 2-/3- grouping, or even nested hierarchies.

    pulse_lengths
        In absense of a `start_hierarchy`, users can specify the structure by
        `pulse_lengths` e.g., in the form [4, 2, 1].
        This will be converted into a `start_hierarchy`.
        See `starts_from_pulse_lengths` for further explanation.

    time_signature
        Alternatively, in absense of a `start_hierarchy` or `pulse_lengths` entry,
        users can specify a `time_signature` (str) from which a `start_hierarchy` can be created.
        See `starts_from_ts` for further explanation.

    levels
        If provided with a `time_signature`, optionally also specify the levels of the metrical hierarchy.
        The default arrangement is to use all levels of a time signature's implied metrical hierarchy.
        Alternatively, this parameter allows users to select certain levels for in-/exclusion.
        See the `starts_from_ts_and_levels` function for further explanation.

    names
        Optionally create a dict mapping temporal positions to names.
        Currently, this supports one textual value per temporal position (key),
        e.g., {0.0: "ta", 1.0: "ka", 2.0: "di", 3.0: "mi"}.


    Examples
    --------
    4/4 can be created and represented as follows:

    >>> four_four = MetricalHierarchy("4/4")

    This retains the assigned time signature name:

    >>> four_four.time_signature
    '4/4'

    It also builds a corresponding `start_hierarchy` in several levels:

    >>> four_four.start_hierarchy[0]
    [0.0, 4.0]

    >>> four_four.start_hierarchy[1]
    [0.0, 2.0, 4.0]

    >>> four_four.start_hierarchy[2]
    [0.0, 1.0, 2.0, 3.0, 4.0]

    This same structure can be created in many ways as outlined in the parameters.
    For example:

    Hierarchies can be created directly.

    >>> hierarchy = MetricalHierarchy(start_hierarchy=[[0.0, 4.0], [0.0, 2.0, 4.0]])
    >>> hierarchy.start_hierarchy
    [[0.0, 4.0], [0.0, 2.0, 4.0]]

    They can be made from a list of `pulse_lengths`

    >>> four_four_from_pulses = MetricalHierarchy(pulse_lengths=[4, 2, 1])
    >>> four_four_from_pulses.start_hierarchy[0]
    [0.0, 4.0]

    >>> four_four_from_pulses.start_hierarchy[1]
    [0.0, 2.0, 4.0]

    >>> four_four_from_pulses.start_hierarchy[2]
    [0.0, 1.0, 2.0, 3.0, 4.0]

    Those levels of the hierarchy are the same, only the number of levels differs.

    Speaking of levels, they cn be specified by index alongside the time signature string.

    >>> level_test = MetricalHierarchy(time_signature="6/8", levels=[1, 2])
    >>> level_test.start_hierarchy
    [[0.0, 3.0], [0.0, 1.5, 3.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]]

    Again, for more on these converters, see the static function in this module,
    e.g., `starts_from_ts`, `starts_from_ts_and_levels`.

    """

    def __init__(
        self,
        time_signature: Optional[str] = None,
        levels: Optional[list] = None,
        pulse_lengths: Optional[list] = None,
        start_hierarchy: Optional[list] = None,
        names: Optional[dict] = None,
    ):
        # Retrieve or create the metrical structure
        if start_hierarchy:
            self.start_hierarchy = start_hierarchy
            return
        elif pulse_lengths:
            self.pulse_lengths = pulse_lengths
            self.start_hierarchy = starts_from_pulse_lengths(
                pulse_lengths, require_2_or_3_between_levels=False
            )
            return
        elif levels:
            self.levels = levels
            if time_signature:  # both time signature and levels
                self.time_signature = time_signature
                self.start_hierarchy = starts_from_ts_and_levels(time_signature, levels)
            else:  # no time signature, yes levels
                raise ValueError(
                    "To specify levels, please also enter a valid time signature."
                )
        elif time_signature:  # time signature and no levels, assume all
            self.time_signature = time_signature
            self.start_hierarchy = starts_from_ts(time_signature)
        else:
            raise ValueError(
                "Specify at least one of `start_hierarchy`, `pulse_length` or `time_signature`"
            )

        if names:
            for key in names:
                assert isinstance(key, float)
                assert isinstance(names[key], str)


class MetricalSplitter:
    """
        Split up notes and rest to reflect a specified metrical hierarchies.

        This class
        takes in a representation of a note in terms of the start position and duration,
        along with a metrical context
        and returns a list of start-duration pairs for the broken-up note value.

        The metrical context should be expressed in the form of a `q
        (effectively a list of lists for the hierarchy).
        This can be provided directly, or made via the `MetricalHierarchy` class.
        See notes on that class for the creation of hierarchies suitable to the task at hand
        via a range of entry point.

        The basic premise here is that a single note can only traverse metrical boundaries
        for levels lower than the one it starts on.
        If it traverses the metrical boundary of a higher level, then
        it is split at that position into two note-heads.
        This split registers as a syncopation for those algorithms
        and as a case for two note-heads to be connected by a tie in notation.

        There are many variants on this basic set up.
        This class aims to support almost any such variant, while providing easy defaults
        for simple, standard practice.

        The flexibility comes from the definition of a metrical structure
        (for which see the `MetricalHierarchy` class).

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
        (1.0, 0.25)]
        as demonstrated at ** below.

        Parameters
        -------
        note_start: float
            The starting position of the note (or rest).

        note_length: float,
            The length (duration) of the note (or rest).

        meter: MetricalHierarchy,
            The metrical strcuture to compare.

        split_same_level: bool
            When creating hierarchies, decide whether to split elements at the same level, e.g., 1/8 and 2/8 in 6/8.
            In cases of metrical structures with a 3-grouping
            (two "weak" events between a "strong" in compound signatures like 6/8)
            some conventions chose to split notes within-level as well as between them.
            For instance, with a quarter note starting on the second eighth note (start 0.5) of 6/8,
            some will want to split that into two 1/8th notes, divided on the third eighth note position,
            while others will want to leave this intact.
            The `split_same_level` option accommodates this:
            it effects the within-level split when set to True and not otherwise (default).

        Examples
        -------
        >>> m = MetricalHierarchy("4/4")
        >>> split = MetricalSplitter(0.25, 2.0, meter=m)
        >>> split.start_duration_pairs
        [(0.25, 0.25), (0.5, 0.5), (1.0, 1.0), (2.0, 0.25)]

        If the note runs past the end of the metrical span,
        the remaining value is stored as follows:

        >>> split = MetricalSplitter(0.25, 4.0, meter=m)
        >>> split.start_duration_pairs
        [(0.25, 0.25), (0.5, 0.5), (1.0, 1.0), (2.0, 2.0)]

        >>> split.remaining_length
        0.25

        If the `note_start` is not in the hierarchy,
        then the fist step is to map to the next nearest value in the lowest level.

        >>> split = MetricalSplitter(0.05, 2.0, meter=m)
        >>> split.start_duration_pairs
        [(0.05, 0.0125), (0.0625, 0.0625), (0.125, 0.125), (0.25, 0.25), (0.5, 0.5), (1.0, 1.0), (2.0, 0.05)]

    )

    """

    def __init__(
        self,
        note_start: float,
        note_length: float,
        meter: MetricalHierarchy,
        split_same_level: bool = True,
    ):

        self.note_length = note_length
        self.note_start = note_start
        self.meter = meter
        self.start_hierarchy = meter.start_hierarchy
        self.split_same_level = split_same_level

        # Initialise
        self.start_duration_pairs = []
        self.updated_start = note_start
        self.remaining_length = note_length
        self.level_pass()

    # ------------------------------------------------------------------------------

    def level_pass(self):
        """
        Given a `start_hierarchy`,
        this method iterates across the levels of that hierarchy to find
        the current start position, and (through `advance_step`) the start position to map to.

        This method runs once for each such mapping,
        typically advancing up one (or more) layer of the metrical hierarchy with each call.
        "Typically" because `split_same_level` is supported where relevant.

        Each iteration creates a new start-duration pair
        stored in the start_duration_pairs list
        that records the constituent parts of the split note.
        """

        for level_index in range(len(self.start_hierarchy)):

            if (
                self.remaining_length <= 0
            ):  # sic, here due to the various routes through
                return

            if (
                self.updated_start == self.start_hierarchy[0][-1]
            ):  # finished metrical span
                return

            this_level = self.start_hierarchy[level_index]

            if self.updated_start in this_level:
                if level_index == 0:  # i.e., updated_start == 0
                    self.start_duration_pairs.append(
                        (self.updated_start, round(self.remaining_length, 4))
                    )
                    return
                else:  # level up. NB: duplicates in nested hierarchy help here
                    if self.split_same_level:  # relevant option for e.g., 6/8
                        self.advance_step(this_level)
                    else:  # usually
                        self.advance_step(self.start_hierarchy[level_index - 1])

        if self.remaining_length > 0:  # start not in the hierarchy at all
            self.advance_step(self.start_hierarchy[-1])  # get to the lowest level
            # Now start the process with the metrical structure:
            self.level_pass()

    def advance_step(self, positions_list: list):
        """
        For a start position, and a metrical level expressed as a list of starts,
        find the next higher value from those levels.
        Used for determining iterative divisions.
        """
        for p in positions_list:
            if p > self.updated_start:
                duration_to_next_position = p - self.updated_start
                if self.remaining_length <= duration_to_next_position:
                    self.start_duration_pairs.append(
                        (self.updated_start, round(self.remaining_length, 4))
                    )
                    # done but still reduce remaining_length to end the whole process in level_pass
                    self.remaining_length -= duration_to_next_position
                    return
                else:  # self.remaining_length > duration_to_next_position:
                    self.start_duration_pairs.append(
                        (self.updated_start, round(duration_to_next_position, 4))
                    )
                    # Updated start and position; run again
                    self.updated_start = p
                    self.remaining_length -= duration_to_next_position
                    self.level_pass()  # NB: to re-start from top as may have jumped a level
                    return


# ------------------------------------------------------------------------------


def starts_from_ts(
    ts_str: str, enforce_2s_3s: bool = True, minimum_pulse: int = 64
) -> list:
    """
    Create a start hierarchy for almost any time signature
    directly from a string (e.g., "4/4") without dependencies.


    Parameters
    ----------
    ts_str
        Any valid string repersenting a time signature. See examples below.
    enforce_2s_3s
        Map 4 to 2+2 and 6 to 3+3 etc. following the conventions of those time signatures.
    minimum_pulse
        Recursively create further down to the denominator level specified. Defaults to 64 for 64th notes.

    Returns
    -------
    list
        Returns a list of lists with start positions by level.

    Examples
    --------
    The following examples index the most interesting level:

    >>> starts_from_ts("4/4")[1]  # note the half cycle division
    [0.0, 2.0, 4.0]

    >>> starts_from_ts("4/4", enforce_2s_3s=False)[1]  # note the absence of a half cycle division
    [0.0, 1.0, 2.0, 3.0, 4.0]

    >>> starts_from_ts("2/2")[1]  # note the presence of a half cycle division
    [0.0, 2.0, 4.0]

    >>> starts_from_ts("6/8")[1]  # note the macro-beat division
    [0.0, 1.5, 3.0]


    Numerators like 5 and 7 are supported.
    Use the total value only to avoid segmentation about the denominator level:

    >>> starts_from_ts("5/4")[1]  # note no 2+3 or 3+2 level division
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]

    Or use numerator addition in the form "X+Y/Z" to clarify this level ...

    >>> starts_from_ts("2+3/4")[1]  # note the 2+3 division
    [0.0, 2.0, 5.0]

    >>> starts_from_ts("2+2+3/8")[1]  # note the 2+2+3 division
    [0.0, 1.0, 2.0, 3.5]

    >>> starts_from_ts("2+2+2+3/8")[1]  # note the 2+2+2+3 division
    [0.0, 1.0, 2.0, 3.0, 4.5]

    Only standard denominators are supported:
    i.e., time signatures in the form X/ one of
    1, 2, 4, 8, 16, 32, or 64.
    No so-called "irrational" meters yet (e.g., 2/3), sorry!

    Likewise, the minimum_pulse must be set to one of these values
    (default = 64 for 64th note) and not be longer than the meter.

    Finally, although we support and provide defaults for time signatures in the form "2+3/8",
    there is no such support for more than one "/" (i.e., the user must build cases like "4/4 + 3/8" explicitly).
    """

    # Prep and checks
    numerator, denominator = ts_str.split("/")
    numerators = [
        int(x) for x in numerator.split("+")
    ]  # Note: support "+" before one "/", e.g., `2+3/4`
    denominator = int(denominator)

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
        ([6, 9], [[6, 9], [3, 3, 3, 3, 3]]),
        ([9, 6], [[6, 6], [3, 3, 3, 3, 3]]),
    )

    if enforce_2s_3s:
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
    ts_str: str,
    levels: Union[list, None] = None,
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

    Parameters
    ----------
    ts_str
        Any valid string repersenting a time signature. See examples below.
    levels
        Optionally specify which levels implied by the time signature to use.

    Returns
    -------
    list
        Returns a list of lists with start positions by level.

    Examples
    --------

    >>> starts_from_ts_and_levels("6/8", [1, 2])
    [[0.0, 3.0], [0.0, 1.5, 3.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]]

    >>> level_not_specified = starts_from_ts_and_levels("6/8")
    >>> len(level_not_specified)
    6

    >>> level_not_specified[3]
    [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]

    """
    if levels is None:
        levels = range(6)

    if max(levels) > 6:
        raise ValueError("6 is the maximum level depth supported.")
    levels = sorted(levels)  # smallest first
    if 0 not in levels:  # likely, and not a problem
        levels = [0] + levels  # Always have level 0 as first entry

    starts_by_level = []

    full_hierarchy = starts_from_ts(ts_str)
    for level in levels:
        starts_by_level.append(full_hierarchy[level])

    return starts_by_level


def starts_from_pulse_lengths(
    pulse_lengths: list,
    measure_length: Optional[float] = None,
    require_2_or_3_between_levels: bool = False,
):
    """
    Convert a list of pulse lengths into a corresponding list of lists
    with start positions per metrical level.
    All values (pulse lengths, start positions, and measure_length)
    are all expressed in terms of quarter length.

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


    Parameters
    ----------
    pulse_lengths
        Any valid list of pulse lengths, e.g., [4, 2, 1].
    measure_length
        Optional. If not provided it's taken to be given by the longest pulse length.
    require_2_or_3_between_levels
        Deafults to False. If True, raise a ValueError in the case of this condition not being met.

    Returns
    -------
    list
        Returns a list of lists with start positions by level.

    Examples
    --------

    >>> qsl = starts_from_pulse_lengths(pulse_lengths=[4, 2, 1, 0.5])

    >>> qsl[0]
    [0.0, 4.0]

    >>> qsl[1]
    [0.0, 2.0, 4.0]

    >>> qsl[2]
    [0.0, 1.0, 2.0, 3.0, 4.0]

    >>> qsl[3]
    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

    """

    pulse_lengths = sorted(pulse_lengths)[::-1]  # largest number first

    if not measure_length:
        measure_length = float(pulse_lengths[0])

    else:
        if pulse_lengths[0] > measure_length:
            raise ValueError(
                f"The `pulse_length` {pulse_lengths[0]} is longer than the `measure_length` ({measure_length})."
            )

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


def coincident_pulse_list(
    m: MetricalHierarchy,
    granular_pulse: float,
) -> list:
    """
    Create a flat list in the form [4, 1, 2, 1, 3, 1, 2, 1]
    from the number of intersecting pulses at each position.

    Parameters
    --------
    m
        A level hierarchy, in the form of a list of list,
        or a metrical hierarchy storing the same.
    granular_pulse
        The pulse value of the fastest level to consider e.g., 1, or 0.25.

    Examples
    --------

    >>> m = [[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]]
    >>> coincident_pulse_list(m, granular_pulse=1)
    [3, 1, 2, 1]

    You can currently set the `granular_pulse` value to anything (this behavious may change).
    For instance, a faster level that's not present simply pads the data out:

    >>> m = [[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]]
    >>> coincident_pulse_list(m, granular_pulse=0.5)
    [3, 0, 1, 0, 2, 0, 1, 0]

    """
    if isinstance(m, MetricalHierarchy):
        m = m.start_hierarchy
    elif not isinstance(m, list):
        raise ValueError("The X must be a `MetricalHierarchy` object or a list")

    measure_length = m[0][-1]

    for level in m:
        assert level[-1] == measure_length

    steps = int(measure_length / granular_pulse)
    granular_level = [granular_pulse * count for count in range(steps)]

    def count_instances(nested_list, target):
        return sum([sublist.count(target) for sublist in nested_list])

    coincidences = []
    for target in granular_level:
        coincidences.append(count_instances(m, target))

    return coincidences


# ------------------------------------------------------------------------------

# Subsidiary one-level converters


def starts_from_lengths(
    measure_length: float, pulse_length: float, include_measure_length: bool = True
):
    """
    Convert a pulse length and measure length into a list of starts.
    All expressed in quarter length.

    Note:
    A maximum of 4 decimal places is hardcoded.
    This is to avoid floating point errors or the need for one line of numpy (np.arange)
    in a module that doesn't otherwise use it.
    4dp should be sufficient for all realistic use cases.

    Parameters
    --------
    measure_length
        The quarter length of the metrical span overall.
    pulse_length
        The quarter length of the pulse (note: must be shorter than the `measure_length`).
    include_measure_length
        If True (default) then each level ends with the full cycle length
        (i.e., the start of the start of the next cycle).

    Examples
    --------

    >>> starts_from_lengths(4, 1)
    [0.0, 1.0, 2.0, 3.0, 4.0]

    >>> starts_from_lengths(4, 1, include_measure_length=False)
    [0.0, 1.0, 2.0, 3.0]
    """
    starts = []
    count = 0
    while count < measure_length:
        starts.append(round(float(count), 4))
        count += pulse_length

    if include_measure_length:
        starts.append(round(float(count), 4))

    return starts


def starts_from_beat_pattern(
    beat_list: list, denominator: float, include_measure_length: bool = True
):
    """
    Converts a list of beats
    like [2, 2, 2]
    or [3, 3]
    or indeed
    [6, 9]
    into a list of starts.

    Parameters
    --------
    beat_list
        An ordered list of the beat types.
    denominator
        The lower value of a time signature to set the pulse value.
    include_measure_length
        If True (default) then each level ends with the full cycle length
        (i.e., the start of the start of the next cycle).

    Examples
    --------

    >>> starts_from_beat_pattern([2, 2, 3], 4)
    [0.0, 2.0, 4.0, 7.0]

    >>> starts_from_beat_pattern([2, 2, 3], 4, include_measure_length = False)
    [0.0, 2.0, 4.0]

    """
    starts = [0.0]  # always float, always starts at zero
    count = 0
    for beat_val in beat_list:
        count += beat_val
        this_start = count * 4 / denominator
        starts.append(this_start)

    if include_measure_length:  # include last value
        return starts
    else:
        return starts[:-1]


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
