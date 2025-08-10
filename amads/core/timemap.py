# timemap.py -- map to convert between quarters and seconds
#


class MapBeat:
    """MapBeat is a (time, beat) pair in a piece-wise linear mapping."""

    def __init__(self, time, beat):
        self.time = time
        self.beat = beat

    def copy(self):
        return MapBeat(self.time, self.beat)


class TimeMap:
    """TimeMap is a map to convert between quarters and seconds."""

    # beats -- array of MapBeat
    # last_tempo -- final beats per second to extrapolate from final
    #         breakpoint

    def __init__(self, bpm=100.0):
        self.beats = [MapBeat(0.0, 0.0)]  # initial beat
        self.last_tempo = bpm / 60.0  # 100 bpm default

    def show(self, indent):
        """print a summary of this time map"""
        print(" " * indent, "TimeMap: [ ", sep="", end="")
        for i, mb in enumerate(self.beats):
            tempo = self.index_to_tempo(i + 1)
            print(f"({mb.beat:.2g}, {mb.time:.3g}s, {tempo:.3g}bpm) ", sep="", end="")
        print("]")

    def deep_copy(self):
        """make a full copy of this time map"""
        newtm = TimeMap(bpm=self.last_tempo * 60)
        for i in self.beats[1:]:
            newtm.beats.append(i.copy())
        return newtm

    def append_beat_tempo(self, beat, tempo):
        """Append a MapBeat specifying a change to tempo at beat.
        beat must be >= last MapBeat's beat. You cannot insert a tempo
        change before the end of the TimeMap. tempo will hold forever
        beginning at beat unless you call append_beat_tempo again to
        change the tempo somewhere beyond beat.

        Parameters
        ----------
        beat: float
            The beat measured in quarters where the tempo changes
        tempo: float
            The new tempo at beat measured in beats per minute
        """
        last_beat = self.beats[-1].beat  # get the last beat
        assert beat >= last_beat
        if beat > last_beat:
            self.beats.append(MapBeat(self.beat_to_time(beat), beat))
        self.last_tempo = tempo / 60.0  # from bpm to bps
        # print("append_beat_tempo", tempo, self.beats[-1])

    def locate_time(self, time):
        """find the insertion index for a 0-based beat at time in seconds"""
        i = 0
        while i < len(self.beats) and time > self.beats[i].time:
            i = i + 1
        return i

    def locate_beat(self, beat):
        """find the insertion index for a beat; equivalent to find the first
        map entry such that entry.beat is > beat, or if beat is greater than
        beats of all entries, return the length of beats.
        """
        i = 0
        while i < len(self.beats) and beat > self.beats[i].beat:
            i = i + 1
        return i

    def beat_to_time(self, beat):
        """convert beat time to seconds"""
        if beat <= 0:  # there is no negative time or tempo before 0
            return beat  # so just pretend like tempo is 60 bpm
        i = self.locate_beat(beat)
        if i == len(self.beats):
            # special case: beat >= than last time,beat pair
            # so extrapolate using last_tempo
            mb1 = self.beats[i - 1]
            if self.last_tempo:
                return mb1.time + (beat - mb1.beat) / self.last_tempo
            elif i == 1:  # only one time point and no last_tempo!
                # assume a tempo of 100
                return beat * 0.6  # (60sec/min / 100bpm)
            else:  # extrapolate from last two time map entries
                mb0 = self.beats[i - 2]
        else:  # interpolate between i - 1 and i
            # note: i is at least 1 because first MapBeat is at time 0
            # and beat > 0
            mb0 = self.beats[i - 1]
            mb1 = self.beats[i]
        # whether we extrapolate or interpolate, the math is the same:
        time_dif = mb1.time - mb0.time
        beat_dif = mb1.beat - mb0.beat
        return mb0.time + (beat - mb0.beat) * time_dif / beat_dif

    def beat_to_tempo(self, beat):
        """what is the tempo in bpm at beat? If there is a tempo change
        here, use the tempo on the left (before the change)
        """
        return self.index_to_tempo(self.locate_beat(beat))

    def index_to_tempo(self, i):
        """return the tempo at entry i in tempo map in bpm -- the tempo
        is in effect JUST BEFORE entry i, where tempo might
        change. Typically, i is related to locate_beat(beat), so i
        refers to the first map entry BEYOND beat.
        """
        # two cases here: (1) we're beyond the last entry, so
        #   use last_tempo or extrapolate, OR
        # (2) there's only one entry, so use last_tempo or
        #   return the default tempo
        if i == len(self.beats) or len(self.beats) <= 1:
            # special case: beat >= last time.beat pair
            # so extrapolate using last_tempo if it is there
            if self.last_tempo:
                return self.last_tempo * 60.0
            elif i <= 1:  # only one time point and no last tempo!
                # assume a tempo of 100
                return 100.0 / 60.0
            else:  # extrapolate from last two time map entries
                mb0 = self.beats[i - 2]
                mb1 = self.beats[i - 1]
        elif i == 0:
            mb0 = self.beats[0]
            mb1 = self.beats[1]
        else:
            mb0 = self.beats[i - 1]
            mb1 = self.beats[i]
        time_dif = mb1.time - mb0.time
        beat_dif = mb1.beat - mb0.beat
        return beat_dif * 60.0 / time_dif

    def time_to_beat(self, time):
        """return the beat associated with time seconds."""
        if time <= 0:
            return time
        i = self.locate_time(time)
        if i == len(self.beats):  # beat is beyond last time map entry
            if self.last_tempo:  # extrapolate beyond last time map entry
                mb0 = self.beats[i - 1]
                return mb0.beat + (time - mb0.time) * self.last_tempo
            elif i == 1:  # only one time point and no last tempo!
                return time * 100 / 60  # assume 100 bpm
            else:  # extrapolate from last two time map entries
                mb0 = self.beats[i - 2]
                mb1 = self.beats[i - 1]
        else:  # interpolate between the surrounding time map entries
            mb0 = self.beats[i - 1]
            mb1 = self.beats[i]
        time_dif = mb1.time - mb0.time
        beat_dif = mb1.beat - mb0.beat
        return mb0.beat + (time - mb0.time) * beat_dif / time_dif

    """
    if we support any extraction of data from scores and want to retain
    the TimeMap, we'll need some of these editing methods, which were
    originally written in Serpent. They are not converted to Python yet.

    def trim(start, end, units_are_seconds=True):
        # extract the time map from start to end and shift to time zero
        # start and end are time in seconds if units_are_seconds is true

        var i = 0 // index into beats
        var start_index // index of first breakpoint after start
        var count = 1
        var initial_beat = start
        var final_beat = end
        if units_are_seconds:
            initial_beat = time_to_beat(start)
            final_beat = time_to_beat(end)
        else
            start = beat_to_time(initial_beat)
            end = beat_to_time(final_beat)
        while i < len(beats) and beats[i].time < start:
            i = i + 1
        // now i is index into beats of the first breakpoint after start
        #if i >= len(beats):
        #    return // only one
        // beats[0] is (0,0) and remains that way
        // copy beats[start_index] to beats[1], etc.
        // skip any beats at or near (start,initial_beat), using count
        // to keep track of how many entries there are
        start_index = i
        while i < len(beats) and beats[i].time < end:
            if beats[i].time - start > alg_eps and
               beats[i].beat - initial_beat > alg_eps:
                beats[i].time = beats[i].time - start
                beats[i].beat = beats[i].beat - initial_beat
                beats[i - start_index + 1] = beats[i]
                count = count + 1
            else:
                start_index = start_index + 1
            i = i + 1
        // set last tempo data
        // we last examined beats[i-1] and copied it to
        //   beats[i - start_index]. Next tempo should come
        //   from beats[i] and store in beats[i - start_index + 1]
        // case 1: there is at least one breakpoint beyond end
        //         => interpolate to put a breakpoint at end
        // case 2: no more breakpoints => set last tempo data
        if i < len(beats):
            // we know beats[i].time >= end, so case 1 applies
            beats[i - start_index + 1].time = end - start
            beats[i - start_index + 1].beat = final_beat - initial_beat
            last_tempo = false // extrapolate to get tempo
            count = count + 1
        // else we will just use stored last tempo (if any)
        beats.set_len(count)

    def cut(start, len, units_are_seconds):
        # remove portion of time map from start to start + len,
        # shifting the tail left by len. start and len are in whatever
        # units the score is in. If you cut the time map as well as cut
        # the tracks of the sequence, then sequences will preserve the
        # association between tempo changes and events
        // display "before cut", start, len, units_are_seconds
        show()
        var end = start + len
        var initial_beat = start
        var final_beat = end
        var i = 0

        if units_are_seconds:
            initial_beat = time_to_beat(start)
            final_beat = time_to_beat(end)
        else
            start = beat_to_time(initial_beat)
            end = beat_to_time(final_beat)
            len = end - start
        var beat_len = final_beat - initial_beat

        while i < len(beats) and beats[i].time < start - alg_eps:
            i = i + 1
        // now i is index into beats of the first breakpoint on or
        // after start, insert (start, initial_beat) in map
        // note: i may be beyond the last breakpoint, so beat[i] may
        // be out of bounds
        // display "after while", i, len(beats)
        if i < len(beats) and within(beats[i].time, start, alg_eps)
            // perterb time map slightly (within alg_eps) to place
            // break point exactly at the start time
            //display "reset", i
            beats[i].time = start
            beats[i].beat = initial_beat
        else
            //display "insert", i
            var point = Alg_beat(start, initial_beat)
            beats.insert(i, point)
        // now, we are correct up to beats[i]. find first beat after
        // end so we can start shifting from there
        i = i + 1
        var start_index = i
        while i < len(beats) and beats[i].time < end + alg_eps:
            i = i + 1
        // now beats[i] is the next point to be included in beats
        // but from i onward, we must shift by (-len, -beat_len)
        while i < len(beats):
            var b = beats[i]
            b.time = b.time - len
            b.beat = b.beat - beat_len
            beats[start_index] = b
            i = i + 1
            start_index = start_index + 1
        beats.set_len(start_index)
        //print "after cut"
        //show()


    def copy():
        var new_map = Alg_time_map()
        new_map.beats = array(len(beats))
        for i = 0 to len(beats):
            new_map.beats[i] = Alg_beat(beats[i].time, beats[i].beat)
        new_map.last_tempo = last_tempo
        return new_map


    def insert_time(start, len):
        // find time,beat pair that determines tempo at start
        // compute beat offset = (delta beat / delta time) * len
        // add len,beat offset to each following Alg_beat
        var i = locate_time(start) // start <= beats[i].time
        if beats[i].time == start:
            i = i + 1
        if i > 0 and i < len(beats):
            var beat_offset = len * (beats[i].beat - beats[i - 1].beat) /
                                    (beats[i].time - beats[i - 1].time)
            while i < len(beats):
                beats[i].beat = beats[i].beat + beat_offset
                beats[i].time = beats[i].time + len
                i = i + 1


    def insert_beats(start, len):
        // find time,beat pair that determines tempo at start
        // compute beat offset = (delta beat / delta time) * len
        // add len,beat offset to each following Alg_beat
        //print "time map before insert beats"
        //show()
        var i = locate_beat(start) // start <= beats[i].time
        if beats[i].beat == start:
            i = i + 1
        if i > 0 and i < len(beats):
            var time_offset = len * (beats[i].time - beats[i - 1].time) /
                                    (beats[i].beat - beats[i - 1].beat)
            while i < len(beats):
                beats[i].time = beats[i].time + time_offset
                beats[i].beat = beats[i].beat + len
                i = i + 1
        //print "time map after insert beats"
        //show()


    def show():
        print "Alg_time_map: ";
        for b in beats:
            print "("; b.time; ", "; b.beat; ") ";
        print "last tempo: "; last_tempo
    """
