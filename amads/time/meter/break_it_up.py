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

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------


class MetricalSplitter:
    """
    Split up notes and rest to reflect a specified metrical hierarchies.

    This class
    takes in a representation of a note in terms of the start position and duration,
    along with a metrical context
    and returns a list of start-duration pairs for the broken-up note value.

    The metrical context should be expressed in the form of a `start_hierarchy`
    (effectively a list of lists for the hierarchy).
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
    as demonstrated below.

    If the note runs past the end of the metrical span,
    the remaining value is stored with the
    `start_duration_pairs` recording the within-measure pairs
    and `remaining_length` attribute for the rest.

    If the `note_start` is not in the hierarchy,
    then the fist step is to map to the next nearest value in the lowest level.

    Parameters
    -------
    note_start: float
        The starting position of the note (or rest).

    note_length: float,
        The length (duration) of the note (or rest).

    split_same_level: bool
        When creating hierarchies, decide whether to split elements at the same level, e.g., 1/8 and 2/8 in 6/8.
        In cases of metrical structures with a 3-grouping
        (two "weak" events between a "strong" in compound signatures like 6/8),
        some conventions chose to split notes within-level as well as between them.
        For instance, with a quarter note starting on the second eighth note (start 0.5) of 6/8,
        some will want to split that into two 1/8th notes, divided on the third eighth note position,
        while others will want to leave this intact.
        The `split_same_level` option accommodates this:
        it affects the within-level split when set to True and not otherwise (default).

    Examples
    -------

    >>> from amads.time.meter import TimeSignature, PulseLengths
    >>> m = TimeSignature(as_string="4/4")
    >>> start_hierarchy = m.to_start_hierarchy()
    >>> start_hierarchy
    [[0.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]]

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

    >>> meter_from_pulses = PulseLengths([4, 2, 1, 0.5, 0.25], cycle_length=4)
    >>> start_hierarchy = meter_from_pulses.to_start_hierarchy()
    >>> start_hierarchy[-1]
    [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0]

    >>> split = MetricalSplitter(0.25, 4.0, start_hierarchy=start_hierarchy)
    >>> split.start_duration_pairs
    [(0.25, 0.25), (0.5, 0.5), (1.0, 1.0), (2.0, 2.0)]

    >>> split.remaining_length
    0.25

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
                    # done but still reduce `remaining_length` to end the whole process in level_pass
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


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
