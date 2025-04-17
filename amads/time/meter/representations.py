"""
This module serves to map out metrical hierarchies in a number of different ways and
to express the relationship between
the notes in
and
the hierarchy of
a metrical cycle.

Uses include identifying notes that traverse metrical levels,
for analysis (e.g., as a cycle of syncopation)
and notation (e.g., re-notating to reflect the
within-cycle notational conventions).
"""

__author__ = "Mark Gotham"

import math
from typing import Optional, Union

import numpy as np

# ------------------------------------------------------------------------------


def is_non_negative_integer_power_of_two(n: float) -> bool:
    """
    Checks if a number is a power of 2.

    >>> is_non_negative_integer_power_of_two(0)
    False

    >>> is_non_negative_integer_power_of_two(0.5)
    False

    >>> is_non_negative_integer_power_of_two(1)
    True

    >>> is_non_negative_integer_power_of_two(2)
    True

    >>> is_non_negative_integer_power_of_two(3)
    False

    >>> is_non_negative_integer_power_of_two(4)
    True
    """
    if n <= 0:  # also catches type error if non-numeric
        return False
    if not isinstance(n, int):
        if int(n) == n:
            n = int(n)
        else:
            return False
    return n > 0 and (n & (n - 1)) == 0


def switch_pulse_length_beat_type(pulse_length_or_beat_type: Union[float, np.array]):
    """
    Switch between a pulse length and beat type.
    Accepts numeric values or numpy arrays thereof.
    Note that a float of vale 0 will raise a `ZeroDivisionError: division by zero`,
    but a numpy array will map any 0s to `inf` without error.

    >>> switch_pulse_length_beat_type(0.5)
    8.0

    >>> switch_pulse_length_beat_type(8)
    0.5

    >>> switch_pulse_length_beat_type(np.array([0.5, 8]))
    array([8. , 0.5])
    """
    return 4 / pulse_length_or_beat_type


