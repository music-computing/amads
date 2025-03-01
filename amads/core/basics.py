# basics.py - basic symbolic music representation classes
# fmt: off
# flake8: noqa E129,E303
"""
Quick overview: The basic hierarchy of a score is shown here.
Each level of this hierarchy can contain 0
or more instances of the next level. Levels are optional,
allowing for more note-list-like representations:

Score (one per musical work or movement)
    Part (one per instrument)
        Staff (usually 1, but e.g. 2 for grand staff)
            Measure (one for each measure)
                (Measure can contain multiple instances of the following)
                Note
                Rest
                Chord
                    Note (one for each note of the chord)
                KeySignature
                TimeSignature

A "flattened" score looks like this:

Score (one per musical work or movement)
    Part (one per instrument)
        Note (no other instances allowed, no ties)

"""

import copy
import functools
from math import floor
from typing import Generator, Optional, Type, Union

from amads.core.time_map import TimeMap


class Event:
    """
    A superclass for Note, Rest, EventGroup, and just about
    anything that takes place in time.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration: float
            The duration of the event in quarters or seconds.
        delta : float
            The onset (start) time relative to the parent's onset time.

    Attributes
    ----------
        parent : Optional[Event]
            The containing object or None.
        duration : float
            The duration of the event in quarters or seconds.
        delta : float
            The onset (start) time relative to the parent's onset time.
    """

    def __init__(self, parent: Optional["EventGroup"], duration: float, delta: float):
        """
        Initialize an Event instance.

        Parameters
        ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration : float
            The duration of the event in quarters or seconds.
        delta : float
            The onset (start) time expressed relative to the parent onset time.
        """
        self.parent = None
        self.duration = duration
        self.delta = delta
        if parent:
            assert isinstance(parent, EventGroup)
            parent.insert(self)


    def copy(self) -> "Event":
        """Return a shallow copy of the Event instance. Probably you should use
        copy_into or emptycopy instead

        Returns
        -------
        Event
            A shallow copy of the Event instance.
        """
        return copy.copy(self)


    def copy_into(self, parent: Optional["EventGroup"]) -> "Event":
        """Perform a shallow copy, then insert into parent. If parent is not
        None, adjust the delta to preseve the (global) onset time under
        the new parent.

        Parameters
        ----------
        parent : Optional[EventGroup]
            The new parent to insert the copied Event into.

        Returns
        -------
        Event
            A shallow copy of the Event instance with the new parent.
        """
        c = self.copy()
        c.parent = None
        if parent:
            # adjust delta to preserve onset time of this event:
            c.delta = self.onset - parent.onset
            parent.insert(c)
        return c


    def deepcopy_into(self, parent: Optional["EventGroup"]) -> "Event":
        """Perform deep copy, then insert into parent. If parent is not
        None, adjust the delta to preseve the (global) onset time under
        the new parent.

        Parameters
        ----------
        parent : Optional[EventGroup]
            The new parent to insert the copied Event into.

        Returns
        -------
        Event
            A deep copy of the Event instance with the new parent.
        """
        # remove link to parent to break link going up the tree
        original_parent = self.parent
        self.parent = None
        c = copy.deepcopy(self)  # deep copy of this event down to leaf nodes
        self.parent = original_parent  # restore link to parent
        if parent:
            # adjust delta to preserve onset time of this event:
            c.delta += original_parent.onset - parent.onset
            parent.insert(c)
        return c


    def convert_to_seconds(self, parent_onset_beat: float,
                           parent_onset_time: float, time_map: TimeMap) -> None:
        """Convert the event's duration and delta to seconds using the
        provided TimeMap.

        Parameters
        ----------
        parent_onset_beat : float
            The parent's onset time in beats.
        parent_onset_time : float
            The parent's onset time in seconds.
        time_map : TimeMap
            The TimeMap object used for conversion.
        """
        onset_beat = parent_onset_beat + self.delta
        onset_time = time_map.seconds(onset_beat)
        offset_time = time_map.seconds(onset_beat + self.duration)
        self.delta = onset_time - parent_onset_time
        self.duration = offset_time - onset_time


    @property
    def delta_offset(self) -> float:
        """Retrieve the offset (stop) time relative to the parent onset
        (start) time.
        Returns
        -------
        float
            The offset (stop) time relative to the parent onset (start) time.
        """
        return self.delta + self.duration


    @property
    def onset(self) -> float:
        """Retrieve the global onset (start) time.
        Returns
        -------
        float
            The global onset (start) time."""
        p = self.parent
        if p is None:
            return self.delta
        return p.onset + self.delta


    @property
    def offset(self) -> float:
        """Retrieve the global offset (stop) time.
        Returns
        -------
        float
            The global offset (stop) time.
        """
        return self.onset + self.duration


    @onset.setter
    def onset(self, value: float) -> None:
        """Set the global onset (start) time.

        Parameters
        ----------
        value : float
            The new global onset (start) time.
        """
        if self.parent is None:
            self.delta = value
        else:
            self.delta = value - self.parent.onset


    @offset.setter
    def offset(self, value: float) -> None:
        """Set the global offset (stop) time.
        It is an error to set the duration to be less than zero.

        Parameters
        ----------
        value : float
            The new global offset (stop) time.
        """
        self.duration = value - self.onset
        assert self.duration >= 0


    @property
    def staff(self) -> Optional["Staff"]:
        """Retrieve the Staff containing this event
        Returns
        -------
        Optional[Staff]
            The Staff containing this event or None if not found."""
        p = self.parent
        while p and not isinstance(p, Staff):
            p = p.parent
        return p



class Rest(Event):
    """Rest represents a musical rest. It is normally an element of
    a Measure.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration : float, optional
            The duration of the rest in quarters or seconds. (Defaults to 1)
        delta : float, optional
            The onset (start) time expressed relative to the parent's onset
            time. (Defaults to 0)

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration : float
            The duration of the rest in quarters or seconds.
        delta : float
            The onset (start) time relative to the parent's onset time.
    """

    def __init__(self, parent: "EventGroup", duration: float = 1, delta: float = 0):
        super().__init__(parent, duration, delta)


    def show(self, indent: int = 0) -> "Rest":
        """Display the Rest information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Rest
            The Rest instance itself.
        """

        print(" " * indent, f"Rest at {self.onset:.3f} ",
              f"delta {self.delta:.3f} duration {self.duration:.3f}", sep="")
        return self



