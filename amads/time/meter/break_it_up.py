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

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------


class MetricalSplitter:
    """
    Split up notes and/or rests to reflect a specified metrical hierarchy.

    This class
    takes in a representation of a note in terms of the start position and duration,
    along with a metrical context
    and returns a list of start-duration pairs for the constituent parts of the broken-up note.

    The metrical context should be expressed in the form of a `start_hierarchy`
    (a list of lists representing the hierarchy from the coarsest level to the finest).
    This can be provided directly or made via various classes in the meter module (see notes there).

    The basic premise here is that a single note can only traverse metrical boundaries
    for levels lower than the one it starts on.
    If it traverses the metrical boundary of a higher level, then
    it is split at that position into two note-heads.
    This split registers as a case of syncopation for those algorithms
    and as a case for two note-heads to be connected by a tie in notation.

    There are many variants on this basic setup.
    This class aims to support almost any such variant, while providing easy defaults
    for simple, standard practice.

    The flexibility comes from the definition of a metrical structure
    (for which see the `MetricalHierarchy` class).

    Each split of the note duration moves up one metrical level.
    The exact definition of metrical structure
    (including the presence and absence of each level) is central.
    Given a "4/4" that's defined by pulse levels 4, 2, 1, 0.5, 0.25
    (`PulseLengths([4, 2, 1, 0.5, 0.25], cycle_length=4)`),
    a note of duration 2.0 starting at
    0.25 connects to 0.5 in level 3 (duration = 0.25), then
    0.5 connects to 1.0 in level 2 (duration = 0.5), then
    1.0 connects to 2.0 in level 1 (duration = 1.0), and
    this leaves a duration of 0.25 to start on 2.0.
    The data is returned as a list of (position, duration) tuples.
    The values for the example would be:
    [(0.25, 0.25),
    (0.5, 0.5),
    (1.0, 1.0),
    (2.0, 0.25)]

    Alternatively, the metrical encoding of 4/4 might decline to specify
    the levels for pulse length 2 and any shorter than 1.
    This is true of default construction with `TimeSignature(as_string="4/4")`.
    Clearly this yields different splits.

    Both of these variants are demonstrated among the examples below.

    If the note runs past the end of the metrical span,
    the remaining value is stored with the
    `start_duration_pairs` recording the within-measure pairs
    and `remaining_length` attribute for the rest.

    If the `note_start` is not in the hierarchy,
    then the first step is to map to the next higher value in the lowest level.

    Parameters
    ----------
    note_start: float
        The starting position of the note (or rest).
    note_length: float
        The length (duration) of the note (or rest).
    start_hierarchy: list[list]
        Metrical hierarchy from the coarsest level to finest.
        Each level must be a superset of the one above it.
        Level 0 must be `[0.0, cycle_length]` .
    split_same_level: bool
        If True, split at boundary positions _within_ the level the note starts on,
        in addition to boundaries _between_ levels.
        Relevant for meters with 3-groupings such as 6/8:
        a quarter note starting on the second eighth note (position 0.5)
        can either be left intact or split on the third eighth (position 1.0)
        depending on this editorial convention.
        Defaults to `True`.

    See Also
    --------
    nested_to_start_hierarchy : Convert a variably-nested list of positions
        into a `start_hierarchy` suitable for this class.

    Examples
    --------

    >>> from amads.time.meter.representations import TimeSignature, PulseLengths
    >>> m = TimeSignature(as_string="4/4")
    >>> start_hierarchy = m.to_start_hierarchy()
    >>> start_hierarchy
    [[0.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]]

    This shows that the `TimeSignature(as_string="4/4")`
    specifies the /1 and /4 levels only (skipping the /2 level and any shorter than the /4).

    Here, in the absence of the /2 level, the `split_same_level` option makes a difference.

    >>> split = MetricalSplitter(0.25, 2.0, start_hierarchy=start_hierarchy, split_same_level=False)
    >>> split.start_duration_pairs
    [(0.25, 0.75), (1.0, 1.25)]

    >>> split = MetricalSplitter(0.25, 2.0, start_hierarchy=start_hierarchy, split_same_level=True)
    >>> split.start_duration_pairs
    [(0.25, 0.75), (1.0, 1.0), (2.0, 0.25)]

    >>> m.fill_2s_3s()
    >>> start_hierarchy = m.to_start_hierarchy()
    >>> start_hierarchy
    [[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]]

    Now we have the /2 level, the `split_same_level` option makes no difference.

    >>> split = MetricalSplitter(0.25, 2.0, start_hierarchy=start_hierarchy, split_same_level=True)
    >>> split.start_duration_pairs
    [(0.25, 0.75), (1.0, 1.0), (2.0, 0.25)]

    >>> split = MetricalSplitter(0.25, 2.0, start_hierarchy=start_hierarchy, split_same_level=False)
    >>> split.start_duration_pairs
    [(0.25, 0.75), (1.0, 1.0), (2.0, 0.25)]

    Creating directly from PulseLengths is clearer in this case:

    >>> meter_from_pulses = PulseLengths([4, 2, 1, 0.5, 0.25], cycle_length=4)
    >>> start_hierarchy = meter_from_pulses.to_start_hierarchy()
    >>> start_hierarchy[-1]
    [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0]

    >>> split = MetricalSplitter(0.25, 2.0, start_hierarchy=start_hierarchy)
    >>> split.start_duration_pairs
    [(0.25, 0.25), (0.5, 0.5), (1.0, 1.0), (2.0, 0.25)]

    Now with a note that extends beyond the end of the cycle:

    >>> split = MetricalSplitter(0.25, 4.0, start_hierarchy=start_hierarchy)
    >>> split.start_duration_pairs
    [(0.25, 0.25), (0.5, 0.5), (1.0, 1.0), (2.0, 2.0)]

    >>> split.remaining_length
    0.25

    Now with a note that starts at a position not in the hierarchy:

    >>> split = MetricalSplitter(0.05, 2.0, start_hierarchy=start_hierarchy)
    >>> split.start_duration_pairs
    [(0.05, 0.2), (0.25, 0.25), (0.5, 0.5), (1.0, 1.0), (2.0, 0.05)]

    """

    def __init__(
        self,
        note_start: float,
        note_length: float,
        start_hierarchy: list[list],
        split_same_level: bool = True,
    ):

        self.note_length = note_length
        self.note_start = note_start
        self.start_hierarchy = start_hierarchy
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
        this method iterates across the levels of that hierarchy to find the
        current start position, and (through `advance_step`) the start
        position to map to.

        This method runs once for each such mapping, typically advancing
        up one (or more) layer of the metrical hierarchy with each call.
        “Typically” because `split_same_level` is supported where relevant.

        Each iteration creates a new start-duration pair
        stored in the `start_duration_pairs` list
        that records the constituent parts of the split note.

        The method includes a check for when the `remaining_length` goes negative,
        as a signal to terminate.
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
            self.advance_step(
                self.start_hierarchy[-1]
            )  # get to the lowest level
            # Now start the process with the metrical structure:
            self.level_pass()

    def advance_step(self, positions_list: list):
        """
        For a start position, and a metrical level expressed as a list of starts,
        find the next higher value from those levels.
        Used for determining iterative divisions.

        While it is not necessarily clear at first glance,
        there is in fact a termination guarantee for this method:
        `remaining_length` strictly decreases on every call to this method.
        The decrease is by the value of the `duration_to_next_position` in the split case,
        and to zero (or below) otherwise.
        This guarantees that the mutual recursion
        between `advance_step` and `level_pass` always terminates.

        Parameters
        ----------
        positions_list : list
            An ordered list of metrical positions at a single hierarchy level.
        """
        for p in positions_list:
            if p > self.updated_start:
                duration_to_next_position = p - self.updated_start
                if self.remaining_length <= duration_to_next_position:
                    self.start_duration_pairs.append(
                        (self.updated_start, round(self.remaining_length, 4))
                    )
                    # done but still reduce `remaining_length` to end the whole process in level_pass
                    self.remaining_length -= duration_to_next_position
                    return
                else:  # self.remaining_length > duration_to_next_position:
                    self.start_duration_pairs.append(
                        (
                            self.updated_start,
                            round(duration_to_next_position, 4),
                        )
                    )
                    # Updated start and position; run again
                    self.updated_start = p
                    self.remaining_length -= duration_to_next_position
                    self.level_pass()  # NB: to re-start from top as may have jumped a level
                    return


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