class StartTimeHierarchy:
    """
    Encoding metrical structure as a hierarchy of start times:
    a representation of metrical levels in terms of starts expressed by quarter length
    from the start of the cycle.

    Parameters
    ----------
    start_hierarchy
        Users can specify the `start_hierarchy` directly and completely from scratch.
        Use this for advanced, non-standard metrical structures
        including those without 2-/3- grouping, or even nested hierarchies,
        as well as for (optionally) encoding micro-timing directly into the metrical structure.
        The only "well-formed" criteria we expect are
        use of 0.0 and full cycle length at the top level, and
        presence of all timepoints from one level in each subsequent level.
        For creating this information from pulse lengths, time signatures, and more
        see the `to_start_hierarchy` methods on those classes.
    names
        Optionally create a dict mapping temporal positions to names.
        Currently, this supports one textual value per temporal position (key),
        e.g., {0.0: "ta", 1.0: "ka", 2.0: "di", 3.0: "mi"}.

    """

    def __init__(
        self,
        start_hierarchy: list[list],
        names: Optional[dict] = None,
    ):
        self.start_hierarchy = start_hierarchy
        self.cycle_length = self.start_hierarchy[0][-1]
        self.pulse_lengths = None

        if names:
            for key in names:
                assert isinstance(key, float)
                assert isinstance(names[key], str)
        self.names = names

    def coincident_pulse_list(
        self,
        granular_pulse: float,
    ) -> list:
        """
        Create a flat list setting out the
        number of intersecting pulses at each successive position in a metrical cycle.

        For example,
        the output [4, 1, 2, 1, 3, 1, 2, 1]
        refers to a base pulse unit of 1,
        with addition pulse streams accenting every 2nd, 4th, and 8th position.


        Parameters
        --------
        granular_pulse
            The pulse value of the fastest level to consider e.g., 1, or 0.25.

        Examples
        --------

        You can currently set the `granular_pulse` value to anything (this may change).
        For instance, in the pair of examples below,
        first we have a `granular_pulse` that's present in the input,
        and then a case using a faster level that's not present (this simply pads the data out):

        >>> hierarchy = StartTimeHierarchy([[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]])
        >>> hierarchy.coincident_pulse_list(granular_pulse=1)
        [3, 1, 2, 1]

        Now, changing the `granular_pulse` for a bit of over-sampling:

        >>> hierarchy.coincident_pulse_list(granular_pulse=0.5)
        [3, 0, 1, 0, 2, 0, 1, 0]

        """
        cycle_length = self.start_hierarchy[0][-1]

        for level in self.start_hierarchy:
            assert level[-1] == cycle_length

        steps = int(cycle_length / granular_pulse)
        granular_level = [granular_pulse * count for count in range(steps)]

        def count_instances(nested_list, target):
            return sum([sublist.count(target) for sublist in nested_list])

        coincidences = []
        for target in granular_level:
            coincidences.append(count_instances(self.start_hierarchy, target))

        return coincidences

    def to_pulse_lengths(self):
        """
        Check if levels have a regular pulse and if so, return the pulse length value.

        Returns
        -------
        list
            Returns a list of pulse values corresponding to the start hierarchy, of the same length.
            If a level is not regular, the list is populated with None.

        Examples
        --------

        >>> hierarchy = StartTimeHierarchy([[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]])
        >>> hierarchy.to_pulse_lengths()
        >>> hierarchy.pulse_lengths
        [4.0, 2.0, 1.0]

        >>> uneven = StartTimeHierarchy([[0.0, 4.0], [0.0, 3.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]])
        >>> uneven.to_pulse_lengths()
        >>> uneven.pulse_lengths
        [4.0, None, 1.0]

        """

        def test_one(level: list):
            diffs = set([level[i + 1] - level[i] for i in range(len(level) - 1)])
            if len(diffs) > 1:
                return None
            return float(list(diffs)[0])

        self.pulse_lengths = [test_one(level) for level in self.start_hierarchy]

    def add_faster_levels(self, minimum_beat_type: int = 64):
        """
        Recursively add faster levels until the `minimum_beat_type` value
        The `minimum_beat_type` is subject to the same constraints as the `beat_types` ("denominators")
        i.e., powers of 2 (1, 2, 4, 8, 16, 32, 64, ...).
        The default = 64 for 64th note.

        Parameters
        ----------
        minimum_beat_type
            Recursively create further levels down to this value.
            Must be power of two.
            Defaults to 64 for 64th notes.

        Raises
        ------
        Errors raised if the currently fastest level of a `starts_hierarchy` is not periodic,
        or if either of the fastest level or `minimum_beat_type` are not powers of 2.
        Set the `starts_hierarchy` manually in these non-standard cases.

        Examples
        --------
        >>> hierarchy = StartTimeHierarchy([[0.0, 4.0], [0.0, 2.0, 4.0]])
        >>> hierarchy.start_hierarchy
        [[0.0, 4.0], [0.0, 2.0, 4.0]]

        >>> hierarchy.to_pulse_lengths()
        >>> hierarchy.pulse_lengths
        [4.0, 2.0]

        >>> hierarchy.add_faster_levels(minimum_beat_type=4)
        >>> hierarchy.start_hierarchy
        [[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]]

        >>> hierarchy.pulse_lengths
        [4.0, 2.0, 1.0]

        >>> hierarchy.add_faster_levels(minimum_beat_type=8)
        >>> hierarchy.start_hierarchy[-1]
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

        >>> len(hierarchy.start_hierarchy)
        4

        >>> hierarchy.pulse_lengths
        [4.0, 2.0, 1.0, 0.5]

        """
        self.to_pulse_lengths()
        fastest = self.pulse_lengths[-1]
        if fastest is None:
            raise ValueError("Fastest level is not regular. Use case unsupported.")
        if not is_non_negative_integer_power_of_two(
            switch_pulse_length_beat_type(fastest)  # from pulse length to beat type
        ):
            raise ValueError(
                f"Fastest level ({fastest}) is not a power of 2. Use case unsupported."
            )
        if not is_non_negative_integer_power_of_two(minimum_beat_type):
            raise ValueError(
                f"The `minimum_beat_type` ({minimum_beat_type}) is not a power of 2. Use case unsupported."
            )

        fastest_beat_type = switch_pulse_length_beat_type(fastest)  # TODO
        fastest_beat_type_exponent = int(math.log2(fastest_beat_type))
        minimum_beat_type_exponent = int(math.log2(minimum_beat_type))

        new_beat_types = [
            2**x
            for x in range(
                fastest_beat_type_exponent + 1, minimum_beat_type_exponent + 1
            )
        ]
        new_pulses = [
            switch_pulse_length_beat_type(beat_type) for beat_type in new_beat_types
        ]
        self.pulse_lengths += new_pulses
        self.pulse_lengths = [x for x in self.pulse_lengths if x is not None]
        self.pulse_lengths = sorted(
            list(set(self.pulse_lengths)), key=abs, reverse=True
        )
        fake_meter = PulseLengths(
            pulse_lengths=new_pulses, cycle_length=self.cycle_length
        )
        self.start_hierarchy += fake_meter.to_start_hierarchy()