class Note(Event):
    """Note represents a musical note. It is normally an element of
    a Measure.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration : float, optional
            The duration of the note in quarters or seconds. (Defaults to 1)
        delta : float, optional
            The onset (start) time expressed relative to the parent's onset
            time. (Defaults to 0)
        pitch : Union[Pitch, int], optional
            A Pitch object or an integer MIDI key number that will be
            converted to a Pitch object. (Defaults to C4)
        dynamic : Optional[Union[int, str]], optional
            Dynamic level (MIDI velocity) or string. (Defaults to None)
        lyric : Optional[str], optional
            Lyric text. (Defaults to None)

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration : float
            The duration of the note in quarters or seconds.
        delta : float
            The onset (start) time relative to the parent's onset time.
        pitch : Pitch
            The pitch of the note.
        dynamic : Optional[Union[int, str]]
            Dynamic level (MIDI velocity) or string.
        lyric : Optional[str]
            Lyric text.
        tie : Optional[str]
            Tie information ('start', 'stop', 'continue', or None).
    """

    def __init__(self,
                 parent: Optional["EventGroup"],
                 duration: float = 1,
                 pitch: Union["Pitch", int, None] = None,
                 dynamic: Union[int, str, None] = None,
                 lyric: Optional[str] = None,
                 delta: float = 0):
        """pitch is normally a Pitch, but can be an integer MIDI key number
        that will be converted to a Pitch object.
        """
        super().__init__(parent, duration, delta)
        if isinstance(pitch, Pitch):
            self.pitch = pitch
        elif pitch:
            self.pitch = Pitch(pitch)
        else:
            self.pitch = Pitch(60)
        self.dynamic = dynamic
        self.lyric = lyric
        self.tie = None


    def __deepcopy__(self, memo: bool = None) -> "Note":
        """Return a deep copy of the Note instance. The pitch is
        shallow copied to avoid copying the entire Pitch object.

        Parameters
        ----------
        memo : bool, optional
            A dictionary to keep track of already copied objects.
            (Defaults to None)

        Returns
        -------
        Note
            A deep copy of the Note instance with a shallow copy of the pitch.
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == "pitch":
                setattr(result, k, self.pitch)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result


    def show(self, indent: int = 0) -> "Note":
        """Show the note with its pitch name, delta, duration, and optional
        tie, dynamic, and lyric information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Note
            The Note instance itself.
        """
        tieinfo = ""
        if self.tie is not None:
            tieinfo = " tie " + self.tie
        dynamicinfo = ""
        if self.dynamic is not None:
            dynamicinfo = " dyn " + str(self.dynamic)
        lyricinfo = ""
        if self.lyric is not None:
            lyricinfo = " lyric " + self.lyric
        print(" " * indent, f"Note at {self.onset:0.3f} ",
              f"delta {self.delta:0.3f} duration {self.duration:0.3f} pitch ",
              self.name_with_octave, tieinfo, dynamicinfo, lyricinfo, sep="")
        return self


    @property
    def name(self) -> str:
        """Retrieve the name of the pitch, e.g. 0, 2, 4, 5, 7, 9, 11,
        corresponding to letter names without accidentals.
        """
        return self.pitch.name


    @property
    def name_str(self) -> str:
        """Retrieve the string representation of the pitch name,
        including accidentals, e.g. A# or Bb.
        """
        return self.pitch.name_str


    @property
    def name_with_octave(self) -> str:
        """Retrieve the string representation of the pitch name
        with octave, e.g. A4 or Bb3.
        """
        return self.pitch.name_with_octave


    @property
    def pitch_class(self) -> int:
        """Retrieve the pitch class of the note, e.g. 0, 1, 2, ..., 11."""
        return self.pitch.pitch_class


    @pitch_class.setter
    def pitch_class(self, pc: int) -> None:
        """Set the pitch class of the note.

        Parameters
        ----------
        pc : int
            The new pitch class value.
        """
        self.pitch.pitch_class = pc


    @property
    def octave(self) -> int:
        """Retrieve the octave number of the note, based on keynum.
        E.g. C4 is enharmonic to B#3 and represent the same (more or less)
        pitch, but BOTH have an octave of 4. On the other hand name_str()
        will return "C4" and "B#3", respectively.

        Returns
        -------
        int
            The octave number of the note.
        """
        return self.octave


    @octave.setter
    def octave(self, oct: int) -> None:
        """Set the octave number of the note.

        Parameters
        ----------
        oct : int
            The new octave number.
        """
        self.pitch.octave = oct


    @property
    def keynum(self) -> int:
        """Retrieve the MIDI key number of the note, e.g. C4 = 60.

        Returns
        -------
        int
            The MIDI key number of the note.
        """
        return self.pitch.keynum


    def enharmonic(self) -> "Pitch":
        """Return a Pitch where alt is zero or has the opposite sign and
        where alt is minimized. E.g. enharmonic(C-double-flat) is A-sharp
        (not B-flat). If alt is zero, return a Pitch with alt of +1 or -1
        if possible. Otherwise, return a Pitch with alt of -2.

        Returns
        -------
        Pitch
            A Pitch object representing the enharmonic equivalent of the note.
        """
        return self.pitch.enharmonic()


    def upper_enharmonic(self) -> "Pitch":
        """Return a valid Pitch with alt decreased by 1 or 2, e.g. C#->Db,
        C##->D, C###->D#.

        Returns
        -------
        Pitch
            A Pitch object representing the upper enharmonic
            equivalent of the note.
        """
        return self.pitch.upper_enharmonic()


    def lower_enharmonic(self) -> "Pitch":
        """Return a valid Pitch with alt increased by 1 or 2, e.g. Db->C#,
        D->C##, D#->C###.

        Returns
        -------
        Pitch
            A Pitch object representing the lower enharmonic
            equivalent of the note.
        """
        return self.pitch.lower_enharmonic()



class TimeSignature(Event):
    """TimeSignature is a zero-duration Event with timesig info.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        beat : int, optional
            The "numerator" of the key signature: beats per measure, a
            number, which may be a fraction. (Defaults to 4)
        beat_type : int, optional
            The "denominator" of the key signature: a whole number
            power of 2, e.g. 1, 2, 4, 8, 16, 32, 64. (Defaults to 4)
        delta : float, optional
            The onset (start) time expressed relative to the parent's
            onset time. (Defaults to 0)

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration : float
            Always zero for this subclass.
        delta : float
            The onset (start) time relative to the parent's onset time.
        beat : int
            The "numerator" of the key signature: beats per measure.
        beat_type : int
            The "denominator" of the key signature: a whole number power of 2.
    """

    def __init__(self,
                 parent: Optional["EventGroup"],
                 beat: int = 4,
                 beat_type: int = 4,
                 delta: float = 0):
        super().__init__(parent, 0, delta)
        self.beat = beat
        self.beat_type = beat_type


    def show(self, indent: int = 0) -> "TimeSignature":
        """Display the TimeSignature information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        TimeSignature
            The TimeSignature instance itself.
        """
        print(" " * indent, f"TimeSignature at {self.onset:0.3f} delta ",
              f"{self.delta:0.3f}: {self.beat}/{self.beat_type}", sep="")
        return self



class KeySignature(Event):
    """KeySignature is a zero-duration Event with keysig info.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        keysig : int, optional
            An integer representing the number of sharps (if positive)
            and flats (if negative), e.g. -3 for Eb major or C minor.
            (Defaults to 0)
        delta : float, optional
            The onset (start) time expressed relative to the
            parent's onset time. (Defaults to 0)

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        duration : float
            Always zero for this subclass.
        delta : float
            The onset (start) time relative to the parent's onset time.
        keysig : int
            An integer representing the number of sharps and flats.
    """

    def __init__(self, parent: Optional["EventGroup"], keysig: int = 0,
                 delta: float = 0):
        super().__init__(parent, 0, delta)
        self.keysig = keysig


    def show(self, indent: int = 0) -> "KeySignature":
        """Display the KeySignature information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        KeySignature
            The KeySignature instance itself.
        """
        print(" " * indent, f"KeySignature at {self.onset:0.3f} delta ",
              f"{self.delta:0.3f}", abs(self.keysig),
              " sharps" if self.keysig > 0 else " flats", sep="")
        return self



@functools.total_ordering
class Pitch:
    """A Pitch represents a symbolic musical pitch. It has two parts:
    The keynum is a number that corresponds to the MIDI convention
    where C4 is 60, C# is 61, etc. The alt is an alteration, where +1
    represents a sharp and -1 represents a flat. Alterations can also
    be, for example, 2 (double-sharp) or -0.5 (quarter-tone flat).
    The symbolic note name is derived by *subtracting* alt from keynum.
    E.g. C#4 has keynum=61, alt=1, so 61-1 gives us 60, corresponding
    to note name C. A Db has the same keynum=61, but alt=-1, and 61-(-1)
    gives us 62, corresponding to note name D. There is no representation
    for the "natural sign" (other than alt=0, which could imply no
    accidental) or "courtesy accidentals."  Because accidentals normally
    "stick" within a measure or are implied by key signatures, accidentals
    are often omitted in the score presentation. Nonetheless, these
    implied accidentals are encoded in the alt field and keynum is the
    intended pitch with the accidental applied.

    Parameters
    ----------
        keynum : float
            MIDI key number, e.g. C4 = 60, generalized to float.
        alt : float, optional
            Alteration, e.g. flat = -1. (Defaults to 0)

    Attributes
    ----------
        keynum : float
            MIDI key number, e.g. C4 = 60, generalized to float.
        alt : float
            Alteration, e.g. flat = -1.
        name : int
            The name of the pitch, e.g. 0, 2, 4, 5, 7, 9, 11.
        name_str : str
            The string representation of the pitch name, including accidentals.
        name_with_octave : str
            The string representation of the pitch name with octave.
        pitch_class : int
            The pitch class of the note
        octave : int
            The octave number of the note, based on keynum.
        enharmonic : Pitch
            The enharmonic equivalent of the pitch.
        upper_enharmonic : Pitch
            The upper enharmonic equivalent of the pitch.
        lower_enharmonic : Pitch
            The lower enharmonic equivalent of the pitch.
    """

    def _fix_alteration(self) -> None:
        """Fix the alteration to ensure it is a valid value, i.e.
        that (keynum - alt) % 12 denotes one of {C D E F G A B}.
        """
        unaltered = self.keynum - self.alt
        if int(unaltered) != unaltered:  # not a whole number
            # fix alt so that unaltered is an integer
            diff = unaltered - round(unaltered)
            self.alt -= diff
            unaltered = round(self.keynum - self.alt)
        # make sure pitch class of unaltered is in {C D E F G A B}
        pc = unaltered % 12
        if pc in [6, 1]:  # F#->F, C#->C
            self.alt += 1
        elif pc in [10, 3, 8]:  # Bb->B, Eb->E, Ab->A
            self.alt -= 1
        # now (keynum + alt) % 12 is in {C D E F G A B}


    def __init__(self, keynum: float, alt: float = 0):
        self.keynum = keynum
        self.alt = alt
        self._fix_alteration()

    def astuple(self):
        """Return a tuple representation of the Pitch instance.

        Returns
        -------
        tuple
            A tuple containing the keynum and alt values.
        """
        return (self.keynum, self.alt)


    def __eq__(self, other):
        """Check equality of two Pitch instances. Pitches are equal if
        both keynum and alteration are equal. Enharmonics are therefore
        not equal, but enharmonic equivalence can be written simply as
        p1.keynum == p2.keynum

        Parameters
        ----------
        other : Pitch
            The other Pitch instance to compare with.

        Returns
        -------
        bool
            True if the keynum and alt values are equal, False otherwise.
        """
        return self.astuple() == other.astuple()


    def __hash__(self) -> int:
        """Return a hash value for the Pitch instance.

        Returns
        -------
        int
            A hash value representing the Pitch instance.
        """
        return hash(self.astuple())


    def __lt__(self, other) -> bool:
        """Check if this Pitch instance is less than another Pitch instance.
        Pitches are compared first by keynum and then by alt. Pitches
        with sharps (i.e. positive alt) are considered lower because
        their letter names are lower in the musical alphabet.

        Parameters
        ----------
        other : Pitch
            The other Pitch instance to compare with.

        Returns
        -------
        bool
            True if this Pitch instance is less than the other, False otherwise.
        """
        return (self.keynum, -self.alt) < (other.keynum, -other.alt)


    @property
    def name(self) -> int:
        """Retrieve the name of the pitch, e.g. 0, 2, 4, 5, 7, 9, 11,
        corresponding to letter names without accidentals.

        Returns
        -------
        int
            The name of the pitch, e.g. 0, 2, 4, 5, 7, 9, 11.
        """
        return (self.keynum - self.alt) % 12


    @property
    def name_str(self) -> str:
        """Return string name including accidentals (# or -) if alt is integral.

        Returns
        -------
        str
            The string representation of the pitch name, including accidentals.
        """
        unaltered = round(self.keynum - self.alt)
        base = ["C", "?", "D", "?", "E", "F", "?", "G", "?", "A", "?", "B"][
            unaltered % 12
        ]
        accidentals = "?"
        if round(self.alt) == self.alt:  # an integer value
            if self.alt > 0:
                accidentals = "#" * self.alt
            elif self.alt < 0:
                accidentals = "b" * -self.alt
            else:
                accidentals = ""  # natural
        return base + accidentals


    @property
    def name_with_octave(self) -> str:
        """Return string name with octave, e.g. C4, B#3, etc.
        The octave number is calculated by subtracting 1 from the
        integer division of keynum by 12. The octave number is
        independent of enharmonics. E.g. C4 is enharmonic to B#3 and
        represent the same (more or less) pitch, but BOTH have an
        octave of 4. On the other hand name_str() will return "C4"
        and "B#3", respectively.

        Returns
        -------
        str
            The string representation of the pitch name with octave.
        """
        unaltered = round(self.keynum - self.alt)
        octave = (unaltered // 12) - 1
        return self.name_str + str(octave)


    @property
    def pitch_class(self) -> int:
        """Retrieve the pitch class of the note, e.g. 0, 1, 2, ..., 11.
        The pitch class is the keynum modulo 12, which gives the
        equivalent pitch class in the range 0-11.

        Returns
        -------
        int
            The pitch class of the note.
        """
        return self.keynum % 12


    @pitch_class.setter
    def pitch_class(self, pc: int) -> None:
        """Set the pitch class of the note.

        Parameters
        ----------
        pc : int
            The new pitch class value.
        """
        self.keynum = (self.octave + 1) * 12 + pc % 12
        self._fix_alteration()


    @property
    def octave(self) -> int:
        """Returns the octave number based on keynum. E.g. C4 is enharmonic
        to B#3 and represent the same (more or less) pitch, but BOTH have an
        octave of 4. On the other hand name_str() will return "C4" and "B#3",
        respectively.
        """
        return floor(self.keynum) // 12 - 1


    @octave.setter
    def octave(self, oct: int) -> None:
        """Set the octave number of the note.

        Parameters
        ----------
        oct : int
            The new octave number.
        """
        self.keynum = (oct + 1) * 12 + self.pitch_class


    def enharmonic(self):
        """If alt is non-zero, return a Pitch where alt is zero
        or has the opposite sign and where alt is minimized. E.g.
        enharmonic(C-double-flat) is A-sharp (not B-flat). If alt
        is zero, return a Pitch with alt of +1 or -1 if possible.
        Otherwise, return a Pitch with alt of -2.

        Returns
        -------
        Pitch
            A Pitch object representing the enharmonic equivalent.
        """
        alt = self.alt
        unaltered = round(self.keynum - alt)
        if alt < 0:
            while alt < 0 or (unaltered % 12) not in [0, 2, 4, 5, 7, 9, 11]:
                unaltered -= 1
                alt += 1
        elif alt > 0:
            while alt > 0 or (unaltered % 12) not in [0, 2, 4, 5, 7, 9, 11]:
                unaltered += 1
                alt -= 1
        else:  # alt == 0
            unaltered = unaltered % 12
            if unaltered in [0, 5]:  # C->B#, F->E#
                alt = 1
            elif unaltered in [11, 4]:  # B->Cb, E->Fb
                alt = -1
            else:  # A->Bbb, D->Ebb, G->Abb
                alt = -2
        return Pitch(self.keynum, alt=alt)


    def upper_enharmonic(self) -> "Pitch":
        """Return a valid Pitch with alt decreased by 1 or 2, e.g. C#->Db,
        C##->D, C###->D#

        Returns
        -------
        Pitch
            A Pitch object representing the upper enharmonic equivalent.
        """
        alt = self.alt
        unaltered = round(self.keynum - alt) % 12
        if unaltered in [0, 2, 4, 7, 9]:  # C->D, D->E, F->G, G->A, A->B
            alt -= 2
        else:  # E->F, B->C
            alt -= 1
        return Pitch(self.keynum, alt=alt)


    def lower_enharmonic(self):
        """Return a valid Pitch with alt increased by 1 or 2, e.g. Db->C#,
        D->C##, D#->C###

        Returns
        -------
        Pitch
            A Pitch object representing the lower enharmonic equivalent.
        """
        alt = self.alt
        unaltered = round(self.keynum - alt) % 12
        if unaltered in [2, 4, 7, 9, 11]:  # D->C, E->D, G->F, A->G, B->A
            alt += 2
        else:  # F->E, C->B
            alt += 1
        return Pitch(self.keynum, alt=alt)


class EventGroup(Event):
    """An EventGroup is a collection of Event objects. This is an abstract
    class. Use one of the subclasses: Score, Part, Staff, Measure or Chord.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
    """

    def __init__(self,
                 parent: Optional["EventGroup"],
                 delta: float,
                 duration: float):
        super().__init__(parent, duration, delta)
        self.content = []


    def convert_to_seconds(self, parent_onset_beat: float, 
                           parent_onset_time: float, time_map: TimeMap) -> None:
        """Convert the event's duration and delta to seconds using the
        provided TimeMap. Convert content as well.

        Parameters
        ----------
        parent_onset_beat : float
            The parent's onset time in beats.
        parent_onset_time : float
            The parent's onset time in seconds.
        time_map : TimeMap
            The TimeMap object used for conversion.
        """
        onset_beat = parent_onset_beat + self.delta
        onset_time = time_map.seconds(onset_beat)
        offset_time = time_map.seconds(onset_beat + self.duration)
        self.delta = onset_time - parent_onset_time
        self.duration = offset_time - onset_time
        for elem in self.content:
            elem.convert_to_seconds(onset_beat, onset_time, time_map)


    def show(self, indent: int = 0, label: str = "EventGroup") -> "EventGroup":
        """Display the EventGroup information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)
        label : str, optional
            The label for the EventGroup. (Defaults to "EventGroup")

        Returns
        -------
        EventGroup
            The EventGroup instance itself.
        """
        print(" " * indent, label, f" at {self.onset:0.3f} delta ",
              f"{self.delta:0.3f} duration {self.duration:0.3f}", sep="")
        for elem in self.content:
            elem.show(indent + 4)
        return self


    @property
    def last(self) -> Optional[Event]:
        """Retrieve the last event in the content list.

        Returns
        -------
        Optional[Event]
            The last event in the content list or None if the list is empty.
        """
        return self.content[-1] if len(self.content) > 0 else None


    def emptycopy_into(self, parent: Optional["EventGroup"]) -> "EventGroup":
        """Create an empty shallow copy of the EventGroup and set its parent.

        Parameters
        ----------
        parent : Optional[EventGroup]
            The new parent to insert the copied Event into.

        Returns
        -------
        EventGroup
            A copy of the EventGroup instance with the new parent.
        """
        # rather than customize __copy__, we "hide" the content to avoid
        # copying it. Then we restore it after copying and fix parent.
        original_content = self.content
        self.content = None
        c = self.copy()
        self.content = original_content
        c.content = []  # change None to (valid) empty content
        c.parent = None  # copy is not a member of self
        if parent:
            parent.insert(c)
        return c


    def find_all(self, elem_type: Type[Event]) -> Generator[Event, None, None]:
        """Find all instances of a specific type within the EventGroup.
        Assumes that objects of type `elem_type` are not nested within
        other objects of the same type.

        Parameters
        ----------
        elem_type : Type[Event]
            The type of event to search for.

        Yields
        -------
        Event
            Instances of the specified type found within the EventGroup.
        """
        # Algorithm: depth-first enumeration of EventGroup content.
        # If elem_types are nested, only the top-level elem_type is
        # returned since it is found first, and the content is not
        # searched. This makes it efficient, e.g., to search for
        # Parts in a Score without enumerating all Notes within.
        for elem in self.content:
            if isinstance(elem, elem_type):
                yield elem
            elif isinstance(elem, EventGroup):
                yield from elem.find_all(elem_type)


    def has_instanceof(self, the_class: Type[Event]) -> bool:
        """Test if EventGroup (e.g. Score, Part, Staff, Measure) contains any
        instances of the_class.

        Parameters
        ----------
        the_class : Type[Event]
            The class type to check for.

        Returns
        -------
        bool
            True iff the EventGroup contains an instance of the_class.
        """
        instances = self.find_all(the_class)
        # if there are no instances (of the_class), next will return "empty":
        return next(instances, "empty") != "empty"


    def has_rests(self) -> bool:
        """Test if EventGroup (e.g. Score, Part, Staff, Measure) has any
        Rest objects.

        Returns
        -------
        bool
            True iff the EventGroup contains any Rest objects.
        """
        return self.has_instanceof(Rest)


    def has_chords(self) -> bool:
        """Test if EventGroup (e.g. Score, Part, Staff, Measure) has any
        Chord objects.

        Returns
        -------
        bool
            True iff the EventGroup contains any Chord objects.
        """
        return self.has_instanceof(Chord)


    def has_ties(self) -> bool:
        """Test if EventGroup (e.g. Score, Part, Staff, Measure) has any
        tied notes.

        Returns
        -------
        bool
            True iff the EventGroup contains any tied notes.
        """
        notes = self.find_all(Note)
        for note in notes:
            if note.tie:
                return True
        return False


    def has_measures(self) -> bool:
        """Test if EventGroup (e.g. Score, Part, Staff) has any measures.

        Returns
        -------
        bool
            True iff the EventGroup contains any Measure objects.
        """
        return self.has_instanceof(Measure)


    def remove_rests(self, new_parent: "EventGroup" = None) -> "EventGroup":
        """Remove all Rest objects. Returns a deep copy with no parent,
        unless new_parent is provided.

        Parameters
        ----------
        new_parent : EventGroup, optional
            The new parent to insert the copied Event into. (Defaults to None)

        Returns
        -------
        EventGroup
            A deep copy of the EventGroup instance with all Rest objects removed.
        """
        # implementation detail: when called without argument, remove_rests
        # makes a deep copy of the subtree and returns the copy without a
        # parent. remove_rests calls itself recursively *with* a parameter
        # indicating that the subtree copy should be inserted into a
        # parent which is the new copy at the next level up. Of course,
        # we check for and ignore Rests so they are never copied.
        group = self.emptycopy_into(new_parent)
        for item in self.content:
            if isinstance(item, Rest):
                continue  # skip the Rests while making deep copy
            if isinstance(item, EventGroup):
                item.remove_rests(group)  # recursion for deep copy
            else:
                item.deepcopy_into(group)  # deep copy non-EventGroup
        return group


    def expand_chords(self, new_parent: "EventGroup" = None) -> "EventGroup":
        """Replace chords with the multiple notes they contain.
        Returns a deep copy with no parent unless new_parent is provided.

        Parameters
        ----------
        new_parent : EventGroup, optional
            The new parent to insert the copied Event into. (Defaults to None)

        Returns
        -------
        EventGroup
            A deep copy of the EventGroup instance with all
            Chord instances expanded.
        """
        group = self.emptycopy_into(new_parent)
        for item in self.content:
            if isinstance(item, Chord):
                for note in item.content:  # expand chord
                    note_copy = note.deepcopy_into(None)
                    # add chord's delta to note's delta to get correct delta
                    note_copy.delta += item.delta
                    group.insert(note_copy)
            if isinstance(item, EventGroup):
                item.expand_chords(group)  # recursion for deep copy/expand
            else:
                item.deepcopy_into(group)  # deep copy non-EventGroup
        return group
    

    def inherit_duration(self) -> "EventGroup":
        """Set the duration of this EventGroup to the maximum duration
        of its children. If the EventGroup is empty, the duration
        is set to 0. This method modifies the EventGroup instance.

        Returns
        -------
        EventGroup
            The EventGroup instance (self) with updated duration.
        """
        for elem in self.content:
            self.duration = max(self.duration, elem.delta_offset)
        return self


    def insert(self, event: Event) -> "EventGroup":
        """Insert an event without any changes to event.delta or
        self.duration. If the event is out of order, insert it just before
        the first element with a greater delta. The method modifies this
        object (self).

        Parameters
        ----------
        event : Event
            The event to be inserted.

        Returns
        -------
        EventGroup
            The EventGroup instance (self) with the event inserted.
        """
        assert not event.parent
        if self.last and event.delta < self.last.delta:
            # search in reverse from end
            i = len(self.content) - 2
            while i >= 0 and self.content[i].delta > event.delta:
                i -= 1
            # now i is either -1 or content[i] <= event.delta, so
            # insert event at content[i+1]
            self.content.insert(i + 1, event)
        else:  # simply append at the end of content:
            self.content.append(event)
        event.parent = self
        return self
    

    def list_all(self, elem_type: Type[Event]) -> list[Event]:
        """Find all instances of a specific type within the EventGroup.
        Assumes that objects of type `elem_type` are not nested within
        other objects of the same type.

        Parameters
        ----------
        elem_type : Type[Event]
            The type of event to search for.

        Returns
        -------
        list[Event]
            A list of all instances of the specified type found
            within the EventGroup.
        """
        return list(self.find_all(elem_type))


    def remove(self, element: Event) -> "EventGroup":
        """Remove an element from the content list. The method modifies
        this object (self).

        Parameters
        ----------
        element : Event
            The event to be removed.

        Returns
        -------
        EventGroup
            The EventGroup instance (self) with the element removed.
            The returned value is not a copy.
        """
        self.content.remove(element)
        return self



class Sequence(EventGroup):
    """Sequence represents a temporal sequence of music events.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float, optional
            The onset (start) time expressed relative to the
            parent's onset time. (Defaults to 0)
        duration : float, optional
            The duration in quarters or seconds. (Defaults to None)

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
    """

    def __init__(self,
                 parent: EventGroup,
                 delta: float = 0,
                 duration: float = 0):
        """Sequence represents a temporal sequence of music events.
        duration(ation) defaults to 0.
        """
        super().__init__(parent, delta, duration)


    def show(self, indent: int = 0, label: str = "Sequence") -> "Sequence":
        """Display the Sequence information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)
        label : str, optional
            The label for the Sequence. (Defaults to "Sequence")

        Returns
        -------
        Sequence
            The Sequence instance itself.
        """
        return super().show(indent, label)


    @property
    def last_offset(self):
        """return the offset (end) time of the last element,
        or the onset (start) time if the Sequence is empty
        """
        if len(self.content) == 0:
            return self.onset
        else:
            return self.last.last_offset


    @property
    def last_delta_offset(self):
        """return the offset (in quarters) of the last element relative to
        the Sequence onset (start) time, or 0 if the Sequence is empty
        """
        if len(self.content) == 0:
            return 0
        else:
            return self.last.last_delta_offset


    # def append(self, element, delta=None, update_duration=True):
    #     """Append an element. If delta is specified, the element is
    #     modified to start at this delta, and the duration of self
    #     is unchanged. If delta is not specified or None, the element
    #     delta is changed to the duration(ation) of self, which is then
    #     incremented by the duration of element.

    #     Parameters
    #     ----------
    #     element : Event
    #         The event to be appended.
    #     delta : float, optional
    #         The delta time to set for the element. (Defaults to element.delta)
    #     update_duration : bool, optional
    #         Whether to update the duration of self. (Defaults to True)
    #     """
    #     if delta is None:
    #         element.delta = self.duration
    #         if update_duration:
    #             self.duration += element.duration
    #     else:
    #         element.delta = delta
    #     self.insert(element)  # places element in order and sets element parent


    def pack(self):
        """Adjust the content to be sequential, with zero delta for the
        first element, and each other object at an delta equal to the
        delta_offset of the previous element. The duration(ation) of
        self is set to the delta_offset of the last element. This method
        essentially, arranges the content to eliminate gaps. pack()
        works recursively on elements that are EventGroups.
        """
        delta = 0
        for elem in self.content:
            elem.delta = 0
            if isinstance(elem, EventGroup):
                elem.pack()
            delta += elem.duration


