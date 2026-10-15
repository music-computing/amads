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
    for levels finer than the one it starts on.
    If it traverses the metrical boundary of a coarser level, then
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
    then the first step is to map to the "next" (larger) value in the finest level specified.

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

        # Pre-compute rounded sets for float-safe membership tests
        self._level_sets = [
            {round(p, 4) for p in level} for level in start_hierarchy
        ]

        # Initialise
        self.start_duration_pairs = []
        self.remaining_length = note_length
        self._run()

    def _run(self):
        current = self.note_start
        remaining = self.note_length

        while remaining > 0:
            if current >= self.start_hierarchy[0][-1]:
                self.remaining_length = remaining
                return

            # Find which level current belongs to
            target_level = None
            for level_index, level_set in enumerate(self._level_sets):
                if round(current, 4) in level_set:
                    if level_index == 0:
                        # On the coarsest level: emit the rest of the note in one piece
                        self.start_duration_pairs.append(
                            (current, round(remaining, 4))
                        )
                        self.remaining_length = 0
                        return
                    # split_same_level=True  → advance to the next boundary in the
                    # current level (i.e. split within the same metrical level).
                    # split_same_level=False → advance only to the next boundary in
                    # the coarser level above (i.e. never split within a level).
                    target_level = (
                        self.start_hierarchy[level_index]
                        if self.split_same_level
                        else self.start_hierarchy[level_index - 1]
                    )
                    break

            if target_level is None:
                # current is not on any level: advance to the next position in the
                # finest level so the note snaps onto the grid.
                target_level = self.start_hierarchy[-1]

            current, remaining = self._advance_step(
                current, remaining, target_level
            )

        self.remaining_length = remaining

    def _advance_step(
        self, current: float, remaining: float, positions_list: list
    ) -> tuple:
        """
        Find the next position after `current` in `positions_list`,
        emit a start-duration pair, and return the updated (current, remaining).
        """
        for p in positions_list:
            if p > current:
                duration_to_next = p - current
                if remaining <= duration_to_next:
                    self.start_duration_pairs.append(
                        (current, round(remaining, 4))
                    )
                    return (
                        current,
                        remaining - duration_to_next,
                    )  # drives remaining <= 0
                else:
                    self.start_duration_pairs.append(
                        (current, round(duration_to_next, 4))
                    )
                    return p, remaining - duration_to_next
        raise ValueError(
            f"No next position found from {current!r} "
            f"in {positions_list!r} — possible float drift past boundary."
        )


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