# ------------------------------------------------------------------------------


class TimeSignature:
    """
    Represent the _notational_ time signature object.
    # TODO consider aligning and merging with basics.TimeSignature, this PR shows some of how that would work.

    Parameters
    ----------
    beats
        The "numerator" of the time signature: beats per cycle, a number (int or fraction) or a lists thereof.
    beat_type
        the so-called "denominator" of the time signature: a whole number power of 2
        (1, 2, 4, 8, 16, 32, 64, ...).
        No so-called "irrational" meters yet (e.g., 2/3), sorry!
    as_string
        An alternative way of creating this object from a string representation.
        See notes at `TimeSignature.from_string`.

    """

    def __init__(
        self,
        beats: Optional[Union[tuple[int]]] = None,
        beat_type: Optional[int] = None,
        # delta: Optional[float] = 0,  # TODO if merging with basics
        as_string: Optional[str] = None,
    ):
        self.beats = beats
        self.one_beat_value = None
        self.beat_type = beat_type
        self.as_string = as_string
        if (self.beats is None) and (self.beat_type is None):
            self.from_string()
        self.check_valid()

        self.cycle_length = sum(self.beats) * 4 / self.beat_type
        self.pulses = None
        self.get_pulses()

    def from_string(self):
        """
        Given a signature string, extract the constituent parts and create an object.
        The string must take the form `<beat>/<beat_type>`
        with exactly one "/" separating the two (spaces are ignored).
        The string does not change.

        The `<beat>` ("numerator") part may be a number (including 5 and 7 which are supported)
        or more than one number separated by the "+" symbol.
        For example, when encoding "5/4",
        use the total value only to avoid segmentation above the denominator level ("5/4")
        or the X+Y form to explicitly distinguish between "2+3" and "3+2".
        I.e., "5/" time signatures have no 3+2 or 2+3 division by default.
        See examples on `TimeSignature.to_starts_hierarchy`.

        Finally, although we support and provide defaults for time signatures in the form "2+3/8",
        there is no such support for more than one "/"
        (i.e., the user must build cases like "4/4 + 3/8" explicitly according to how they see it).


        Examples
        --------

        >>> ts_4_4 = TimeSignature(as_string="4/4")
        >>> ts_4_4.beats # Tuple of one element
        (4,)

        >>> ts_4_4.beat_type
        4

        """
        beats, beat_type = self.as_string.split("/")

        self.beats = tuple([int(x) for x in beats.split("+")])
        self.beat_type = int(beat_type)

    def check_valid(self):
        """
        Check the validity of the input:
        .beats must be an integer or a list / tuple thereof.
        .beat_type must be a single integer power of two.
        """
        # beats  # TODO this check may be overdoing it
        if self.beats:
            assert isinstance(self.beats, tuple)
            for b in self.beats:
                assert isinstance(b, int)

        # beat_type  # TODO this is the part we want to actively check
        if not is_non_negative_integer_power_of_two(self.beat_type):
            raise ValueError(
                f"Beat type set as {self.beat_type} is invalid: must be a non-negative integer power of 2."
            )

    def get_pulses(self):
        """
        Create an unordered set for the regular pulses present in this time signature.
        This will include the full cycle and beat type ("denominator") value,
        e.g., in "3/4" the pulse lengths are 3.0 (full cycle) and 1.0 (beat type).
        If there are other regular levels between the two, they will be added
        only if the user has first called `fill_2s_3s` (it does not run by default).
        For instance, the splitting of 4 into 2+2 is user choice (see `fill_2s_3s`)
        With this split, this "4/4" has pulse lengths of 4.0 (full cycle)
        and 1.0 (beat type) as well as 2.0 given that the two twos are of one kind.
        In "2+3/4" there is no such 2.0 (or 3.0) regularity, and so no pulse is created for that level.

        Examples
        --------
        >>> ts_4_4 = TimeSignature(as_string="4/4")
        >>> ts_4_4.pulses
        [4.0, 1.0]

        >>> ts_4_4.fill_2s_3s()
        >>> ts_4_4.pulses
        [4.0, 2.0, 1.0]

        >>> ts_6_8 = TimeSignature(as_string="6/8")
        >>> ts_6_8.pulses
        [3.0, 0.5]

        >>> ts_6_8.fill_2s_3s()
        >>> ts_6_8.pulses
        [3.0, 1.5, 0.5]

        """
        pulses = [float(self.cycle_length), 4 / self.beat_type]

        first_beat_to_pulse = self.beats[0] * 4 / self.beat_type

        if len(self.beats) == 1:  # one beat type
            pulses.append(first_beat_to_pulse)
            self.one_beat_value = self.beats[0]
        elif len(self.beats) > 1:  # 2+ beats
            if (
                len(set(self.beats)) == 1
            ):  # duplicate of the same e.g., (2, 2), so still one consistent pulse.
                self.one_beat_value = self.beats[0]
                pulses.append(first_beat_to_pulse)

        self.pulses = sorted(list(set(pulses)), key=abs, reverse=True)

    def fill_2s_3s(self):
        """
        Optionally, add pulse values to follow the conventions of the time signatures,
        enforcing 2- and 3-grouping.
        This only applies to cases with a single beat in the "numerator".
        For instance,
        given a "4/4" signature, this method will add the half-cycle (pulse value 2.0),
        given a "6/8", it will again add the half-cycle (pulse value 1.5),
        and given a "12/8", it will add both the half- and quarter-cycle (pulse values 3.0 and 1.5),

        This functionality is factored out and does not run by default.
        Even if this runs, the original time signature string is unchanged,
        as is the `beats` attribute.

        Examples
        --------
        >>> ts_4_4 = TimeSignature(as_string="4/4")
        >>> ts_4_4.pulses
        [4.0, 1.0]

        >>> ts_4_4.fill_2s_3s()
        >>> ts_4_4.pulses
        [4.0, 2.0, 1.0]

        >>> ts_6_8 = TimeSignature(as_string="6/8")
        >>> ts_6_8.pulses
        [3.0, 0.5]

        >>> ts_6_8.fill_2s_3s()
        >>> ts_6_8.pulses
        [3.0, 1.5, 0.5]

        """
        metrical_mappings = {4: [2], 6: [3], 9: [3], 12: [6, 3]}

        if self.one_beat_value is not None:
            if self.one_beat_value in metrical_mappings:
                self.pulses += [
                    x * 4 / self.beat_type
                    for x in metrical_mappings[self.one_beat_value]
                ]
        self.pulses = sorted(list(set(self.pulses)), key=abs, reverse=True)

    def to_start_hierarchy(self) -> list:
        """
        Create a start hierarchy for almost any time signature
        (with constraints as noted in the top level class description and in the `.from_string` method).
        See below for several examples of how this handles
        specific time signatures and related assumptions,
        and note the effect of running `fill_2s_3s()`.

        Returns
        -------
        list
            Returns a list of lists with start positions by level.

        Examples
        --------

        >>> ts_4_4 = TimeSignature(as_string="4/4")
        >>> ts_4_4.pulses
        [4.0, 1.0]

        >>> test_1 = ts_4_4.to_start_hierarchy()
        >>> test_1[0]
        [0.0, 4.0]

        >>> test_1[1]
        [0.0, 1.0, 2.0, 3.0, 4.0]

        >>> ts_4_4.fill_2s_3s()
        >>> ts_4_4.pulses
        [4.0, 2.0, 1.0]

        >>> test_2 = ts_4_4.to_start_hierarchy()
        >>> test_2[0]
        [0.0, 4.0]

        >>> test_2[1]
        [0.0, 2.0, 4.0]

        >>> test_2[2]
        [0.0, 1.0, 2.0, 3.0, 4.0]

        >>> ts_2_2 = TimeSignature(as_string="2/2")
        >>> ts_2_2.pulses
        [4.0, 2.0]

        >>> test_3 = ts_2_2.to_start_hierarchy()
        >>> test_3[0]
        [0.0, 4.0]

        >>> test_3[1]
        [0.0, 2.0, 4.0]

        >>> ts_2_2.fill_2s_3s() # no effect, unchanged
        >>> ts_2_2.pulses
        [4.0, 2.0]

        >>> test_4 = ts_2_2.to_start_hierarchy()
        >>> test_4[0]
        [0.0, 4.0]

        >>> test_4[1]
        [0.0, 2.0, 4.0]

        >>> ts_6_8 = TimeSignature(as_string="6/8")
        >>> ts_6_8.pulses
        [3.0, 0.5]

        >>> test_5 = ts_6_8.to_start_hierarchy()
        >>> test_5[0]
        [0.0, 3.0]

        >>> test_5[1]
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

        >>> ts_6_8.fill_2s_3s()
        >>> ts_6_8.pulses
        [3.0, 1.5, 0.5]

        >>> test_6 = ts_6_8.to_start_hierarchy()
        >>> test_6[0]
        [0.0, 3.0]

        >>> test_6[1]
        [0.0, 1.5, 3.0]

        >>> test_6[2]
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

        >>> ts_5_4 = TimeSignature(as_string="5/4")
        >>> ts_5_4.pulses
        [5.0, 1.0]

        >>> test_7 = ts_5_4.to_start_hierarchy()
        >>> test_7[0]
        [0.0, 5.0]

        >>> test_7[1]
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]

        >>> ts_2_3_4 = TimeSignature(as_string="2+3/4")
        >>> ts_2_3_4.pulses # as before
        [5.0, 1.0]

        >>> test_8 = ts_2_3_4.to_start_hierarchy()
        >>> test_8[0]
        [0.0, 5.0]

        >>> test_8[1]
        [0.0, 2.0, 5.0]

        >>> test_8[2]
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]

        """
        # 1. Basic elements: all periodic cycles from the full cycle to the `beat_type` level.
        pulses = PulseLengths(  # TODO consistency wrt what is added to the class.
            pulse_lengths=self.pulses, cycle_length=self.cycle_length
        )
        start_hierarchy = pulses.to_start_hierarchy()

        # 2. irregular beat layer, if applicable.
        if len(self.beats) > 1:  # not a regular pulse e.g., (2, 3)
            bp = BeatPattern(
                self.beats, self.beat_type
            )  # TODO consistency wrt what is added to the class.
            beat_starts = bp.beat_pattern_to_start_hierarchy()
            start_hierarchy.append(beat_starts)

            start_hierarchy = [list(i) for i in set(map(tuple, start_hierarchy))]
            start_hierarchy.sort(key=len)
            # TODO consider move to StartTimeHierarchy?

        return start_hierarchy