class Concurrence(EventGroup):
    """Concurrence represents a temporally simultaneous collection
    of music events (but if elements have a non-zero delta, a Concurrence
    can represent events organized over time).  Thus, the main distinction
    between Concurrence and Sequence is the behavior of methods, since both
    classes can represent simultaneous or sequential events.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float, optional
            The onset (start) time expressed relative to the parent's
            onset time. (Defaults to 0)
        duration : float, optional
            The duration in quarters or seconds. (Defaults to None)

    Attributes
    ---------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
    """

    def __init__(self,
                 parent: Optional[EventGroup],
                 delta: float = 0,
                 duration: float = None):
        """duration defaults 0
        """
        super().__init__(parent, delta, duration)


    def show(self, indent=0, label="Concurrence") -> "Concurrence":
        """Display the Concurrence information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)
        label : str, optional
            The label for the Concurrence. (Defaults to "Concurrence")

        Returns
        -------
        Concurrence
            The Concurrence instance itself.
        """
        return super().show(indent, label)

    def pack(self):
        """Adjust the content to deltas of zero. The duration(ation) of self
        is set to the maximum delta_offset of the elements. This method
        essentially, arranges the content to eliminate gaps. pack() works
        recursively on elements that are EventGroups.
        """
        self.duration = 0
        for elem in self.content:
            elem.delta = 0
            if isinstance(elem, EventGroup):
                elem.pack()
            self.duration = max(self.duration, elem.duration)

    # def append(self, element: Event, delta: float = 0, update_duration: bool = True):
    #     """Append an element to the content with the given delta.
    #     (Specify delta=element.delta to retain the element's delta.)  By
    #     default, the duration(ation) of self is increased to the
    #     delta_offset of element if the delta_offset is greater than the
    #     current duration(ation). To retain the duration(ation) of self,
    #     specify update_duration=False.

    #     Parameters
    #     ----------
    #     element : Event
    #         The event to be appended.
    #     delta : float, optional
    #         The delta time to set for the element. (Defaults to 0)
    #     update_duration : bool, optional
    #         Whether to update the duration of self. (Defaults to True)
    #     """
    #     element.delta = delta
    #     self.insert(element)
    #     if update_duration:
    #         self.duration = max(self.duration, element.delta_offset)


