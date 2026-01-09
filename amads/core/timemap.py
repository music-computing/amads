"""
Mapping between quarters and seconds (beats and time).

    from amads.core import *

Note: `amads.core` includes `amads.core.basics`, `amads.core.distribution` and amads.core.timemap`.
"""

import sys


class MapQuarter:
    """
    Represents a (time, quarter) pair in a piece-wise linear mapping.

    Parameters
    ----------
    time : float
        The time in seconds.
    quarter : float
        The corresponding quarter note position.

    Attributes
    ----------
    time : float
        The time in seconds.
    quarter : float
        The corresponding quarter note position.

    Methods
    -------
    copy()
        Return a copy of the MapQuarter instance.
    """

    __slots__ = ["time", "quarter"]
    time: float
    quarter: float

    def __init__(self, time: float, quarter: float):
        self.time = time
        self.quarter = quarter

    def copy(self) -> "MapQuarter":
        """return a copy of this MapQuarter

        Returns
        -------
        MapQuarter
            A copy of this MapQuarter instance.
        """
        return MapQuarter(self.time, self.quarter)


class TimeMap:
    """
    Implement the `time_map` attribute of `Score` class.

    Every `Score` has a `time_map` attribute whose value is a
    `TimeMap` that maintains a mapping between time in seconds
    and beats in quarters. A `TimeMap` encodes the information
    in a MIDI File tempo track as well as tempo information from
    a Music XML score.

    This class holds a list representing tempo changes as a list of
    (time, quarter) pairs, which you can think of as tempo changes.
    More mathematically, they are breakpoints in a piece-wise linear
    function that maps from time to quarter or from quarter to time.

    Since tempo is not continuous, the tempo at a breakpoint is
    defined to be the tempo just *after* the breakpoint.

    Parameters
    ----------
    qpm : float, optional
        Initial tempo in quarters per minute (default is 100.0).

    Attributes
    ----------
    changes : list of MapQuarter
        List of (time, quarter) breakpoints for piece-wise linear mapping.
    last_tempo : float
        Final quarters per second (qps) for extrapolatation.

    Examples
    --------
    >>> tm = TimeMap(qpm=120)
    >>> tm.append_change(4.0, 60.0)  # change to 60 qpm at quarter 4
    >>> tm.quarter_to_time(5.0)
    3.0
    >>> tm.time_to_quarter(3.0)
    5.0
    """

    __slots__ = ["changes", "last_tempo"]
    changes: list[MapQuarter]
    last_tempo: float

    def __init__(self, qpm=100.0):
        self.changes = [MapQuarter(0.0, 0.0)]  # initial quarter
        self.last_tempo = qpm / 60.0  # 100 qpm default

    def show(self, indent: int = 0, file=sys.stdout) -> None:
        """Print a summary of this time map.

        Parameters
        ----------
        indent : int, optional
            Number of spaces to indent (default is 0).
        file : TextIO, optional
            The file to print to (default is sys.stdout).

        Returns
        -------
        None
        """
        print(" " * indent, "TimeMap: [ ", sep="", end="", file=file)
        for i, mb in enumerate(self.changes):
            tempo = self.get_tempo_at(i)
            print(
                f"({mb.quarter:.2g}, {mb.time:.3g}s, {tempo:.3g}qpm) ",
                sep="",
                end="",
                file=file,
            )
        print("]", file=file)

    def deep_copy(self) -> "TimeMap":
        """Make a full copy of this time map.

        Returns
        -------
        TimeMap
            A deep copy of this TimeMap instance.
        """
        newtm = TimeMap(qpm=self.last_tempo * 60)
        for i in self.changes[1:]:
            newtm.changes.append(i.copy())
        return newtm

    def append_change(self, quarter: float, tempo: float) -> None:
        """Append a tempo change at a given quarter.

        Append a `MapQuarter` specifying a change to tempo at quarter.
        quarter must be at least as great as last MapQuarter's quarter.
        You cannot insert a tempo change before the end of the TimeMap.
        The `tempo` will hold forever beginning at `quarter` unless you call
        `append_change` again to change the tempo somewhere beyond
        `quarter`.

        Parameters
        ----------
        quarter: float
            The quarter measured in quarters where the tempo changes
        tempo: float
            The new tempo at quarter measured in quarters per minute.
            Typically, this is the same as beats per minute (BPM),
            but only when a beat lasts one quarter.

        Returns
        -------
        None
        """
        last_quarter = self.changes[-1].quarter  # get the last quarter
        assert quarter >= last_quarter
        if quarter > last_quarter:
            self.changes.append(
                MapQuarter(self.quarter_to_time(quarter), quarter)
            )
        self.last_tempo = tempo / 60.0  # from qpm to qps
        # print("append_change", tempo, self.changes[-1])

    def get_time_at(self, index: int) -> float:
        """Get the time in seconds at a given index in the changes list.

        Parameters
        ----------
        index : int
            The index in the changes list.

        Returns
        -------
        float
            The time in seconds at the specified index.
        """
        return self.changes[index].time

    def get_tempo_at(self, index: int) -> float:
        """Get the tempo at a given index in the changes list.

        The tempo changes at each breakpoint. This method returns
        the tempo in QPM just after the breakpoint at the specified
        index.

        Parameters
        ----------
        index : int
            The index in the changes list.

        Returns
        -------
        float
            The tempo in quarters per minute immediately after
            the specified index.

        The tempo at entry i is the tempo in effect JUST BEFORE entry i,

        Parameters
        ----------
        index : int
            The index in the changes list.

        Returns
        -------
        float
            The tempo in quarters per minute (qpm) just after entry i.
        """
        # two cases here: (1) we're at or beyond the last entry, so
        #   use last_tempo or extrapolate, OR
        #   (2) there's only one entry, so use last_tempo or
        #   return the default tempo
        if index < 0:
            raise ValueError("Index must be non-negative")
        if index >= len(self.changes) - 1:
            # special case: quarter >= last (time, quarter) pair
            # so extrapolate using last_tempo if it is there
            return self.last_tempo * 60.0
        mb0 = self.changes[index]
        mb1 = self.changes[index + 1]
        time_dif = mb1.time - mb0.time
        quarter_dif = mb1.quarter - mb0.quarter
        return quarter_dif * 60.0 / time_dif

    def _time_to_insert_index(self, time: float) -> int:
        """Find the insertion index for a given time in seconds.

        Returns the index of the first MapQuarter whose `time` attribute
        is greater than the specified `time`. If `time` is greater than
        all entries, returns the length of `self.changes`.

        This assumes that if you insert a tempo change at an existing
        time, the new change goes *after* the existing one. (But
        really, shouldn't you overwrite the existing one?)

        Parameters
        ----------
        time : float
            The time in seconds to locate.

        Returns
        -------
        int
            The insertion index for the given time.
        """
        i = 0
        while i < len(self.changes) and time >= self.changes[i].time:
            i = i + 1
        return i

    # def _time_to_index(self, time: float) -> int:
    #     """Find the index for a given time in seconds.

    #     Returns the index of the first MapQuarter whose `time` attribute
    #     is equal or greater than the specified `time`. If `time` is greater
    #     than all entries, returns the length of `self.changes`.

    #     Parameters
    #     ----------
    #     time : float
    #         The time in seconds to locate.

    #     Returns
    #     -------
    #     int
    #         The insertion index for the given time.
    #     """
    #     i = 0
    #     while i < len(self.changes) and time > self.changes[i].time:
    #         i = i + 1
    #     return i

    def _quarter_to_insert_index(self, quarter: float) -> int:
        """Find the insertion index for a given quarter in seconds.

        Returns the index of the first MapQuarter whose `quarter`
        attribute is greater than the specified
        `quarter`. If `quarter` is greater than all entries, returns the
        length of `self.changes`.

        This assumes that if you insert a tempo change at an existing
        quarter, the new change goes *after* the existing one. (But
        really, shouldn't you overwrite the existing one?)

        Parameters
        ----------
        quarter : float
            The quarter note position to locate.

        Returns
        -------
        int
        The insertion index for the given quarter position.
        """
        i = 0
        while i < len(self.changes) and quarter >= self.changes[i].quarter:
            i = i + 1
        return i

    # def _quarter_to_index(self, quarter: float) -> int:
    #     """Find the index for a given quarter in seconds.

    #     Returns the index of the first MapQuarter whose `quarter`
    #     attribute is equal or greater than the specified `quarter`.
    #     If `quarter` is greater than all entries, returns the
    #     length of `self.changes`.

    #     Parameters
    #     ----------
    #     quarter : float
    #         The quarter note position to locate.

    #     Returns
    #     -------
    #     int
    #     The index for the given quarter position.
    #     """
    #     i = 0
    #     while i < len(self.changes) and quarter > self.changes[i].quarter:
    #         i = i + 1
    #     return i

    def quarter_to_time(self, quarter: float) -> float:
        """Convert time in quarters to time to seconds.

        Parameters
        ----------
        quarter: float
            A score position in changes.

        Returns
        -------
        float
            The time in seconds corresponding to `quarter`.
        """
        if quarter <= 0:  # there is no negative time or tempo before 0
            return quarter  # so just pretend like tempo is 60 qpm
        i = self._quarter_to_insert_index(quarter)
        return self.changes[i - 1].time + (
            quarter - self.changes[i - 1].quarter
        ) * 60.0 / self.get_tempo_at(i - 1)

    def quarter_to_tempo(self, quarter: float) -> float:
        """Get the tempo in qpm at a given quarter.

        Parameters
        ----------
        quarter: float
            A score position in changes.

        Returns
        -------
        float
            The tempo at `quarter`. If there is a tempo change here,
            returns the tempo on the right (after the change).
        """
        return self.get_tempo_at(self._quarter_to_insert_index(quarter) - 1)

    # def _index_to_tempo(self, i: int) -> float:
    #     """Return the tempo at entry i in the tempo map.

    #     The tempo at entry i is the tempo in effect JUST BEFORE entry i,
    #     Typically, i is related to `_locate_quarter(quarter)`, so i
    #     refers to the first map entry BEYOND quarter. (In particular,
    #     if the quarter of interest is exactly one of the breakpoints,
    #     i will be at the *next* breakpoint. If i is 0 or there
    #     are no MapQuarter entries, return the tempo AFTER entry i.

    #     Parameters
    #     ----------
    #     i : int
    #         The index in the changes list.

    #     Returns
    #     -------
    #     float
    #         The tempo in quarters per minute (qpm) just before entry i.
    #     """
    #     # two cases here: (1) we're beyond the last entry, so
    #     #   use last_tempo or extrapolate, OR
    #     # (2) there's only one entry, so use last_tempo or
    #     #   return the default tempo
    #     if i == len(self.changes) or len(self.changes) <= 1:
    #         # special case: quarter >= last time.quarter pair
    #         # so extrapolate using last_tempo if it is there
    #         return self.last_tempo * 60.0

    #     elif i == 0:
    #         mb0 = self.changes[0]
    #         mb1 = self.changes[1]
    #     else:
    #         mb0 = self.changes[i - 1]
    #         mb1 = self.changes[i]
    #     time_dif = mb1.time - mb0.time
    #     quarter_dif = mb1.quarter - mb0.quarter
    #     return quarter_dif * 60.0 / time_dif

    def time_to_quarter(self, time: float) -> float:
        """Convert time in seconds to quarter position.

        Parameters
        ----------
        time: float
            A score time in seconds.

        Returns
        -------
        float
            The score position in changes corresponding to `time`.
        """
        if time <= 0:
            return time
        i = self._time_to_insert_index(time)
        return (
            self.changes[i - 1].quarter
            + (time - self.changes[i - 1].time)
            * self.get_tempo_at(i - 1)
            / 60.0
        )

    def time_to_tempo(self, time: float) -> float:
        """Get the tempo in qpm at a given time (in seconds).

        Parameters
        ----------
        time: float
            A score time in seconds.

        Returns
        -------
        float
            The tempo at `time`. If there is a tempo change here,
            use the tempo on the right (aftr the change).
        """
        return self.get_tempo_at(self._time_to_insert_index(time) - 1)

    # Editing methods for TimeMap
    """
    if we support any extraction of data from scores and want to retain
    the TimeMap, we'll need some of these editing methods, which were
    originally written in Serpent. They are not converted to Python yet.

    def trim(start, end, units_are_seconds=True):
        # extract the time map from start to end and shift to time zero
        # start and end are time in seconds if units_are_seconds is true

        var i = 0 // index into changes
        var start_index // index of first breakpoint after start
        var count = 1
        var initial_quarter = start
        var final_quarter = end
        if units_are_seconds:
            initial_quarter = time_to_quarter(start)
            final_quarter = time_to_quarter(end)
        else
            start = quarter_to_time(initial_quarter)
            end = quarter_to_time(final_quarter)
        while i < len(changes) and changes[i].time < start:
            i = i + 1
        // now i is index into changes of the first breakpoint after start
        #if i >= len(changes):
        #    return // only one
        // changes[0] is (0,0) and remains that way
        // copy changes[start_index] to changes[1], etc.
        // skip any changes at or near (start,initial_quarter), using count
        // to keep track of how many entries there are
        start_index = i
        while i < len(changes) and changes[i].time < end:
            if changes[i].time - start > alg_eps and
               changes[i].quarter - initial_quarter > alg_eps:
                changes[i].time = changes[i].time - start
                changes[i].quarter = changes[i].quarter - initial_quarter
                changes[i - start_index + 1] = changes[i]
                count = count + 1
            else:
                start_index = start_index + 1
            i = i + 1
        // set last tempo data
        // we last examined changes[i-1] and copied it to
        //   changes[i - start_index]. Next tempo should come
        //   from changes[i] and store in changes[i - start_index + 1]
        // case 1: there is at least one breakpoint beyond end
        //         => interpolate to put a breakpoint at end
        // case 2: no more breakpoints => set last tempo data
        if i < len(changes):
            // we know changes[i].time >= end, so case 1 applies
            changes[i - start_index + 1].time = end - start
            changes[i - start_index + 1].quarter = (final_quarter -
                                                     initial_quarter)
            last_tempo = false // extrapolate to get tempo
            count = count + 1
        // else we will just use stored last tempo (if any)
        changes.set_len(count)

    def cut(start, len, units_are_seconds):
        # remove portion of time map from start to start + len,
        # shifting the tail left by len. start and len are in whatever
        # units the score is in. If you cut the time map as well as cut
        # the tracks of the sequence, then sequences will preserve the
        # association between tempo changes and events
        // display "before cut", start, len, units_are_seconds
        show()
        var end = start + len
        var initial_quarter = start
        var final_quarter = end
        var i = 0

        if units_are_seconds:
            initial_quarter = time_to_quarter(start)
            final_quarter = time_to_quarter(end)
        else
            start = quarter_to_time(initial_quarter)
            end = quarter_to_time(final_quarter)
            len = end - start
        var quarter_len = final_quarter - initial_quarter

        while i < len(changes) and changes[i].time < start - alg_eps:
            i = i + 1
        // now i is index into changes of the first breakpoint on or
        // after start, insert (start, initial_quarter) in map
        // note: i may be beyond the last breakpoint, so quarter[i] may
        // be out of bounds
        // display "after while", i, len(changes)
        if i < len(changes) and within(changes[i].time, start, alg_eps)
            // perterb time map slightly (within alg_eps) to place
            // break point exactly at the start time
            //display "reset", i
            changes[i].time = start
            changes[i].quarter = initial_quarter
        else
            //display "insert", i
            var point = Alg_quarter(start, initial_quarter)
            changes.insert(i, point)
        // now, we are correct up to changes[i]. find first quarter after
        // end so we can start shifting from there
        i = i + 1
        var start_index = i
        while i < len(changes) and changes[i].time < end + alg_eps:
            i = i + 1
        // now changes[i] is the next point to be included in changes
        // but from i onward, we must shift by (-len, -quarter_len)
        while i < len(changes):
            var b = changes[i]
            b.time = b.time - len
            b.quarter = b.quarter - quarter_len
            changes[start_index] = b
            i = i + 1
            start_index = start_index + 1
        changes.set_len(start_index)
        //print "after cut"
        //show()


    def copy():
        var new_map = Alg_time_map()
        new_map.changes = array(len(changes))
        for i = 0 to len(changes):
            new_map.changes[i] = Alg_quarter(changes[i].time,
                                              changes[i].quarter)
        new_map.last_tempo = last_tempo
        return new_map


    def insert_time(start, len):
        // find time,quarter pair that determines tempo at start
        // compute quarter offset = (delta quarter / delta time) * len
        // add len,quarter offset to each following Alg_quarter
        var i = _time_to_insert_index(start) // start <= changes[i].time
        if changes[i].time == start:
            i = i + 1
        if i > 0 and i < len(changes):
            var quarter_offset = len * (changes[i].quarter -
                                        changes[i - 1].quarter) /
                                       (changes[i].time - changes[i - 1].time)
            while i < len(changes):
                changes[i].quarter = changes[i].quarter + quarter_offset
                changes[i].time = changes[i].time + len
                i = i + 1


    def insert_changes(start, len):
        // find time,quarter pair that determines tempo at start
        // compute quarter offset = (delta quarter / delta time) * len
        // add len,quarter offset to each following Alg_quarter
        //print "time map before insert changes"
        //show()
        var i = _locate_quarter(start) // start <= changes[i].time
        if changes[i].quarter == start:
            i = i + 1
        if i > 0 and i < len(changes):
            var time_offset = len * (changes[i].time - changes[i - 1].time) /
                                    (changes[i].quarter -
                                     changes[i - 1].quarter)
            while i < len(changes):
                changes[i].time = changes[i].time + time_offset
                changes[i].quarter = changes[i].quarter + len
                i = i + 1
        //print "time map after insert changes"
        //show()


    def show():
        print "Alg_time_map: ";
        for b in changes:
            print "("; b.time; ", "; b.quarter; ") ";
        print "last tempo: "; last_tempo
    """