# ------------------------------------------------------------------------------


class PulseLengths:
    def __init__(
        self,
        pulse_lengths: list[float],
        cycle_length: Optional[float] = None,
        include_cycle_length: bool = True,
    ):
        """
        Representation of fully periodic meter centred on the constituent pulse lengths.

        Parameters
        ----------
        pulse_lengths
            Any valid list of pulse lengths, e.g., [4, 2, 1].
        cycle_length
            Optional. If not provided, the cycle length is taken to be given by the longest pulse length.
        include_cycle_length
            Defaults to True. If True, when converting to starts, include the full cycle length in the list.

        """

        self.pulse_lengths = pulse_lengths
        self.pulse_lengths.sort(reverse=True)  # largest number first

        self.cycle_length = cycle_length
        if self.cycle_length is not None:
            if pulse_lengths[0] > self.cycle_length:
                raise ValueError(
                    f"The `pulse_length` {pulse_lengths[0]} is longer than the `cycle_length` ({self.cycle_length})."
                )
        else:
            self.cycle_length = float(pulse_lengths[0])

        self.start_hierarchy = None
        self.include_cycle_length = include_cycle_length

    def to_start_hierarchy(
        self,
        require_2_or_3_between_levels: bool = False,
    ):
        """
        Convert a list of pulse lengths into a corresponding list of lists
        with start positions per metrical level.
        All values (pulse lengths, start positions, and cycle_length)
        are all expressed in terms of quarter length.

        That is, the user provides pulse lengths for each level of a metrical hierarchy,
        and the algorithm expands this into a hierarchy assuming equal spacing (aka "isochrony").

        This does not work for ("nonisochronous") pulse streams of varying duration
        in time signatures like 5/x, 7/x
        (e.g., the level of 5/4 with dotted/undotted 1/2 notes).

        It is still perfectly fine to use this for the pulse streams
        within those meters that are regular, equally spaced ("isochronous")
        (e.g., the 1/4 note level of 5/4).

        The list of pulse lengths is handled internally in decreasing order, whatever the ordering in the argument.

        If `require_2_or_3_between_levels` is True (default), this functions checks that
        each level is either a 2 or 3 multiple of the next.

        By default, the cycle_length is taken by the longest pulse length.
        Alternatively, this can be user-defined to anything as long as it is
        1) longer than the longest pulse and
        2) if `require_2_or_3_between_levels` is True then exactly 2x or 3x longer.


        Parameters
        ----------
        require_2_or_3_between_levels
            Defaults to False.
            If True, raise a ValueError in the case of this condition not being met.

        Returns
        -------
        list
            Returns a list of lists with start positions by level.

        Examples
        --------

        >>> qsl = PulseLengths(pulse_lengths=[4, 2, 1, 0.5])
        >>> qsl.pulse_lengths
        [4, 2, 1, 0.5]

        >>> start_hierarchy = qsl.to_start_hierarchy()
        >>> start_hierarchy[0]
        [0.0, 4.0]

        >>> start_hierarchy[1]
        [0.0, 2.0, 4.0]

        >>> start_hierarchy[2]
        [0.0, 1.0, 2.0, 3.0, 4.0]

        >>> start_hierarchy[3]
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

        """

        if require_2_or_3_between_levels:  # TODO consider refactor
            for level in range(len(self.pulse_lengths) - 1):
                if self.pulse_lengths[level] / self.pulse_lengths[level + 1] not in [
                    2,
                    3,
                ]:
                    raise ValueError(
                        "The proportion between consecutive levels is not 2 or 3 in "
                        f"this case: {self.pulse_lengths[level]}:{self.pulse_lengths[level + 1]}."
                    )

        start_list = []

        for pulse_length in self.pulse_lengths:
            starts = self.one_pulse_to_start_hierarchy_list(pulse_length)
            start_list.append(starts)

        self.start_hierarchy = start_list
        return start_list

    def one_pulse_to_start_hierarchy_list(
        self,
        pulse_length: float,
    ):
        """
        Convert a single pulse length and cycle length into a list of starts.
        All expressed in quarter length.

        Note:
        A maximum of 4 decimal places is hardcoded.
        This is to avoid floating point errors or the need for one line of numpy (np.arange)
        in a module that doesn't otherwise use it.
        4d.p. should be sufficient for all realistic use cases.

        Parameters
        --------
        pulse_length
            The quarter length of the pulse (note: must be shorter than the `cycle_length`).

        Examples
        --------

        >>> pls = PulseLengths(pulse_lengths=[4, 2, 1, 0.5], cycle_length=4)
        >>> pls.pulse_lengths
        [4, 2, 1, 0.5]

        >>> pls.one_pulse_to_start_hierarchy_list(1)
        [0.0, 1.0, 2.0, 3.0, 4.0]

        >>> pls = PulseLengths(pulse_lengths=[4, 2, 1, 0.5], cycle_length=4, include_cycle_length=False)
        >>> pls.one_pulse_to_start_hierarchy_list(1)
        [0.0, 1.0, 2.0, 3.0]

        """
        starts = []
        count = 0
        while count < self.cycle_length:
            starts.append(round(float(count), 4))
            count += pulse_length

        if self.include_cycle_length:
            starts.append(round(float(count), 4))

        return starts

    def to_array(self):
        """
        Create an array with the levels as rows,
        and the entries as pulse length values,
        where those pulse lengths start, and 0 otherwise.

        Examples
        --------

        >>> pls = PulseLengths(pulse_lengths=[4, 2, 1, 0.5], cycle_length=4)
        >>> pls.to_array()
        array([[4. , 0. , 0. , 0. , 0. , 0. , 0. , 0. ],
               [2. , 0. , 0. , 0. , 2. , 0. , 0. , 0. ],
               [1. , 0. , 1. , 0. , 1. , 0. , 1. , 0. ],
               [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]])

        """
        tatum = self.pulse_lengths[-1]
        linear_positions = int(self.cycle_length / tatum)
        granular_row = np.full(
            shape=(1, linear_positions), fill_value=tatum, dtype=np.float64
        )
        symbolic_pulse_length_array = np.array(granular_row)
        for pulse in self.pulse_lengths[-2::-1]:  # TODO check len?
            multiple_of_tatum = int(pulse / tatum)
            divider_of_cycle = int(linear_positions / multiple_of_tatum)
            proto_row = np.zeros((1, multiple_of_tatum))
            proto_row[0, 0] = pulse
            row = proto_row
            for i in range(divider_of_cycle - 1):
                row = np.append(row, proto_row)
            symbolic_pulse_length_array = np.vstack((row, symbolic_pulse_length_array))

        return symbolic_pulse_length_array