class Chord(Concurrence):
    """A Chord is a collection of Notes, normally with deltas of zero
    and the same durations and distinct keynums, but this is not
    enforced.  The order of notes is arbitrary. Normally, a Chord is a
    member of a Staff. There is no requirement that simultaneous or
    overlapping notes be grouped into Chords, so the Chord class is
    merely an optional element of music structure representation.
    Representation note: An alternative representation would be to
    subclass Note and allow a list of pitches, which has the advantage
    of enforcing the shared deltas and durations. However, there can be
    ties connected differently to each note within the Chord, thus we
    use a Concurrence with Note objects as elements. Each Note.tie can
    be different.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float, optional
            The onset (start) time expressed relative to the parent's
            onset time. (Defaults to 0)
        duration : float, optional
            The duration in quarters or seconds. (Defaults to None)
        content : list[Event], optional
            Elements contained within this collection. (Defaults to [])

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
    """

    def show(self, indent: int = 0) -> "Chord":
        """Display the Chord information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Chord
            The Chord instance itself.
        """
        return super().show(indent, "Chord")

    def is_measured(self):
        """Test if Chord is well-formed. Conforms to strict hierarchy of:
        Chord-Note
        """
        for note in self.content:
            # Chord can contain many object types, so we can only rule
            # out things that are outside of the strict hierarchy:
            if isinstance(note, (Score, Part, Staff, Measure, Rest, Chord)):
                return False
        return True


class Measure(Sequence):
    """A Measure models a musical measure (bar) and can contain many object
    types including Note, Rest, Chord, KeySignature, Timesignature. Measures
    are elements of a Staff.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        number : Union[str, None], optional
            A string representing the measure number. (Defaults to None)
        delta : float, optional
            The onset (start) time relative to the parent's onset time. (Defaults to 0)
        duration : float, optional
            The duration in quarters or seconds. (Defaults to 4)
        content : list[Event], optional
            Elements contained within this collection. (Defaults to [])

    Attributes
    -----------
        number : Union[str, None]
            A string representing the measure number (if any). E.g. "22a".
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
    """

    def __init__(self,
                 parent: Optional[EventGroup],
                 number: Optional[str] = None,
                 delta: float = 0,
                 duration: float = 4):
        super().__init__(parent, delta, duration)
        self.number = number


    def show(self, indent: int = 0) -> "Measure":
        """Display the Measure information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Measure
            The Measure instance itself.
        """
        nstr = " " + str(self.number) if self.number else ""
        return super().show(indent, "Measure" + nstr)


    def is_measured(self) -> bool:
        """Test if Measure is well-formed: Conforms to strict hierarchy of:
        Measure-(Note or Rest or Chord) and Chord-Note

        Returns
        -------
        bool
            True if the Measure is well-formed, False otherwise.
        """
        for item in self.content:
            # Measure can contain many object types, so we can only rule
            # out things that are outside of the strict hierarchy:
            if isinstance(item, (Score, Part, Staff, Measure)):
                return False
            if isinstance(item, Chord) and not item.is_measured():
                return False
        return True


def note_onset(note: Note) -> float:
    """helper function to sort notes

    Parameters
    ----------
    note : Note
        The note whose onset time is to be retrieved.

    Returns
    -------
    float
        The onset time of the note.
    """
    return note.onset