class BeatPattern:
    """
    Encoding only the part of a metrical structure identified as the beat pattern.

    Parameters
    --------
    beat_list
        An ordered list of the beat types.
    beat_type
        The lower value of a time signature to set the pulse value.
    """

    def __init__(
        self,
        beat_list: tuple[int, ...],
        beat_type: int,
    ):

        self.beat_list = beat_list
        self.beat_type = beat_type
        self.start_time_hierarchy = self.beat_pattern_to_start_hierarchy()

    def beat_pattern_to_start_hierarchy(
        self, include_cycle_length: bool = True
    ) -> list:
        """
        Converts a list of beats
        like [2, 2, 2]
        or [3, 3]
        or indeed
        [6, 9]
        into a list of within-cycle starting positions, as defined relative
        to the start of the cycle.
        Basically, the list of beats functions like the time signature's so-called "numerator",
        so for instance, `[2, 2, 3]` with the denominator `4` is a kind of 7/4.
        This equates to starting positions of
        `[0.0, 2.0, 4.0, 7.0]`.

        Parameters
        --------
        include_cycle_length
            If True (default) then each level ends with the full cycle length
            (i.e., the start of the next cycle).

        Examples
        --------

        >>> bp = BeatPattern((2, 2, 3), 4)
        >>> bp.beat_pattern_to_start_hierarchy()
        [0.0, 2.0, 4.0, 7.0]

        >>> bp.beat_pattern_to_start_hierarchy(include_cycle_length = False)
        [0.0, 2.0, 4.0]

        """
        starts = [0.0]  # always float, always starts at zero
        count = 0
        for beat_val in self.beat_list:
            count += beat_val
            this_start = count * 4 / self.beat_type
            starts.append(this_start)

        if include_cycle_length:  # include last value
            return starts
        else:
            return starts[:-1]


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