class Score(Concurrence):
    """A score is a top-level object representing a musical work.
    Normally, a Score contains Part objects, all with delta zero.

    Parameters
    ----------
        delta : float, optional
            The onset (start) time expressed relative to the
            parent's onset time. (Defaults to 0)
        duration : float, optional
            The duration in quarters or seconds. (Defaults to 0)
        content : list[Event], optional
            Elements contained within this collection. (Defaults to [])
        time_map : TimeMap, optional
            A map from quarters to seconds (or seconds to quarters). (Defaults to None)

    Attributes
    ----------
        delta : float
            The onset (start) time expressed relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
        time_map : TimeMap
            A map from quarters to seconds (or seconds to quarters).

    Additional attributes may be assigned, e.g. 'title', 'source_file',
    'composer', etc.
    """

    def __init__(self,
                 delta: float = 0,
                 duration: float = 0,
                 time_map: Optional["TimeMap"] = None):
        super().__init__(None, delta, duration)  # score parent is None
        self.time_map = time_map if time_map else TimeMap()


    def emptycopy(self) -> "Score":
        """Construct a shallow copy of a score with emptied content
        For scores, this is preferable to self.emptycopy_into(None)

        Returns
        -------
        Score
            A shallow copy of the Score instance with emptied content.
        """
        return self.emptycopy_into(None)


    def deepcopy(self) -> "Score":
        """Return a deep copy of the Score instance. Note that Part, Staff,
        Measure, and Chord objects use deepcopy_into() to copy their content
        rather than deepcopy() to encourage their attachment to a parent.
        Scores do not have a parent.

        Returns
        -------
        Score
            A deep copy of the Score instance.
        """
        return copy.deepcopy(self)


    @classmethod
    def from_melody(cls,
                    pitches: list[Union[int, Pitch]],
                    durations: Union[float, list[float]] = 1.0,
                    iois: Optional[Union[float, list[float]]] = None,
                    deltas: Optional[list[float]] = None) -> "Score":
        """Create a Score from a melody specified as a list of pitches
        and optional timing information.

        Parameters
        ----------
        pitches : list of int or list of Pitch
            MIDI note numbers or Pitch objects for each note.
        durations : float or list of float
            Durations for each note. If a scalar value, it will be repeated
            for all notes. Defaults to 1.0 (quarter notes).

        iois : float or list of float or None, optional Inter-onset
            intervals between successive notes. If a scalar value,
            it will be repeated for all notes. If not provided and
            deltas is None, takes values from the durations argument,
            assuming that notes are placed sequentially without overlap.

        deltas : list of float or None, optional
            Start times relative to the melody's start. Cannot be used together
            with iois. If both are None, defaults to using durations as IOIs.

        Returns
        -------
        Score
            A new Score object containing the melody in a single part.
            If pitches is empty, returns a score with an empty part.

        Examples
        --------
        Create a simple C major scale with default timing (sequential quarter notes):

        >>> score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])  # all quarter notes
        >>> notes = score.content[0].content
        >>> len(notes)  # number of notes in first part
        8
        >>> notes[0].pitch.keynum
        60
        >>> score.duration  # last note ends at t=8
        8.0

        Create three notes with varying durations:

        >>> score = Score.from_melody(
        ...     pitches=[60, 62, 64],  # C4, D4, E4
        ...     durations=[0.5, 1.0, 2.0],
        ... )
        >>> score.duration  # last note ends at t=3.5
        3.5

        Create three notes with custom IOIs:

        >>> score = Score.from_melody(
        ...     pitches=[60, 62, 64],  # C4, D4, E4
        ...     durations=1.0,  # quarter notes
        ...     iois=2.0,  # 2 beats between each note onset
        ... )
        >>> score.duration  # last note ends at t=5
        5.0

        Create three notes with explicit deltas:

        >>> score = Score.from_melody(
        ...     pitches=[60, 62, 64],  # C4, D4, E4
        ...     durations=1.0,  # quarter notes
        ...     deltas=[0.0, 2.0, 4.0],  # onset times 2 beats apart
        ... )
        >>> score.duration  # last note ends at t=5
        5.0
        """
        if len(pitches) == 0:
            return cls._from_melody(pitches=[], deltas=[], durations=[])

        if iois is not None and deltas is not None:
            raise ValueError("Cannot specify both iois and deltas")

        # Convert scalar durations to list
        if isinstance(durations, (int, float)):
            durations = [float(durations)] * len(pitches)

        # If deltas are provided, use them directly
        if deltas is not None:
            if len(deltas) != len(pitches):
                raise ValueError("deltas list must have same length as pitches")
            deltas = [float(d) for d in deltas]

        # Otherwise convert IOIs to deltas
        else:
            # If no IOIs provided, use durations as default IOIs
            if iois is None:
                iois = durations[:-1]  # last duration not needed for IOIs
            # Convert scalar IOIs to list
            elif isinstance(iois, (int, float)):
                iois = [float(iois)] * (len(pitches) - 1)

            # Validate IOIs length
            if len(iois) != len(pitches) - 1:
                raise ValueError("iois list must have length len(pitches) - 1")

            # Convert IOIs to deltas
            deltas = [0.0]  # first note onsets at 0
            current_time = 0.0
            for ioi in iois:
                current_time += float(ioi)
                deltas.append(current_time)

        if not (len(pitches) == len(deltas) == len(durations)):
            raise ValueError("All input lists must have the same length")

        return cls._from_melody(pitches, deltas, durations)


    def collapse_parts(self, part=None, staff=None, has_ties=True):
        """merge the notes of selected Parts and Staffs into a flattened
        score with only one part, retaining only Notes. If you are using
        this method to extract notes by Staff, you can save some
        computation by performing a one-time score = score.merge_tied_notes()
        and providing the parameter has_ties=False. If has_ties is False,
        it is assumed without checking that part.has_ties() is False,
        allowing this method to skip calls to part.merge_tied_notes()
        for each selected part.

        If part is given, only notes from the selected part are included.
        part may be an integer to match a part number
        part may be a string to match a part instrument
        part may be a list with an index, e.g. [3] will select
        the 4th part (because indexing is zero-based)
        If staff is given, only the notes from selected staves are included.
        staff may be an integer to match a staff number
        staff may be a list with an index, e.g. [1] will select
        the 2nd staff.
        If staff is given without a part specification, an exception
        is raised.
        If staff is given and this is a flattened score (no staves),
        an exception is raised.
        Note: The use of the form [1] for part and staff index notation
        is not ideal, but we need to distinguish between part numbers
        (arbitrary labels) and part index. Initially, I used tuples,
        but they are error prone. E.g. part=(0) means part=0, so you
        have to write keynum_list(part=((0))). With [n], you write
        keynum_list(part=[0]) to indicate an index. This is
        prettier and less prone to error.
        """
        # Algorithm: Since we might be selecting individual Staffs and
        # Parts, we want to do selection first, then copy to avoid
        # modifying the source Score (self).
        content = []  # collect selected Parts/Staffs here
        score = self.emptycopy()
        parts = self.find_all(Part)
        for i, p in enumerate(parts):
            if (part is None
                or (isinstance(part, int) and part == p.number)
                or (isinstance(part, str) and part == p.instrument)
                or (isinstance(part, list) and part[0] == i)):
                # merging tied notes takes place at the Part level because
                # notes can be tied across Staffs.
                if has_ties:
                    # put parts into score copy to allow onset computation
                    # later, we will merge notes and remove these parts
                    p = p.merge_tied_notes(score)

                if staff is None:  # no staff selection, use whole Part
                    content.append(p)
                else:  # must find Notes in selected Staffs
                    staffs = p.find_all(Staff)
                    for i, s in enumerate(staffs):
                        if (staff is None
                            or (isinstance(staff, int) and staff == s.number)
                            or (isinstance(staff, list) and staff[0] == i)):
                            content.append(s)
        # now content is a list of Parts or Staffs to merge
        notes = []
        for part_or_staff in content:  # works with both Part and Score:
            notes += part_or_staff.list_all(Note)
        new_part = Part(score)
        if not has_ties:
            # because we avoided merging ties in parts, notes still belong
            # to the original score (self), so we need to copy them:
            copies = []  # copy all notes to here
            for note in notes:
                # rather than a possibly expensive insert into new_part, we
                # retain the old parent and use sort (below) to construct
                # the content of new_part. If parent is None, the delta will
                # be retained, so by temporarily plugging in note.parent as
                # the note_copy.parent, we insure that note_copy.onset will
                # equal note.onset; we need that later to properly set the
                # final note_copy.delta (see below):
                note_copy = note.deepcopy_into(parent=None)
                note_copy.parent = note.parent
                copies.append(note_copy)
            notes = copies
        # notes can be modified, so reuse them in the new_part:
        for note in notes:
            # it is possible we are moving the note from a Part or Staff with
            # a non-zero offset, so recompute the note.delta to preserve onset
            # time under the new parent (new_part, which has delta=0,
            # and therefore onset=score.delta):
            note.delta = note.onset - score.delta
            note.parent = new_part
        notes.sort(key=lambda x: x.delta)
        new_part.content = notes
        # remove all the parts that we merged, leaving only new_part
        score.content = [new_part]
        return score


    def flatten(self, collapse=False):
        """Deep copy notes in a score to a flattened score consisting of
        only Parts containing Notes. If collapse is True, multiple parts are
        collapsed into a single part, and notes are ordered according to
        onset times. Tied notes are merged unless keep_ties is True.
        """
        score = self.merge_tied_notes()  # also copies score
        # it is now safe to modify score because it has been copied
        if collapse:  # similar to Part.flatten() but we have to sort and
            # do some other extra work to put all notes into score
            new_part = Part(score)
            notes = score.list_all(Note)  # force iterator into list to sort
            score.content = [new_part]  # remove all other parts and events

            # adjust deltas for new parent: new_part will have delta = 0,
            # so note deltas will be relative to score.offset (which is
            # probably 0 too, but not required):
            for note in notes:
                note.delta = note.onset - score.delta
                note.parent = new_part
            # notes with equal onset times are sorted in pitch from high to low
            notes.sort(key=lambda x: (x.delta, -note.pitch.keynum))
            new_part.content = notes  # content will have only Notes

            # set the Part duration so it ends at the max offset of all Parts:
            offset = max((part.offset for part in self.find_all(Part)), default=0)
            new_part.duration = offset - score.delta

        else:  # flatten each part separately
            for part in score.find_all(Part):
                part.flatten(in_place=True)
        return score


    @classmethod
    def _from_melody(cls,
                     pitches: list[Union[int, Pitch]],
                     deltas: list[float],
                     durations: list[float]) -> "Score":
        """Helper function to create a Score from preprocessed lists of pitches,
        deltas, and durations.

        All inputs must be lists of the same length, with numeric values already
        converted to float.
        """
        if not (len(pitches) == len(deltas) == len(durations)):
            raise ValueError("All inputs must be lists of the same length")
        if not all(isinstance(x, float) for x in deltas):
            raise ValueError("All deltas must be floats")
        if not all(isinstance(x, float) for x in durations):
            raise ValueError("All durations must be floats")

        # Check for overlapping notes
        for i in range(len(deltas) - 1):
            current_end = deltas[i] + durations[i]
            next_onset = deltas[i + 1]
            if current_end > next_onset:
                raise ValueError(
                    f"Notes overlap: note {i} ends at {current_end:.2f} but note {i + 1} starts at {next_onset:.2f}"
                )

        score = cls()
        part = Part(score)

        # Create notes and add them to the part
        for pitch, delta, duration in zip(pitches, deltas, durations):
            if not isinstance(pitch, Pitch):
                pitch = Pitch(pitch)
            note = Note(part, duration=duration, pitch=pitch, delta=delta)

        # Set the score duration to the end of the last note
        if len(deltas) > 0:
            score.duration = float(
                max(delta + duration for delta, duration in zip(deltas, durations))
            )
        else:
            score.duration = 0.0

        return score


    def is_flat(self):
        """Test if Score is flat. Conforms to strict hierarchy of:
        Score-Part-Note with no tied notes.
        """
        for part in self.content:
            # only Parts are expected, but things outside of the hierarchy
            # are allowed, so we only rule out violations of the hierarchy:
            if isinstance(part, (Score, Staff, Measure, Note, Rest, Chord)):
                return False
            if isinstance(part, Part) and not part.is_flat():
                return False
        return True


    def is_flat_and_collapsed(self):
        """Determine if score has been flattened into one part"""
        return self.part_count() == 1 and self.is_flat()


    def is_measured(self) -> bool:
        """Test if Score is measured. Conforms to strict hierarchy of:
        Score-Part-Staff-Measure-(Note or Rest or Chord) and Chord-Note.

        Returns
        -------
        bool
            True if the Score is measured, False otherwise.
        """
        for part in self.content:
            # only Parts are expected, but things outside of the hierarchy
            # are allowed, so we only rule out violations of the hierarchy:
            if isinstance(part, (Score, Staff, Measure, Note, Rest, Chord)):
                return False
            if isinstance(part, Part) and not part.is_measured():
                return False
        return True


    def merge_tied_notes(self) -> "Score":
        """Create a new Score with tied note sequences replaced by
        equivalent notes

        Returns
        -------
        Score
            A new Score instance with tied notes merged.
        """
        score = self.emptycopy()
        for part in self.content:
            if isinstance(part, Part):
                part.merge_tied_notes(score)
            else:
                part.deepcopy_into(score)
        return score


    def note_containers(self):
        """Returns a list of non-empty note containers. For Measured Scores,
        these are the Staff objects. For Flat Scores, these are the Part
        objects. This is mainly useful for extracting note sequences where
        each staff represents a separate sequence. In a Flat Score,
        staves are collapsed and each Part (instrument) represents a
        separate sequence. This implementation also handles a mix of
        Parts with and without Staffs, returning a list of whichever
        is the direct parent of a list of Notes.
        """
        containers = []
        # start with parts, which are common to both measured scores and
        # flat scores. If the Part has a Staff, the Staffs are the
        # containers we want. If the Part has a Note, the Part itself is
        # the container. Other event classes can exist and are ignored.
        for part in self.find_all(Part):
            for event in part.content:
                if isinstance(event, Staff):
                    containers += part.list_all(Staff)
                    break
                elif isinstance(event, Note):
                    containers.append(part)
                    break
            # if part was empty, it is not added to containers
        return containers


    def part_count(self):
        """How many parts are in this score?"""
        return len(self.list_all(Part))


    def remove_measures(self) -> "Score":
        """Create a new Score with all Measures removed, but preserving
        Staffs in the hierarchy. Notes are "lifted" from Measures to become
        direct content of their Staff. The result satisfies neither is_flat()
        nor is_measured(), but it could be useful in preserving a
        separation between staves. See also ``collapse_parts()``, which
        can be used to extract individual staves from a score. The result
        will have ties merged. (If you want to preserve ties and access
        the notes in a Staff, consider using find_all(Staff), and then
        for each staff, find_all(Note), but note that ties can cross
        between staves.)

        Returns
        -------
        Score
            A new Score instance with all Measures removed.
        """
        score = self.emptycopy()
        for part in self.content:
            if isinstance(part, Part):
                part = part.merge_tied_notes(score)
                part.remove_measures(score, has_ties=False)
            else:  # non-Part objects are simply copied
                part.deepcopy_into(score)
        return score


    def show(self, indent: int = 0) -> "Score":
        """Display the Score information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Score
            The Score instance itself.
        """

        print(" " * indent, f"Score at {self.onset:0.3f} delta ",
              f"{self.delta:0.3f} duration {self.duration:0.3f}", sep="")
        self.time_map.show(indent + 4)
        for elem in self.content:
            elem.show(indent + 4)
        return self


    def sorted_notes(self):
        """Return a list of sorted notes with merged ties"""
        # score will have one Part, content of which is all Notes:
        return self.flatten(collapse=True).content[0].content



class Part(Concurrence):
    """A Part models a staff or staff group such as a grand staff. For that
    reason, a Part contains one or more Staff objects. It should not contain
    any other object types. Parts are normally elements of a Score.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
        number : Union[str, None], optional
            A string representing the part number. (Defaults to None)
        instrument : Union[str, None], optional
            A string representing the instrument name. (Defaults to None)
        delta : float, optional
            The onset (start) time relative to the parent's onset time. (Defaults to 0)
        duration : float, optional
            The duration in quarters or seconds. (Defaults to 0)

    Attributes
    ----------
        number : Union[str, None]
            A string representing the part number (if any). E.g. "22a".
        instrument : Union[str, None]
            A string representing the instrument name (if any).
        parent : Optional[EventGroup]
            The containing object or None.
        delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
    """

    def __init__(self,
                 parent: Optional[Score],
                 number: Optional[str] = None,
                 instrument: Optional[str] = None,
                 delta: float = 0,
                 duration: float = 0):
        super().__init__(parent, delta, duration)
        self.number = number
        self.instrument = instrument


    def show(self, indent: int = 0) -> "Part":
        """Display the Part information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Part
            The Part instance itself.
        """
        nstr = (" " + str(self.number)) if self.number else ""
        name = (" (" + self.instrument + ")") if self.instrument else ""
        return super().show(indent, "Part" + nstr + name)


    def is_measured(self):
        """Test if Part is measured. Conforms to strict hierarchy of:
        Part-Staff-Measure-(Note or Rest or Chord) and Chord-Note.
        """
        for staff in self.content:
            # only Staffs are expected, but things outside of the hierarchy
            # are allowed, so we only rule out violations of the hierarchy:
            if isinstance(staff, (Score, Part, Measure, Note, Rest, Chord)):
                return False
            if isinstance(staff, staff) and not staff.is_measured():
                return False
        return True


    def merge_tied_notes(self, parent: Optional[Score] = None) -> "Part":
        """Create a new Part with tied note sequences replaced by
        equivalent notes in each staff. Insert the new Part into parent.
        In cases where a note is tied across Staffs, the merged note is
        considered a member of the Staff where the note begins, and the
        tied-to notes in other Staffs are removed.
        """
        # Algorithm: Find all notes, and from notes, extract lists of
        # tied notes to be merged. (This will force iterator to complete
        # before we change the score.) For each group to be merged,
        # adjust the duration of the first note and delete the rest.
        # This pays the cost of copying some tied notes only to delete
        # them later, but it is robust in that notes can be tied across
        # Staffs and Chords, and with or without Measures. Ambiguity occurs
        # when two tied groups with the same pitch exist in different
        # Staff objects within the same Part: First, assume that when
        # two notes are tied, the offset of the first approximately matches
        # the onset of the second. When looking for the note at the end of
        # a tie, always look for matching pitches around the expected
        # onset time. If there are multiple candidates at the same pitch
        # and approximately same onset time, follow parent links up to
        # the staff level and choose the note with the matching Staff.
        # If the result is not unique, raise an exception.

        part = self.deepcopy_into(parent)
        notes = part.list_all(Note)
        tied_groups = []
        for i, note in enumerate(notes):
            if note.tie == "start":
                tied_groups.append(Part._find_tied_group(notes, i))
        # adjust the part according to the tied note groups:
        for group in tied_groups:
            note = group[0]
            onset = note.onset
            offset = group[-1].offset
            note.duration = offset - onset
            note.tie = None
            for note in group[1:]:
                note.parent.remove(note)
        return part


    @classmethod
    def _find_tied_group(self, notes, i):
        """find notes tied to notes[i]"""
        group = [notes[i]]  # start the list
        while notes[i].tie == "start" or notes[i].tie == "continue":
            offset = notes[i].offset
            keynum = notes[i].keynum  # allow ties to enharmonics
            candidates = []  # save indices of possible tied notes
            j = i + 1  # search for candidates starting at i + 1
            while j < len(notes) and notes[j].onset < offset + 0.0001:
                if (notes[j].keynum == keynum
                    and (notes[j].tie == "stop" or notes[j].tie == "continue")
                    and notes[j].onset > offset - 0.0001):
                    candidates.append(j)  # found one!
                j += 1
            if len(candidates) == 0:
                raise Exception("no note can resolve tie")
            elif len(candidates) > 1:  # do extra work to compare Staffs
                staff = notes[i].staff
                candidates = [c for c in candidates if notes[c].staff == staff]
                if len(candidates) != 1:
                    raise Exception("could not resolve ambiguous tie")
            # else note that we can tie notes between Staffs when it is not
            #     ambiguous
            i = candidates[0]
            group.append(notes[i])
            # note that the loop will collect notes until we satisfy
            #     notes[i].tie == 'stop', so notes[i].tie == 'continue'
            #     cause the loop to find the next tied note.
        return group


    def flatten(self, in_place=False):
        """Build a flattened Part where content will consist of notes only.
        If in_place=True, Part already has no ties and can be modified.
        Otherwise, return a new Part where deep copies of tied notes are
        merged.
        """
        part = self if in_place else self.merge_tied_notes()
        notes = part.list_all(Note)  # need list so we can sort
        # adjust deltas for new parent
        part_onset = part.onset
        for note in notes:
            note.delta = note.onset - part_onset
            note.parent = part
        notes.sort(key=lambda x: x.delta)
        part.content = notes
        return part


    def is_flat(self):
        """Test if Part is flat (contains only notes without ties)."""
        for note in self.content:
            # only Notes without ties are expected, but things outside of
            # the hierarchy are allowed, so we only rule out violations of
            # the hierarchy:
            if isinstance(note, (Score, Part, Staff, Measure, Rest, Chord)):
                return False
            if isinstance(note, Note) and note.tie is not None:
                return False
        return True


    def remove_measures(self, score: Optional["Score"],
                        has_ties: bool = True) -> "Part":
        """Return a Part with all Measures removed, but preserving
        Staffs in the hierarchy. Notes are "lifted" from Measures to
        become direct content of their Staff. Uses `merge_tied_notes()`
        to copy this Part unless `has_ties` is False, in which case
        there must be no tied notes and this Part is modified.

        Parameters
        ----------
        score : Union[Score, None]
            The Score instance (if any) to which the new Part will be added.
        has_ties : bool, optional
            If False, assume this is a copy we are free to modify,
            there are tied notes, and this Part is already contained
            by `score`. (Defaults to True: this Part will be copied
            into `score`.)

        Returns
        -------
        Part
            A Part with all Measures removed.
        """
        part = self.merge_tied_notes(score) if has_ties else self
        for staff in part.content:
            if isinstance(staff, Staff):
                staff.remove_measures()
        return part


class Staff(Sequence):
    """A Staff models a musical staff line extending through all systems.
    It can also model one channel of a standard MIDI file track. A Staff
    normally contains Measure objects and is an element of a Part.

    Parameters
    ----------
        parent : Optional[EventGroup]
            The containing object or None. (Defaults to None)
        number : Optional[int], optional
            The staff number. Normally, a Staff is given an integer number
            where 1 is the top staff of the part, 2 is the 2nd, etc.
        delta : float, optional
            The onset (start) time relative to the parent's onset time. (Defaults to 0)
        duration : float, optional
            The duration in quarters or seconds. (Defaults to 0)

    Attributes
    ----------
        parent : Optional[EventGroup]
            The containing object or None.
       delta : float
            The onset (start) time relative to the parent's onset time.
        duration : float
            The duration in quarters or seconds.
        content : list[Event]
            Elements contained within this collection.
        number : Optional[int]
            The staff number. Normally a Staff is given an integer number
            where 1 is the top staff of the part, 2 is the 2nd, etc.
    """

    def __init__(self,
                 parent: Optional[EventGroup],
                 number: Optional[int] = None,
                 delta: float = 0,
                 duration: float = 0):
        super().__init__(parent, delta, duration)
        self.number = number


    def show(self, indent: int = 0) -> "Staff":
        """Display the Staff information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Staff
            The Staff instance itself.
        """
        nstr = (" " + str(self.number)) if self.number else ""
        return super().show(indent, "Staff" + nstr)


    def is_measured(self):
        """Test if Staff is measured. Conforms to strict hierarchy of:
        Staff-Measure-(Note or Rest or Chord) and Chord-Note)
        """
        for measure in self.content:
            # Staff can contain many objects such as key signature or time
            # signature. We only rule out types that are outside-of-hierarchy:
            if isinstance(measure, (Score, Part, Staff, Note, Rest, Chord)):
                return False
            if isinstance(measure, Measure) and not measure.is_measured():
                return False
        return True


    def strip_ties(self, parent):
        """Create a new staff with tied note sequences replaced by
        equivalent notes
        """
        staff = self.emptycop_into(parent)
        for m_num, m in enumerate(self.find_all(Measure)):
            measure = m.emptycopy_into(staff)
            for event in m.content:
                if isinstance(event, Note):
                    if event.tie is None:
                        event.copy_into(measure)
                    elif event.tie == "start":
                        new_event = event.copy_into(measure)
                        new_event.duration = self.tied_duration(event, m_index=m_num)
                        new_event.tie = None
                    # else ignore the tied continuations of a previous note
                elif isinstance(event, Chord):
                    new_chord = event.copy_into()
                    for note in event.content:
                        if note.tie is None:
                            new_chord.insert(note.copy())
                        elif note.tie == "start":
                            new_note = note.copy()
                            new_note.duration = self.tied_duration(note, m_index=m_num)
                            new_note.tie = None
                            new_chord.insert(new_note)
                    measure.insert(new_chord)
                else:  # non-note objects are simply copied:
                    measure.insert(event.deep_copy())
            staff.insert(measure)
        return staff


    def tied_duration(self, note: Note, m_index=None):
        """Compute the full duration of note as the sum of notes that note
        is tied to. note.tie must be 'start'
        """
        measure = note.parent
        # if note was in chord we need the note's grandparent:
        if isinstance(measure, Chord):
            measure = measure.parent
        if m_index is None:  # get measure index
            m_index = self.content.index(measure)
        n_index = measure.content.index(note) + 1  # get note index
        onset = note.onset
        # search across all measures for tied-to note:
        while m_index < len(self.content):  # search all measures
            measure = self.content[m_index]
            # search within measure for tied-to note:
            while n_index < len(measure.content):
                event = measure.content[n_index]
                if isinstance(event, Note) and event.keynum == note.keynum:
                    if event.tie == "stop":
                        return event.end - onset
                    elif event.tie != "continue":
                        raise Exception("inconsistent tie attributes or notes")
                elif isinstance(event, Chord):
                    # search within chord for tied-to note:
                    for n in event.content:
                        if n.keynum == note.keynum:
                            # add durations until 'stop'
                            if n.tie == "continue" or n.tie == "stop":
                                duration = n.end_event - note.delta
                                if n.tie == "stop":
                                    return duration
                n_index += 1
            n_index = 0
            m_index += 1
        raise Exception("incomplete tie")


    def remove_measures(self) -> "Staff":
        """Modify Staff by removing all Measures.  Notes are "lifted"
        from Measures to become direct content of this Staff. There is
        no special handling for notes tied to or from another Staff,
        so normally this method should be used only on a Staff where
        ties have been merged (see `merge_tied_notes()`).
        This method is normally called from `remove_measures()` in Part,
        which insures that this Staff is not shared, so it is safe to
        modify it. If called directly, the caller, to avoid unintended
        side effects, must ensure that this Staff is not shared data.
        Only Note and KeySignature objects are copied from Measures
        to the Staff. All other objects are removed.

        Returns
        -------
        Staff
            A Staff with all Measures removed.
        """
        new_content = []
        for measure in self.content:
            if isinstance(measure, Measure):
                for event in measure.content:
                    if isinstance(event, (Note, KeySignature)):
                        new_content.append(event)
                    # else ignore the event
            else:  # non-Measure objects are simply copied
                new_content.append(measure)
        self.content = new_content
        return self
# fmt: off
