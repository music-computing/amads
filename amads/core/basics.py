# fmt: off
# flake8: noqa E129,E303
"""
Basic Symbolic Music Representation Classes

Overview
--------
The basic hierarchy of a score is [described here](../core.md).

Constructor Details
-------------------

The safe way to construct a score is to fully specify onsets for every Event.
These onsets are absolute and will not be adjusted *provided that* the parent
onset is also specified.

However, for convenience and to support simple constructs such as

  Chord(Note(pitch=60), Note(pitch=64)),

onsets are optional and default to None. To make this simple example work:

- Concurrences (Score, Part, and Chord) replace unspecified (None)
  onsets in their immediate content with the parent's onset (or 0 if
  it is None).

- Sequences (Staff, Measure) replace unspecified (None) onsets in
  their immediate content starting with the parent's onset (or 0 if
  None) for the first event and the offset of the previous Event for
  subsequent events.

- To handle the construction of nested Events, when an unspecified
  (None) onset of an EventGroup is replaced, the entire subtree of
  its content is shifted by the same amount. E.g. if a Chord is
  constructed with Notes with unspecified onsets, the Notes onsets
  will initially be replaced with zeros. Then, if the Chord onset is
  unspecified (None) and the Chord is passed in the content of a
  Measure and the Chord onset is replaced with 1.0, then the Notes
  are shifted to 1.0. If the Measure is then passed in the content of
  a Staff, the Measure and all its content might be shifted again.
"""

import copy
from typing import Dict, Generator, List, Optional, Type, Union

from amads.core.pitch import Pitch
from amads.core.timemap import TimeMap

__author__ = "Roger B. Dannenberg"


class Event:
    """A superclass for Note, Rest, EventGroup, and just about
    anything that takes place in time.

    Parameters
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    onset : float | None
        The onset (start) time.
    duration : float
        The duration of the event in quarters or seconds.

    Attributes
    ----------
    parent : Optional[Event]
        The containing object or None.
    _onset : float | None
        The onset (start) time.
    duration : float
        The duration of the event in quarters or seconds.
    info : Optional[Dict]
        Additional attribute/value information.
    """
    __slots__ = ["parent", "_onset", "duration", "info"]
    parent: Optional["EventGroup"]
    _onset: float | None
    duration: float
    info: Optional[Dict]


    def __init__(self, parent: Optional["EventGroup"],
                 onset: float | None, duration: float):
        """
        Initialize an Event instance.

        """
        self.parent = None  # set below when inserted into parent
        self._onset = onset
        self.duration = duration
        self.info = None

        if parent:
            assert isinstance(parent, EventGroup)
            parent.insert(self)
        else:
            self.parent = None


    def _event_onset(self) -> str:
        """produce onset string for __str__
        """
        return ("onset=None" if self.onset is None else
                f"onset={self.onset:0.3f}")

            
    def _event_times(self, dur: bool = True) -> str:
        """produce onset and duration string for __str__
        """
        duration = self.duration
        if duration is not None:
            duration = f"{self.duration:0.3f}"

        return f"{self._event_onset()}, duration={duration}"


    def set(self, property, value):
        """Set a property on this Event. Every event can be extended
        with additional properties.

        Parameters
        ----------
        property : str
            The name of the property to set.
        value : Any
            The value to assign to the property.
        """
        if self.info is None:
            self.info = {}
        self.info[property] = value


    def get(self, property, default=None):
        """Get the value of a property from this Event.

        Parameters
        ----------
        property : str.
            The name of the property to get.

        default : Any, optional.
            The default value to return if the property is not found.
            (Defaults to None)

        Returns
        -------
        Any
            The value of the specified property.
        """
        if self.info is None:
            return default
        return self.info.get(property, default)


    def has(self, property) -> bool:
        """Check if the Event has a specific property.

        Parameters
        ----------
        property : str
            The name of the property to check.

        Returns
        -------
        bool
            True if the property exists, False otherwise.
        """
        return property in self.info


    def copy(self, parent: Optional[EventGroup] = None) -> Event:
        """
        Return a deep copy of the `Event` instance except for the parent,
        which may be provided as an argument. See also copyempty to copy
        an EventGroup without the content.

        Returns
        -------
        Event
            A deep copy (except for parent) of the Event instance.
        """
        # remove link to parent to break link going up the tree
        # preventing deep copy from copying the entire tree
        original_parent = self.parent
        self.parent = None
        c = copy.deepcopy(self)  # deep copy of this event down to leaf nodes
        self.parent = original_parent  # restore link to parent
        if parent:
            parent.insert(c)
        return c


    @property
    def onset(self) -> float:
        """Retrieve the onset (start) time.

        If the onset is None, raise an exception. (Events can have None
        onset times, but they must be set before retrieval. onsets that
        are None are automatically set when the Event is added to an
        EventGroup.)
    
        Returns
        -------
        float | None
            The onset (start) time.
        """
        if self._onset is None:
            raise ValueError("Onset time is not set.")
        return self._onset


    @onset.setter
    def onset(self, onset: float) -> None:
        """Set the onset (start) time.

        Parameters
        ----------
        onset : float
            The new onset (start) time.
        """
        self._onset = onset


    def _quantize(self, divisions: int) -> "Event":
        """Modify onset and offset to a multiple of divisions per quarter note.

        This method modifies the Event in place. It also handles tied notes.

        E.g., use divisions=4 for sixteenth notes. If a
        Note tied to or from other notes quantizes to a zero
        duration, reduce the chain of tied notes to eliminate
        zero-length notes. See Collection.quantize for
        additional details.

        self.onset and self.duration must be non-None.

        Parameters
        ----------
        divisions : int
            The number of divisions per quarter note, e.g., 4 for
            sixteenths, to control quantization.

        Returns
        -------
        Event
            self, after quantization.
        """
        if self._onset is None or self.duration is None:
            raise ValueError(
                "Cannot quantize Event with None onset or duration")
        self.onset = round(self.onset * divisions) / divisions
        quantized_offset = round(self.offset * divisions) / divisions

        # tied note cases: Given any two tied notes where the first has a
        # quantized duration of zero, we want to eliminate the first one
        # because it is almost certainly at the end of a measure and ties
        # to the "real" note at the start of the next measure. In the
        # special case where the tied-to note quantizes to a zero duration,
        # we still want it to appear at the beginning of the measure, and
        # our convention is to set its duration to one quantum as long as
        # the original string of tied notes had a non-zero duration.
        # (Zero duration is preserved however for cases like meta-events
        # and grace notes which have zero duration before quantization.)
        #     Otherwise, if there are two tied notes and the first has a
        # non-zero and the second has zero quantized duration, we assume
        # that the note extended just barely across the bar line and we
        # eliminate the second note.
        #     Note that since we cannot look back to see if we are at the
        # end of a tie, we need to look forward using Note.tie.

        if (self.duration == 0 and
            (not isinstance(self, Note) or self.tie == None)):
            return self  # do not change duration if it is originally zero

        while isinstance(self, Note) and self.tie:  # check tied-to note:
            tie = self.tie  # the note our tie connects to
            onset = round(tie.onset * divisions) / divisions  # type: ignore
            offset = round(tie.offset * divisions) / divisions  # type: ignore
            duration = offset - onset  # quantized duration
            # if we tie from non-zero quantized duration to zero quantized
            # duration, eliminate the tied-to note
            if (quantized_offset - self.onset > 0 and   # type: ignore
                duration == 0):                         # type: ignore
                self.tie = tie.tie  # in case tie continues
                # remove tied_to note from its parent
                if tie.parent:
                    tie.parent.remove(tie)
                # print("removed tied-to note", tied_to,
                #       "because duration quantized to zero")
            elif quantized_offset - self.onset == 0:    # type: ignore
                # remove self from its parent; prefer tied_to note
                # before removing, transfer duration from self to
                # tied_to to avoid strange case where the tied group
                # originally had a non-zero duration so we want the
                # tied_to duration to be non-zero:
                tie.duration += self.duration
                if self.parent:
                    self.parent.remove(self)
                # tied_to will be revisited and quantized so no more work here
                return self
            else:  # both notes have non-zero durations
                break

        # now that potential ties are handled, set the duration of self
        if self.duration != 0:  # only modify non-zero durations
            self.duration = quantized_offset - self.onset  # type: ignore
            if self.duration == 0:  # do not allow duration to become zero:
                self.duration = 1 / divisions 
        # else: original zero duration remains zero after quantization
        return self


    @property
    def units_are_seconds(self) -> bool:
        """Check if the times are in seconds.

        Returns
        -------
        bool
            True if the event's times in seconds and there is a parent.
        """
        return self.parent.units_are_seconds if self.parent else False


    @property
    def units_are_quarters(self) -> bool:
        """Check if the times are in quarters.

        Returns
        -------
        bool
            True if the event's times in quarters and there is a parent.
        """
        return self.parent.units_are_quarters if self.parent else False


    def _convert_to_seconds(self, time_map: TimeMap) -> None:
        """Convert the event's duration and onset to seconds using the
        provided TimeMap.

        Parameters
        ----------
        time_map : TimeMap
            The TimeMap object used for conversion.
        """
        if self._onset is None or self.duration is None:
            raise ValueError(
                "Cannot convert Event with None onset or duration")
        onset_time = time_map.quarter_to_time(self.onset)       # type: ignore
        offset_time = time_map.quarter_to_time(self.offset)     # type: ignore
        self.onset = onset_time
        self.duration = offset_time - onset_time


    def _convert_to_quarters(self, time_map: TimeMap) -> None:
        """Convert the event's duration and onset to quarters using the
        provided TimeMap.

        Parameters
        ----------
        time_map : TimeMap
            The TimeMap object used for conversion.
        """
        if self._onset is None or self.duration is None:
            raise ValueError(
                "Cannot convert Event with None onset or duration")
        onset_quarters = time_map.time_to_quarter(self.onset)
        offset_quarters = time_map.time_to_quarter(self.offset)
        self.onset = onset_quarters
        self.duration = offset_quarters - onset_quarters


    @property
    def offset(self) -> float:
        """Retrieve the global offset (stop) time.

        Returns
        -------
        float
            The global offset (stop) time.
        """
        if self._onset is None or self.duration is None:
            raise ValueError(
                "Event offset undefined (onset or duration is None)")
        return self.onset + self.duration


    @offset.setter
    def offset(self, offset: float) -> None:
        """Set the global offset (stop) time.

        Parameters
        ----------
        offset : float
            The new global offset (stop) time.
        """
        if self._onset is None:
            raise ValueError("Event offset undefined (onset is None)")
        self.duration = offset - self.onset


    @property
    def part(self) -> Optional["Part"]:
        """Retrieve the Part containing this event

        Returns
        -------
        Optional[Part]
            The Part containing this event or None if not found."""
        p = self.parent
        while p and not isinstance(p, Part):
            p = p.parent
        return p


    @property
    def score(self) -> Optional["Score"]:
        """Retrieve the Score containing this event

        Returns
        -------
        Optional[Score]
            The Score containing this event or None if not found."""
        p = self.parent
        while p and not isinstance(p, Score):
            p = p.parent
        return p


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
    parent : Optional[EventGroup], optional
        The containing object or None.
    onset : float, optional
        The onset (start) time. An initial value of None might
        be assigned when the Note is inserted into an EventGroup.
        (Defaults to None)
    duration : float, optional
        The duration of the rest in quarters or seconds. (Defaults to 1)

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : float, optional
        The onset (start) time. None represents an unspecified onset.
    duration : float
        The duration of the rest in quarters or seconds.
    """
    __slots__ = []

    def __init__(self, parent: Optional["EventGroup"] = None,
                 onset: Optional[float] = None, duration: float = 1):
        super().__init__(parent, onset, duration)


    def __str__(self) -> str:
        """Short string representation
        """
        return f"Rest({self._event_times()})"


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

        print(" " * indent, self, sep="")
        return self



class Note(Event):
    """Note represents a musical note. It is normally an element of
    a Measure.

    Parameters
    ----------
    parent : Optional[EventGroup], optional
        The containing object or None.
    onset : float, optional
        The onset (start) time. An initial value of None might
        be assigned when the Note is inserted into an EventGroup.
        (Defaults to None)
    duration : float, optional
        The duration of the note in quarters or seconds. (Defaults to 1)
    pitch : Union[Pitch, int, float], optional
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
    _onset : Optional[float]
        The onset (start) time. None represents an unspecified onset.
    duration : float
        The duration of the note in quarters or seconds. See the
        property tied_duration for the duration of an entire group
        if the note is the first of a tied group of notes.
    pitch :  Pitch | None
        The pitch of the note. Unpitched notes have a pitch of None.
    dynamic : Optional[Union[int, str]]
        Dynamic level (MIDI velocity) or string.
    lyric : Optional[str]
        Lyric text.
    tie : Optional[Note]
        The note that this note is tied to, if any.
    """
    __slots__ = ["pitch", "dynamic", "lyric", "tie"]
    pitch: Optional[Pitch]
    dynamic: Optional[Union[int, str]]
    lyric: Optional[str]
    tie: Optional["Note"]

    def __init__(self,
                 parent: Optional["EventGroup"] = None,
                 onset: Optional[float] = None,
                 duration: float = 1.0,
                 pitch: Union["Pitch", int, float, str, None] = 60,
                 dynamic: Union[int, str, None] = None,
                 lyric: Optional[str] = None):
        """Initialize a Note instance.
        pitch is normally a Pitch, but can be an integer MIDI key number
        that will be converted to a Pitch object.
        """
        super().__init__(parent, onset, float(duration))
        if isinstance(pitch, Pitch):
            self.pitch = pitch
        elif pitch is not None:
            self.pitch = Pitch(pitch)
        # else pitch is None, unpitched note
        self.dynamic = dynamic
        self.lyric = lyric
        self.tie = None


    def __deepcopy__(self, memo: dict) -> "Note":
        """Return a deep copy of the Note instance. The pitch is
        shallow copied to avoid copying the entire Pitch object.

        Parameters
        ----------
        memo : dict
            A dictionary to keep track of already copied objects.

        Returns
        -------
        Note
            A deep copy of the Note instance with a shallow copy of the pitch.
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # Iterate up the superclass chain and copy __slots__ at each level
        # If there is a __dict__, it will be in a __slots__ and will be deep
        # copied, so all attributes in __dict__ will be copied. If there is
        # multiple inheritance with duplicated slots, this will copy the
        # duplicated slot two (or more) times, but it should get the right
        # result.
        for base in cls.__mro__:
            if hasattr(base, '__slots__'):
                slots = base.__slots__
                if isinstance(slots, str):
                    slots = [slots]
                for slot in slots:
                    if slot == "pitch":
                        result.pitch = self.pitch
                    else:
                        setattr(result, slot,
                                copy.deepcopy(getattr(self, slot), memo))

        return result

    @property
    def tied_duration(self) -> Union[float, int]:
        """Retrieve the duration of the note in quarters or seconds.
        If the note is the first note of a group of tied notes,
        return the duration of the entire group.

        Returns
        -------
        float
            The duration of the note in quarters or seconds.
        """
        duration = self.duration
        if self.tie is not None:  # recursively sum all tied durations:
            duration += self.tie.tied_duration
        return duration  # type: ignore (Note duration is always float)


    def __str__(self) -> str:
        """Short string representation

       Returns
        -------
        str
            A short human-readable description of the note.
        """
        dynamic_info = ""
        if self.dynamic is not None:
            dynamic_info = f", dynamic={self.dynamic}"

        lyric_info = ""
        if self.lyric is not None:
            lyric_info = f", lyric={self.lyric}"

        return (f"Note({self._event_times()}{dynamic_info}{lyric_info}, " +
                f"pitch={self.name_with_octave})")


    def show(self, indent: int = 0, tied: bool = False) -> "Note":
        """Show the note with its pitch name, onset, duration, and optional
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
        tie_info = ""
        if self.tie is not None:
            tie_info = " tied"
        tie_prefix = "  tied to " if tied else ""

        print(" " * indent, tie_prefix, self, tie_info, sep="")
        if self.tie:
            self.tie.show(indent + 2, tied=True)
        return self


    @property
    def step(self) -> str:
        """Retrieve the name of the pitch, e.g. A, B, C, D, E, F, G
        corresponding to letter names without accidentals.

        If the note is unpitched (pitch is None), return the empty string.
        """
        return self.pitch.step if self.pitch else ""


    @property
    def name(self) -> str:
        """Retrieve the string representation of the pitch name,
        including accidentals, e.g. A# or Bb.

        If the note is unpitched (pitch is None), return the empty string.
        """
        return self.pitch.name if self.pitch else ""


    @property
    def name_with_octave(self) -> str:
        """Retrieve the string representation of the pitch name
        with octave, e.g. A4 or Bb3.

        If the note is unpitched (pitch is None), return the empty string.
        """
        return self.pitch.name_with_octave if self.pitch else ""


    @property
    def pitch_class(self) -> int:
        """Retrieve the pitch class of the note, e.g. 0, 1, 2, ..., 11.

        If the note is unpitched (pitch is None), raise ValueError.
        """
        if self.pitch is None:
            raise ValueError("Unpitched note has no pitch class.")
        return self.pitch.pitch_class


    @pitch_class.setter
    def pitch_class(self, pc: int) -> None:
        """Set the pitch class of the note. 
        
        Keep the same octave, but not necessarily the same register.
        The alt (accidental) is preserved.

        Parameters
        ----------
        pc : int
            The new pitch class value.
        """
        self.pitch = Pitch(pc + 12 * (self.octave + 1), 
                           self.pitch.alt if self.pitch else 0)


    @property
    def octave(self) -> int:
        """Retrieve the octave number of the note, based on key_num.
        E.g. C4 is enharmonic to B#3 and represent the same (more or less)
        pitch, but BOTH have an octave of 4. On the other hand name()
        will return "C4" and "B#3", respectively.

        If the note is unpitched (pitch is None), raise ValueError.

        Returns
        -------
        int
            The octave number of the note.
        """
        if self.pitch is None:
            raise ValueError("Unpitched note has no octave.")
        else:
            return self.pitch.octave


    @octave.setter
    def octave(self, oct: int) -> None:
        """Set the octave number of the note.

        The alt (accidental) is preserved.
        If the note is unpitched (pitch is None), raise ValueError.

        Parameters
        ----------
        oct : int
            The new octave number.
        """
        self.pitch = Pitch(self.key_num + (oct - self.octave) * 12,
                           self.pitch.alt if self.pitch else 0)


    @property
    def key_num(self) -> float | int:
        """Retrieve the MIDI key number of the note, e.g. C4 = 60.

        If the note is unpitched (pitch is None), raise ValueError.

        Returns
        -------
        int
            The MIDI key number of the note.
        """
        if self.pitch is None:
            raise ValueError("Unpitched note has no key number.")
        return self.pitch.key_num


    def enharmonic(self) -> "Pitch":
        """Return a Pitch where alt is zero or has the opposite sign and
        where alt is minimized. E.g. enharmonic(C-double-flat) is A-sharp
        (not B-flat). If alt is zero, return a Pitch with alt of +1 or -1
        if possible. Otherwise, return a Pitch with alt of -2.

        If the note is unpitched (pitch is None), raise ValueError.

        Returns
        -------
        Pitch
            A Pitch object representing the enharmonic equivalent of the note.
        """
        if self.pitch is None:
            raise ValueError("Unpitched note has no enharmonic equivalent.")
        return self.pitch.enharmonic()


    def upper_enharmonic(self) -> "Pitch":
        """Return a valid Pitch with alt decreased by 1 or 2, e.g. C#->Db,
        C##->D, C###->D#.

        If the note is unpitched (pitch is None), raise ValueError.

        Returns
        -------
        Pitch
            A Pitch object representing the upper enharmonic
            equivalent of the note.
        """
        if self.pitch is None:
            raise ValueError(
                      "Unpitched note has no upper enharmonic equivalent.")
        return self.pitch.upper_enharmonic()


    def lower_enharmonic(self) -> "Pitch":
        """Return a valid Pitch with alt increased by 1 or 2, e.g. Db->C#,
        D->C##, D#->C###.

        If the note is unpitched (pitch is None), raise ValueError.

        Returns
        -------
        Pitch
            A Pitch object representing the lower enharmonic
            equivalent of the note.
        """
        if self.pitch is None:
            raise ValueError(
                      "Unpitched note has no lower enharmonic equivalent.")
        return self.pitch.lower_enharmonic()


    def simplest_enharmonic(self, 
            sharp_or_flat: Optional[str] = "default") -> "Pitch":
        """Return a valid Pitch with the simplest enharmonic representation.
        (see Pitch.simplest_enharmonic)

        Parameters
        ----------
        sharp_or_flat: str
            This is only relevant if the pitch needs an alteration, otherwise
            it is unused. The value can be "sharp" (use sharps), "flat" (use
            flats), and otherwise use the same enharmonic choice as the Pitch
            constructor.

        Exceptions
        ----------
        If the note is unpitched (pitch is None), raise ValueError.

        Returns
        -------
        Pitch
            A Pitch object representing the enharmonic equivalent.
        """
        if self.pitch is None:
            raise ValueError(
                      "Unpitched note has no simplest enharmonic equivalent.")
        return self.pitch.simplest_enharmonic(sharp_or_flat)



class TimeSignature(Event):
    """TimeSignature is a zero-duration Event with timesig info.

    Parameters
    ----------
    parent : Optional[EventGroup], optional
        The containing object or None. (Defaults to None)
    onset : float, optional
        The onset (start) time. An initial value of None might
        be assigned when the TimeSignature is inserted into an EventGroup.
        (Defaults to None)
    upper : float, optional
        The "numerator" of the key signature: subdivisions units per
        measure, a number, which may be a fraction. (Defaults to 4)
    lower : int, optional
        The "denominator" of the key signature: a whole number power
        of 2, e.g. 1, 2, 4, 8, 16, 32, 64. (Defaults to 4) representing
        the symbol for one subdivision, e.g. 4 implies quarter note.

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : float
        The onset (start) time.
    duration : float
        Always zero for this subclass.
    upper : float
        The "numerator" of the key signature: subdivisions per measure.
    lower : int
        The "denominator" of the key signature: a whole number power of 2.
    """
    __slots__ = ["upper", "lower"]
    upper: float
    lower: int

    def __init__(self,
                 parent: Optional["EventGroup"] = None,
                 onset: float = 0.0, upper: float = 4.0, lower: int = 4):
        super().__init__(parent, 0, onset)
        self.upper = upper
        self.lower = lower


    def __str__(self) -> str:
        """Short string representation
        """
        return (f"TimeSignature({self._event_onset()}, " +
                f"{self.upper}/{self.lower})")


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
        print(" " * indent, self, sep="")
        return self



class Clef(Event):
    """Clef is a zero-duration Event with clef info.

    Parameters
    ----------
    parent : Optional["EventGroup"], optional
        The containing object or None. (Defaults to None)
    onset : float, optional
        The onset (start) time. An initial value of None might
        be assigned when the TimeSignature is inserted into an EventGroup.
        (Defaults to None)
    clef : str, optional (Defaults to "treble")

    Attributes
    ----------
    parent : Optional["EventGroup"]
        The containing object or None.
    _onset : float
        The onset (start) time.
    duration : float
        Always zero for this subclass.
    clef : str
        The clef name, one of "treble", "bass", "alto", "tenor", 
        "percussion", "treble8vb" (Other clefs may be added later.)
    """
    __slots__ = ["clef"]
    clef: str

    def __init__(self,
                 parent: Optional["EventGroup"] = None,
                 onset: float = 0.0, clef: str = "treble"):
        super().__init__(parent, 0, onset)
        if clef not in ["treble", "bass", "alto", "tenor",
                      "percussion", "treble8vb"]:
            raise ValueError(f"Invalid clef: {clef}")
        self.clef = clef


    def __str__(self) -> str:
        """Short string representation
        """
        return f"Clef({self._event_onset()}, {self.clef})"


    def show(self, indent: int = 0) -> "Clef":
        """Display the Clef information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        Clef
            The Clef instance itself.
        """
        print(" " * indent, self, sep="")
        return self



class KeySignature(Event):
    """KeySignature is a zero-duration Event with key_sig info.

    Parameters
    ----------
    parent : Optional["EventGroup"], optional
        The containing object or None. (Defaults to None)
    onset : float, optional
        The onset (start) time. An initial value of None might
        be assigned when the KeySignature is inserted into an EventGroup.
        (Defaults to None)
    key_sig : int, optional
        An integer representing the number of sharps (if positive)
        and flats (if negative), e.g. -3 for Eb major or C minor.
        (Defaults to 0)

    Attributes
    ----------
    parent : Optional["EventGroup"]
        The containing object or None.
    _onset : float
        The onset (start) time.
    duration : float
        Always zero for this subclass.
    key_sig : int
        An integer representing the number of sharps and flats.
    """
    __slots__ = ["key_sig"]
    key_sig: int

    def __init__(self, parent: Optional["EventGroup"] = None,
                 onset: float = 0.0, key_sig: int = 0):
        super().__init__(parent=parent, onset=onset, duration=0)
        self.key_sig = key_sig


    def __str__(self) -> str:
        """Short string representation
        """
        key_sig = abs(self.key_sig)
        kind = "sharps" if self.key_sig > 0 else "flats"
        return f"KeySignature({self._event_onset()}, {key_sig} {kind})"


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
        print(" " * indent, self, sep="")
        return self



class EventGroup(Event):
    """A collection of Event objects. (An abstract class.)

    Use one of the subclasses: Score, Part, Staff, Measure or Chord.

    Normally, you create any EventGroup (Chord, Measure, Staff, Part,
    Score) with no content, then add content. You can add content in
    bulk by simply setting the `content` attribute to a list of Events
    whose `parent` attributes have been set to the EventGroup. You can
    also add one event at a time, by calling the EventGroup's insert
    method. (This will change the event parent from None to the group.)
    It is recommended to specify all onsets and durations explicitly,
    including the onset of the group itself.

    Alternatively, you can provide content when the group is
    constructed.  Chord, Measure, Staff, Part, and Score all have
    `*args` parameters so that you can write something like:

        Score(Part(Staff(Measure(Note(...), Note(...)),
        Measure(Note(...), Note(...)))))

    In this case, it is recommended that you leave the onsets of content
    and chord unknown (None, the default). Then, as each event or group
    becomes content for a parent, the onsets will be set automatically,
    organizing events sequentially (in Measures and Staves) or
    concurrently (in Chords, Parts, Scores).

    The use of unknown (None) onsets is offered as a convenience for
    simple cases. The main risk is that onsets are considered to be
    relative to the group onset if the group onset is not known. E.g.
    if onsets are specified within the content of an EventGroup (Chord,
    Measure, Staff, Part, Score) but the group onset is unknown (None),
    and *then* you assign (or a parent assigns) an onset value to the
    group, the content onsets (even "known" ones) will all be shifted
    by the assigned onset. This happens *only* when changing an onset
    from None to a number. Subsequent changes to the group onset will
    not adjust the content onsets, which are considered absolute times
    once the group onset is known.

    Parameters
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    onset : float | None
        The onset (start) time.
    duration : Optional[float]
        The duration in quarters or seconds.
    content : Optional[list]
        A list of Event objects to be added to the group. The parent
        of each Event is set to this EventGroup, and it is an error
        if any Event already has a parent.
    pack : bool, optional
        If true, Events in content are adjusted to form a sequence
        where the first event onset is the specified group onset
        (which defaults to 0) and the onset of other events is
        the offset of the previous event in the sequence.
        (Defaults to False).


    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : Optional[float]
        The onset (start) time.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    """
    __slots__ = ["content"]
    duration: float
    content: list[Event]


    def __init__(self, parent: Optional["EventGroup"],
                 onset: Optional[float], duration: Optional[float],
                 content: Optional[list[Event]], pack: bool = False):

        # pass 0 for duration because Event constructor wants a number,
        # but we will set duration later based on duration parameter or
        # based on content if duration is None:
        super().__init__(parent=parent, onset=onset, duration=0.0)
        max_offset = 0
        if content:
            prev_offset = 0 if onset == None else onset
            for elem in content:
                if elem.parent and elem.parent != self:
                    raise Exception("Event already has a (different) parent")
                # Not sure why Pylance thinks this is a problem:
                elem.parent = self
                if pack or (elem.onset == None):
                    elem.onset = prev_offset
                    prev_offset = elem.offset  # depends on e.onset
                max_offset = max(max_offset, elem.offset)
            if duration == None:
                duration = max_offset - (0 if onset is None else onset)
        self.duration = duration if duration is not None else 0.0
        self.content = content if content else []


    @onset.setter
    def onset(self, onset: float) -> None:
        """When an unspecified onset time is set (normally because this will
        become the content of a Sequence or Concurrence such as a Staff, Part
        or Score, the content is assumed to have offsets that reflect deltas
        from the beginning of this EventGroup. Setting onset to a non-zero
        value will treat the content onsets as deltas and shift them by onset
        so that the resulting content has correct absolute onset times.
        """
        if self._onset == None and onset != 0: # shift content
            for elem in self.content:
                elem._onset += onset  # type: ignore
        self._onset = onset


    def _convert_to_seconds(self, time_map: TimeMap) -> None:
        """Convert the event's duration and onset to seconds using the
        provided TimeMap. Convert content as well.

        Parameters
        ----------
        time_map : TimeMap
            The TimeMap object used for conversion.
        """
        super()._convert_to_seconds(time_map)
        for elem in self.content:
            elem._convert_to_seconds(time_map)


    def _convert_to_quarters(self, time_map: TimeMap) -> None:
        """Convert the event's duration and onset to quarters using the
        provided TimeMap. Convert content as well.

        Parameters
        ----------
        time_map : TimeMap
            The TimeMap object used for conversion.
        """
        onset_quarters = time_map.time_to_quarter(self.onset)
        offset_quarters = time_map.time_to_quarter(self.onset + self.duration)
        self.onset = onset_quarters
        self.duration = offset_quarters - onset_quarters
        for elem in self.content:
            elem._convert_to_quarters(time_map)


    def emptycopy(self, parent: Optional["EventGroup"] = None) -> "EventGroup":
        """Create a deep copy of the EventGroup except for the parent and
        content. The parent may be provided as an argument. This is
        useful for copying an EventGroup without copying its content.
        See also copy() to copy an EventGroup with its content.

        Parameters
        ----------
        parent : Optional[EventGroup]
            The new parent to insert the copied Event into.

        Returns
        -------
        EventGroup
            A deep copy of the EventGroup instance with the new parent
            (if any) and no content.
        """
        # rather than customize __deepcopy__, we "hide" the content to avoid
        # copying it. Then we restore it after copying and fix parent.
        original_content = self.content
        self.content = []
        c = self.copy(parent)
        self.content = original_content
        return c  #type: ignore (c will always be an EventGroup)


    def expand_chords(self, parent: Optional["EventGroup"] = None) -> "EventGroup":
        """Replace chords with the multiple notes they contain.

        Returns a deep copy with no parent unless parent is provided.
        Normally, you will call score.expand_chords() which returns a deep
        copy of Score with notes moved from each chord to the copy of the
        chord's parent (a Measure or a Part). The parent parameter is 
        primarily for internal use when expand_chords is called recursively
        on score content.

        Parameters
        ----------
        parent : EventGroup, optional
            The new parent to insert the copied EventGroup into. (Defaults to None)

        Returns
        -------
        EventGroup
            A deep copy of the EventGroup instance with all
            Chord instances expanded.
        """
        group = self.emptycopy(parent)
        for item in self.content:
            if isinstance(item, Chord):
                for note in item.content:  # expand chord
                    note.copy(group)
            if isinstance(item, EventGroup):
                item.expand_chords(group)  # recursion for deep copy/expand
            else:
                item.copy(group)  # deep copy non-EventGroup
        return group


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


    def inherit_duration(self) -> "EventGroup":
        """Set the duration of this EventGroup according to the
        maximum offset (end) time of its children. If the EventGroup
        is empty, the duration is set to 0. This method modifies the
        EventGroup instance.

        Returns
        -------
        EventGroup
            The EventGroup instance (self) with updated duration.
        """
        onset = 0 if self._onset == None else self._onset
        max_offset = onset
        for elem in self.content:
            max_offset = max(max_offset, elem.offset)
        self.duration = max_offset - onset

        return self


    def insert(self, event: Event) -> "EventGroup":
        """Insert an event without any changes to event.onset or
        self.duration. If the event is out of order, insert it just before
        the first element with a greater onset. The method modifies this
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
        assert event._onset != None  # must be a number
        atend = self.last()
        if atend and event.onset < atend.onset:
            # search in reverse from end
            i = len(self.content) - 2
            while i >= 0 and self.content[i].onset > event.onset:
                i -= 1
            # now i is either -1 or content[i] <= event.onset, so
            # insert event at content[i+1]
            self.content.insert(i + 1, event)
        else:  # simply append at the end of content:
            self.content.append(event)
        event.parent = self
        return self


    def last(self) -> Optional[Event]:
        """Retrieve the last event in the content list.

        Returns
        -------
        Optional[Event]
            The last event in the content list or None if the list is empty.
        """
        return self.content[-1] if len(self.content) > 0 else None


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


    def merge_tied_notes(self, parent: Optional["EventGroup"] = None,
                         ignore: list[Note] = []) -> "EventGroup":
        """Create a new EventGroup with tied note sequences replaced by
        equivalent notes in each staff. Insert the new EventGroup into parent.
        Notes identified as being tied to are passed in ignore.
        """
        # Algorithm: Find all notes, removing tied notes and updating
        # duration when ties are found. These tied notes are added to
        # ignore so they can be skipped when they are encountered.

        group = self.emptycopy(parent)
        for event in self.content:
            if isinstance(event, Note):
                if event in ignore:  # do not copy tied notes into group;
                    if event.tie:
                        ignore.append(event.tie)  # add tied note to ignore
                    # We will not see this note again, so
                    # we can also remove it from ignore. Removal is expensive
                    # but it could be worse for ignore to grow large when there
                    # are many ties since we have to search it entirely once
                    # per note. An alternate representation might be a set to
                    # make searching fast.
                    ignore.remove(event)
                else:
                    if event.tie:
                        tied_note = event.tie  # save the tied-to note
                        event.tie = None  # block the copy
                        ignore.append(tied_note)
                        event_copy = event.copy(group)  # copy note into group
                        event.tie = tied_note  # restore original event
                        # this is subtle: event.tied_duration (a property) will sum
                        # up durations of all the tied notes. Since event_copy
                        # is not tied, the sum of durations is stored on that
                        # one event_copy:
                        event_copy.duration = event.tied_duration
                    else:
                        event.copy(group)  # put the untied note into group
            elif isinstance(event, EventGroup):
                event.merge_tied_notes(group, ignore)
            else:
                event.copy(group)  # simply copy to new parent
        return group


    def _quantize(self, divisions: int) -> "EventGroup":
        """"Since `_quantize` is called recursively on children, this method is
        needed to redirect `EventGroup._quantize` to `quantize`
        """
        return quantize(self, divisions)


    def quantize(self, divisions: int) -> "EventGroup":
        """Modify all times and durations to a multiple of divisions
        per quarter note, e.g., 4 for sixteenth notes. Onsets and offsets
        are moved to the nearest quantized time. Any resulting duration
        change is less than one quantum. Any non-zero duration that would
        quantize to zero duration gets a duration of one quantum since
        zero duration is almost certainly going to cause notation and
        visualization problems.
        
        Special cases for zero duration: 
            1. If the original duration is zero as in metadata or possibly
               grace notes, we preserve that.
            2. If a tied note durations quantizes to zero, we remove the
               tied note entirely provided some other note in the tied
               sequence has non-zero duration. If all tied notes quantize
               to zero, we keep the first one and set its duration to
               one quantum.

        This method modifies this EventGroup and all its content in place.

        Note that there is no way to specify "sixteenths or eighth triplets"
        because 6 would not allow sixteenths and 12 would admit sixteenth
        triplets. Using tuples as in Music21, e.g., (4, 3) for this problem
        creates another problem: if quantization is to time points 1/4, 1/3,
        then the difference is 1/12 or a thirty-second triplet. If the
        quantization is applied to durations, then you could have 1/4 + 1/3
        = 7/12, and the remaining duration in a single beat would be 5/12,
        which is not expressible as sixteenths, eighth triplets or any tied
        combination.

        Parameters
        ----------
        divisions : int
            The number of divisions per quarter note, e.g., 4 for
            sixteenths, to control quantization.

        Returns
        -------
        EventGroup
            The EventGroup instance (self) with (modified in place) 
            quantized times.
        """

        super().quantize(divisions)
        # iterating through content is tricky because we may delete a
        # Note, shifting the content:
        i = 0
        while i < len(self.content):
            event = self.content[i]
            event.quantize(divisions)
            if event == self.content[i]:
                i += 1
            # otherwise, we deleted event so the next event to
            # quantize is at index i; don't incremenet i
        return self


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
        element.parent = None
        return self


    def remove_rests(self, parent: Union["EventGroup", 
                                         None] = None) -> "EventGroup":
        """Remove all Rest objects. Returns a deep copy with no parent,
        unless parent is provided.

        Parameters
        ----------
        parent : EventGroup, optional
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
        group = self.emptycopy(parent)
        for item in self.content:
            if isinstance(item, Rest):
                continue  # skip the Rests while making deep copy
            if isinstance(item, EventGroup):
                item.remove_rests(group)  # recursion for deep copy
            else:
                item.copy(group)  # deep copy non-EventGroup
        return group


    def __str__(self) -> str:
        """Short string representation
        """
        return f"{self.__class__.__name__}({self._event_times()})"


    def show(self, indent: int = 0) -> "EventGroup":
        """Display the EventGroup information.

        Parameters
        ----------
        indent : int, optional
            The indentation level for display. (Defaults to 0)

        Returns
        -------
        EventGroup
            The EventGroup instance itself.
        """
        print(" " * indent, self, sep="")
        for elem in self.content:
            elem.show(indent + 4)  # type: ignore (show exists)
        return self



class Sequence(EventGroup):
    """Sequence represents a temporal sequence of music events.

    Parameters
    ----------
    parent : Optional[EventGroup], optional
        The containing object or None. (Defaults to None)
    onset : Optional[float], optional
        The onset (start) time. None means unknown, to be
        set when Sequence is added to a parent. (Defaults to None)
    duration : Optional[float], optional
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset in content, or 0
        if there is no content.) (Defaults to None)
    content : Optional[list[Event]], optional
        A list of Event objects to be added to the group. Content
        events with onsets of None are set to the offset of the
        previous event in the sequence. The first event onset is
        the specified group onset, or zero if onset is None.
        (Defaults to None)
    pack: bool
        If true, Events in content are adjusted to form a sequence
        where the first event onset is the specified group onset
        (where None means 0) and the onsets of other events are
        the offsets of the previous events in the sequence. A
        pack=True value changes the default behavior by overriding
        any existing onsets in the content. (Defaults to False
        because we do not want to automatically override onsets
        when they are specified.)

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : Optional[float]
        The onset (start) time. None represents "unknown" and to
        be determined when this object is added to a parent.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    """
    __slots__ = []

    def __init__(self, parent: Optional[EventGroup],
                 onset: Optional[float] = None, duration: Optional[float] = None,
                 content: Optional[list[Event]] = None, pack: bool = False):
        """Sequence represents a temporal sequence of music events.
        """
        super().__init__(parent, onset, duration, content, pack)


    @property
    def last_offset(self) -> float:
        """return the offset (end) time of the last element,
        or the onset (start) time if the Sequence is empty
        """
        if len(self.content) == 0:
            return self.onset
        else:  # last() is not None because len(content) > 0
            return self.last().offset  # type: ignore


    def pack(self, onset: float = 0.0) -> float:
        """Adjust the content to be sequential, begining with the
        parameter onset (defaults to 0), and each other object at
        an onset equal to the offset of the previous element. The
        duration of self is set to the offset of the last element.
        This method essentially arranges the content to eliminate
        gaps. pack() works recursively on elements that are
        EventGroups.

        Parameters
        ----------
        onset : float, optional
            The onset (start) time for this object. (Defaults to 0)

        Returns
        -------
        float
            duration of self
        """
        self.onset = onset
        for elem in self.content:
            elem.onset = onset
            if isinstance(elem, EventGroup):  # either Sequence or Concurrence
                elem.duration = elem.pack()   # type: ignore
            onset += elem.duration
        self.duration = onset
        return self.duration


class Concurrence(EventGroup):
    """Concurrence represents a temporally simultaneous collection
    of music events (but if elements have a non-zero onset, a Concurrence
    can represent events organized over time).  Thus, the main distinction
    between Concurrence and Sequence is that a Sequence can be constructed
    with pack=True to force sequential timing of the content. Note that a
    Sequence can have overlapping or entirely simultaneous Events as well.

    Parameters
    ----------
    parent : Optional[EventGroup], optional
        The containing object or None. (Defaults to None)
    onset : Optional[float], optional
        The onset (start) time. None means unknown, to be
        set when Sequence is added to a parent. (Defaults to None)
    duration : Optional[float], optional
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset in content, or 0
        if there is no content.)
    content : Optional[list[Event]], optional
        A list of Event objects to be added to the group. Content
        events with onsets of None are set to the offset of the
        concurrence, or zero if onset is None. (Defaults to None)

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : Optional[float]
        The onset (start) time. None represents "unknown" and to
        be determined when this object is added to a parent.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    """
    __slots__ = []

    def __init__(self, parent: Optional["EventGroup"] = None,
                 onset: Optional[float] = None,
                 duration: Optional[float] = None,
                 content: Optional[list[Event]] = None):
        """duration defaults 0
        """
        # initialize (super) EventGroup with numbers for onset and duration
        # but they will be adjusted before we return
        temp_onset = 0 if onset == None else onset
        # make a pass through the content. Compute onset values: replace onset
        # when onset == None. We also use the loop to compute the maximum
        # overall offset (max_offset) in case we need to set self.duration. Note
        # that max_offset is not necessarily the offset of the last Note due to
        # possible note overlap.
        max_offset = 0
        if duration == None and content:  # compute event onsets
            for elem in content:
                assert isinstance(elem, Event)
                assert elem.parent == None
                if elem._onset == None:
                    elem.onset = temp_onset
                max_offset = max(max_offset, elem.offset)
        if duration == None:  # compute duration from content
            duration = max_offset - temp_onset
        super().__init__(parent, onset, duration, content)
 

    def pack(self, onset: float = 0.0) -> float:
        """Adjust the content to onsets starting with the onset parameter
        (defaults to 0). The duration of self is set to the maximum offset
        of the content. This method essentially arranges the content to
        eliminate gaps. pack() works recursively on elements that are
        EventGroups.

        Parameters
        ----------
        onset : float, optional
            The onset (start) time for this object. (Defaults to 0)

        Returns
        -------
        float
            duration of self
        """
        self.onset = onset
        self.duration = 0
        for elem in self.content:
            elem.onset = onset
            if isinstance(elem, EventGroup):   # either Sequence or Concurrence
                elem.duration = elem.pack(onset)  # type: ignore
            self.duration = max(self.duration, elem.duration)
        return self.duration


class Chord(Concurrence):
    """A collection of notes played together.

    Typically, chords represent notes that would share a stem, and note
    start times and durations match the start time and duration of the
    chord, but none of this is enforced.  The order of notes is arbitrary.

    Normally, a Chord is a member of a Measure. There is no requirement
    that simultaneous or overlapping notes be grouped into Chords,
    so the Chord class is merely an optional element of music structure
    representation.

    See :class:`~amads.core.basics.EventGroup` documentation on
    construction styles.

    Representation note: An alternative representation would be to
    subclass Note and allow a list of pitches, which has the advantage
    of enforcing the shared onsets and durations. However, there can be
    ties connected differently to each note within the Chord, thus we
    use a Concurrence with Note objects as elements. Each Note.tie can
    be None (no tie) or tie to a Note in another Chord or Measure.

    Parameters
    ----------
    *args : Event
        The Event objects to be added to the group. Content
        events with onsets of None are set to the onset of the
        chord, or zero if onset is None. (Defaults to None)
    parent : Optional[EventGroup], optional
        The containing object or None. Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)
    onset : Optional[float], optional
        The onset (start) time. None means unknown, to be
        set when Sequence is added to a parent.  Must be passed
        as a keyword parameter due to `*args`. (Defaults to None)
    duration : Optional[float], optional
        The duration in quarters or seconds. (Defaults to None)
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.) Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : Optional[float]
        The onset (start) time.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    """
    __slots__ = []

    def __init__(self, *args: Event,
                 parent: Optional[EventGroup] = None,
                 onset: Optional[float] = None,
                 duration: Optional[float] = None):
        super().__init__(parent, onset, duration, list(args))


    def is_measured(self):
        """Test if Chord conforms to strict hierarchy of Chord-Note
        """
        for note in self.content:
            # Chord can (in theory) contain many object types, so we can
            # only rule out things that are outside of the strict hierarchy:
            if isinstance(note, (Score, Part, Staff, Measure, Rest, Chord)):
                return False
        return True



class Measure(Sequence):
    """A Measure models a musical measure (bar) and can contain many object
    types including Note, Rest, Chord, KeySignature, Timesignature and (in
    theory) custom Events. Measures are elements of a Staff.

    See EventGroup documentation on construction styles.


    Parameters
    ----------
    *args:  Event
        A variable number of Event objects to be added to the group.
    parent : Optional[EventGroup], optional
        The containing object or None. Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)
    onset : Optional[float], optional
        The onset (start) time. None means unknown, to be set when
        Sequence is added to a parent. Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)
    duration : Optional[float], optional
        The duration in quarters or seconds. Must be passed as a
        keyword parameter due to `*args`. (Defaults to 4)
    number : Optional[str], optional
        A string representing the measure number. Must be passed as
        a keyword parameter due to `*args`. (Defaults to None)
    pack : bool, optional
        If true, Events in `*args` are adjusted to form a sequence
        where the first event onset is the specified group onset
        (which defaults to 0) and the onset of other events is the
        offset of the previous event in the sequence. Must be passed
        as a keyword parameter due to `*args`. (Defaults to False).

    Attributes
    -----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : Optional[float]
        The onset (start) time. None represents "unknown" and to
        be determined when this object is added to a parent.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this Measure.
    number : Optional[str]
        A string representing the measure number if any.
    """
    __slots__ = ["number"]
    number: Optional[str]

    def __init__(self, *args: Event, parent: Optional[EventGroup] = None,
                 onset: Optional[float] = None, duration: float = 4,
                 number: Optional[str] = None,
                 pack: bool = False):
        super().__init__(parent, onset, duration, list(args), pack)
        self.number = number


    def __str__(self) -> str:
        """Short string representation
        """
        nstr = f", number={self.number}" if self.number else ""
        return f"Measure({self._event_times()}{nstr})"


    def is_measured(self) -> bool:
        """Test if Measure conforms to strict hierarchy of:
        Measure-(Note or Rest or Chord) and Chord-Note

        Returns
        -------
        bool
            True if the Measure conforms to normal hierarchy.
        """
        for item in self.content:
            # Measure can (in theory) contain many object types, so we can
            # only rule out things that are outside of the strict hierarchy:
            if isinstance(item, (Score, Part, Staff, Measure)):
                return False
            if isinstance(item, Chord) and not item.is_measured():
                return False
        return True



class Score(Concurrence):
    """A score is a top-level object representing a musical work.
    Normally, a Score contains Part objects, all with onsets zero.

    See EventGroup documentation on construction styles.

    Parameters
    ----------
    *args : Event
        A variable number of Event objects to be added to the group.
    onset : Optional[float], optional
        The onset (start) time. If unknown (None), onset will be set
        when the score is added to a parent, but normally, Scores do
        not have parents, so the default onset is 0. You can override
        this using keyword parameter (due to `*args`).
    duration : Optional[float], optional
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.) Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)
    time_map : TimeMap, optional
        A map from quarters to seconds (or seconds to quarters).
        Must be passed as a keyword parameter due to `*args`.
        (Defaults to None)


    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : float
        The onset (start) time.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    time_map : TimeMap
        A map from quarters to seconds (or seconds to quarters).
    _units_are_seconds : bool
        True if the units are seconds, False if the units are quarters.

    Additional attributes may be assigned, e.g. 'title', 'source_file',
    'composer', etc.
    """
    __slots__ = ["time_map", "_units_are_seconds"]
    time_map: TimeMap
    _units_are_seconds: bool

    def __init__(self, *args: Event,
                 onset: Optional[float] = 0,
                 duration: Optional[float] = None,
                 time_map: Optional["TimeMap"] = None):
        super().__init__(None, onset, duration, list(args))  # score parent is None
        self.time_map = time_map if time_map else TimeMap()
        self._units_are_seconds = False


    @classmethod
    def from_melody(cls,
                    pitches: list[Union[int, Pitch]],
                    durations: Union[float, list[float]] = 1.0,
                    iois: Optional[Union[float, list[float]]] = None,
                    onsets: Optional[list[float]] = None) -> "Score":
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
            onsets is None, takes values from the durations argument,
            assuming that notes are placed sequentially without overlap.
        onsets : list of float or None, optional
            Start times. Cannot be used together with iois.
            If both are None, defaults to using durations as IOIs.

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
        >>> notes[0].key_num
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

        Create three notes with explicit onsets:

        >>> score = Score.from_melody(
        ...     pitches=[60, 62, 64],  # C4, D4, E4
        ...     durations=1.0,  # quarter notes
        ...     onsets=[0.0, 2.0, 4.0],  # onset times 2 beats apart
        ... )
        >>> score.duration  # last note ends at t=5
        5.0
        """
        if len(pitches) == 0:
            return cls._from_melody(pitches=[], onsets=[], durations=[])

        if iois is not None and onsets is not None:
            raise ValueError("Cannot specify both iois and onsets")

        # Convert scalar durations to list
        if isinstance(durations, (int, float)):
            durations = [float(durations)] * len(pitches)

        # If onsets are provided, use them directly
        if onsets is not None:
            if len(onsets) != len(pitches):
                raise ValueError("onsets list must have same length as pitches")
            onsets = [float(d) for d in onsets]

        # Otherwise convert IOIs to onsets
        else:  # onsets is Nonex
            onsets = [0.0]
            # If no IOIs provided, use durations as default IOIs
            if iois is None:
                iois = durations[:-1]  # last duration not needed for IOIs
            # Convert scalar IOIs to list
            elif isinstance(iois, (int, float)):
                iois = [float(iois)] * (len(pitches) - 1)

            # Validate IOIs length
            if len(iois) != len(pitches) - 1:
                raise ValueError("iois list must have length len(pitches) - 1")

            # Convert IOIs to onsets
            onsets = [0.0]  # first note onsets at 0
            current_time = 0.0
            for ioi in iois:
                current_time += float(ioi)
                onsets.append(current_time)

        if not (len(pitches) == len(onsets) == len(durations)):
            raise ValueError("All input lists must have the same length")

        return cls._from_melody(pitches, onsets, durations)


    # the Score.units_are_quarters is the base case for the recursive
    # Event.units_are_quarters method.
    @property
    def units_are_quarters(self) -> bool:
        """True if the units are in quarters, False if in seconds.
        """
        return not self.units_are_seconds


    # the Score.units_are_seconds is the base case for the recursive
    # Event.units_are_seconds method.
    @property
    def units_are_seconds(self) -> bool:
        """True if the units are in seconds, False if in quarters.
        """
        return self._units_are_seconds


    def convert_to_seconds(self) -> None:
        """Convert the score to represent time in seconds.
        """
        if self.units_are_seconds:
            return
        super()._convert_to_seconds(self.time_map)
        self._units_are_seconds = True   # set the flag


    def convert_to_quarters(self) -> None:
        """Convert the score to represent time in quarters.
        """
        if not self.units_are_seconds:
            return
        super()._convert_to_quarters(self.time_map)
        self._units_are_seconds = False   # clear the flag


    def collapse_parts(self, part=None, staff=None, has_ties=True):
        """Merge the notes of selected Parts and Staffs into a flattened
        score with only one part, retaining only Notes. (Ties are merged.)

        The flatten() method is similar and generally preferred. It can
        flatten each Part while retaining (not merging) the Parts, or it
        can flatten all notes into one Part. Normally, you use this
        collapse_parts method to select an individual Staff or Part and
        flatten it to a single note sequence, thus it gives you
        finer-grained selection.

        If you are calling this method to extract notes separately for each
        Staff, it may do extra work. It might save some computation by
        performing a one-time

            score = score.merge_tied_notes()

        and calling this method with the parameter has_ties=False. 
        If has_ties is False, it is assumed without checking that
        each part.has_ties() is False, allowing this method to skip
        calls to part.merge_tied_notes() for each selected part.

        Parameters
        ----------
        part : Union[int, str, list[int], None], optional
            If part is not None, only notes from the selected part are
            included.
            part may be an integer to match a part number, or
            part may be a string to match a part instrument, or
            part may be a list with an index, e.g. [3] will select the 4th
            part (because indexing is zero-based).
        staff : Union[int, List[int], None], optional
            If staff is given, only the notes from selected staves are
            included.
            staff may be an integer to match a staff number, or
            staff may be a list with an index, e.g. [1] will select
            the 2nd staff.
            If staff is given without a part specification, an exception
            is raised.
            If staff is given and this is a flattened score (no staves),
            an exception is raised.
        has_ties : bool, optional
            Indicates the possibility of tied notes, which must be merged
            as part of flattening. If the parts are flattened already,
            setting has_ties=False will save some computation.

        Note
        ----
        The use of lists like [1] for part and staff index notation
        is not ideal, but parts can be assigned a designated number that
        is not the same as the index, so we need a way to select by
        designated number, e.g. 1, and by index, e.g. [1]. Initially, I
        used tuples, but they are error prone. E.g. part=(0) means part=0,
        so you would have to write collapse_parts(part=((0))). With [n]
        notation, you write collapse_parts(part=[0]) to indicate an index.
        This is prettier and less prone to error.

        """

        # Algorithm: Since we might be selecting individual Staffs and
        # Parts, we want to do selection first, then copy to avoid
        # modifying the source Score (self).
        content = []  # collect selected Parts/Staffs here
        score : Score = self.emptycopy()  # type: ignore
        parts : Generator = self.find_all(Part)
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
        new_part = Part(parent=score)
        if not has_ties:
            # because we avoided merging ties in parts, notes still belong
            # to the original score (self), so we need to copy them:
            copies = []  # copy all notes to here
            for note in notes:
                # rather than a possibly expensive insert into new_part, we
                # use sort (below) to construct the content of new_part.
                copies.append(note.copy())
            notes = copies
        # notes can be modified, so reuse them in the new_part:
        for note in notes:
            note.parent = new_part
        notes.sort(key=lambda x: (x.onset, x.pitch))
        new_part.content = notes
        # remove all the parts that we merged, leaving only new_part
        score.content = [new_part]
        return score


    def flatten(self, collapse=False):
        """Deep copy notes in a score to a flattened score consisting of
        only Parts containing Notes (Ties are merged.)

        See collapse_parts() to select specific Parts or Staffs and
        flatten them.

        Parameters
        ----------
        collapse : bool, optional
            If collapse is True, multiple parts are collapsed into a single
            part, and notes are ordered according to onset times. The resulting
            score contains one or more Parts, each containing only Notes.
        """
        # make a deep copy of the score, merging tied notes in the process.
        score : Score = self.merge_tied_notes()  # type: ignore
        # it is now safe to modify score because it has been copied
        if collapse:  # similar to Part.flatten() but we have to sort and
            # do some other extra work to put all notes into score
            # first, see if all parts have the same instrument. If so, we
            # will set instrument in the collapsed part. Otherwise, the
            # collapsed part will not have an instrument name.
            instrument = None
            instr_state = None
            for part in score.content:
                if isinstance(part, Part):
                    if instr_state is None:  # capture first instrument name
                        instrument = part.instrument
                        instr_state = "set"
                    elif instrument != part.instrument:
                        instr_state = "multiple"
                        instrument = None  # multiple instrument names found
                    else:  # this part.instrument is consistent
                        pass

            new_part = Part(parent=score, onset=score.onset,
                            instrument=instrument)
            notes : list[Note] = score.list_all(Note)  # type: ignore
            score.content = [new_part]  # remove all other parts and events
            for note in notes:
                note.parent = new_part
            # notes with equal onset times are sorted in pitch from high to low
            notes.sort(key=lambda x: (x.onset, x.pitch))

            new_part.content = notes  # type: ignore (List[Note] < List[Event])

            # set the Part duration so it ends at the max offset of all Parts:
            offset = max((part.offset for part in self.find_all(Part)), default=0)
            new_part.duration = offset - score.onset

        else:  # flatten each part separately
            for part in score.find_all(Part):
                part.flatten(in_place=True)  # type: ignore (part is a Part)
        return score


    @classmethod
    def _from_melody(cls,
                     pitches: list[Union[int, Pitch]],
                     onsets: list[float],
                     durations: list[float]) -> "Score":
        """Helper function to create a Score from preprocessed lists of pitches,
        onsets, and durations.

        All inputs must be lists of the same length, with numeric values already
        converted to float.
        """
        if not (len(pitches) == len(onsets) == len(durations)):
            raise ValueError("All inputs must be lists of the same length")
        if not all(isinstance(x, float) for x in onsets):
            raise ValueError("All onsets must be floats")
        if not all(isinstance(x, float) for x in durations):
            raise ValueError("All durations must be floats")

        # Check for overlapping notes
        for i in range(len(onsets) - 1):
            current_end = onsets[i] + durations[i]
            next_onset = onsets[i + 1]
            if current_end > next_onset:
                raise ValueError(
                        f"Notes overlap: note {i} ends at {current_end:.2f}" + \
                        f" but note {i + 1} starts at {next_onset:.2f}")

        score = cls()
        part = Part(parent=score)

        # Create notes and add them to the part
        for pitch, onset, duration in zip(pitches, onsets, durations):
            if not isinstance(pitch, Pitch):
                pitch = Pitch(pitch)
            Note(part, onset, duration, pitch)

        # Set the score duration to the end of the last note
        if len(onsets) > 0:
            score.duration = float(
                max(onset + duration for onset, duration in zip(onsets, durations))
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
        for part in self.find_all(Part):  # type: ignore (Part is an Event)
            part : Part
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
        score : Score = self.emptycopy()  # type: ignore
        for part in self.content:  # type: ignore (score contains Parts)
            if isinstance(part, Part):
                part : Part = part.merge_tied_notes(score)  # type: ignore
                part.remove_measures(score, has_ties=False)
                part.copy(score)
            else:  # non-Part objects are simply copied
                part.copy(score)
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

        print(" " * indent, self, sep="")
        self.time_map.show(indent + 4)
        for elem in self.content:
            elem.show(indent + 4)  # type: ignore (all Events have show())
        return self


    def get_sorted_notes(self):
        """Return a list of sorted notes with merged ties"""
        # score will have one Part, content of which is all Notes:
        return self.flatten(collapse=True).content[0].content  # type: ignore



class Part(EventGroup):
    """A Part models a staff or staff group such as a grand staff. For that
    reason, a Part contains one or more Staff objects. It should not contain
    any other object types. Parts are normally elements of a Score. Note that
    in a flattened score, a Part is a collection of Notes, not Staffs, and it
    should be organized more sequentially than concurrently, so the default
    assignment of onset times may not be appropriate.

    See EventGroup documentation on construction styles. Part is an EventGroup
    rather than a Sequence or Concurrence because in flattened scores, it acts
    like a Sequence of notes, but in full scores, it is like a Concurrence of
    Staff objects.

    Parameters
    ----------
    *args : Optional[Event], optional
        A variable number of Event objects to be added to the group.
    parent : Optional[EventGroup], optional
        The containing object or None. Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)
    onset : Optional[float], optional
        The onset (start) time. If unknown (None), it will be set
        when this Part is added to a parent. Must be passed as a
        keyword parameter due to `*args`. (Defaults to None)
    duration : Optional[float], optional
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.)  Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)
    number : Optional[str], optional
        A string representing the part number. (Defaults to None)
    instrument : Optional[str], optional
        A string representing the instrument name. (Defaults to None)
    pack : bool, optional
        If true, Events in `*args` are adjusted to form a sequence
        where the first event onset is the specified group onset
        (which defaults to 0) and the onset of other events is the
        offset of the previous event in the sequence. Must be passed
        as a keyword parameter due to `*args`. (Defaults to False)

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : float
        The onset (start) time.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    number : Union[str, None]
        A string representing the part number (if any). E.g. "22a".
    instrument : Union[str, None]
        A string representing the instrument name (if any).
    """
    __slots__ = ["number", "instrument"]
    number: Optional[str]
    instrument: Optional[str]

    def __init__(self, *args: Event,
                 parent: Optional[Score] = None,
                 onset: float = 0.0,
                 duration: Optional[float] = None,
                 number: Optional[str] = None,
                 instrument: Optional[str] = None,
                 pack: bool = False):
        super().__init__(parent, onset, duration, list(args), pack)
        if self.duration is None:  # compute default duration
            temp_onset = 0 if onset == None else onset
            max_offset = temp_onset
            for elem in self.content:
                max_offset = max(max_offset, elem.offset)
            self.duration = max_offset
        self.number = number
        self.instrument = instrument


    def __str__(self) -> str:
        """Short string representation
        """
        nstr = f", number={self.number}" if self.number else ""
        name = f", instrument={self.instrument}" if self.instrument else ""
        return f"Part({self._event_onset()}{nstr}{name})"


    def is_measured(self):
        """Test if Part is measured. Conforms to strict hierarchy of:
        Part-Staff-Measure-(Note or Rest or Chord) and Chord-Note.
        """
        for staff in self.content:  # type: ignore (Part contains Staffs)
            staff : Staff
            # only Staffs are expected, but things outside of the hierarchy
            # are allowed, so we only rule out violations of the hierarchy:
            if isinstance(staff, (Score, Part, Measure, Note, Rest, Chord)):
                return False
            if isinstance(staff, Staff) and not staff.is_measured():
                return False
        return True


    @classmethod
    def _find_tied_group(cls, notes, i):
        """find notes tied to notes[i]"""
        group = [notes[i]]  # start the list
        while notes[i].tie == "start" or notes[i].tie == "continue":
            offset = notes[i].offset
            key_num = notes[i].key_num  # allow ties to enharmonics
            candidates = []  # save indices of possible tied notes
            j = i + 1  # search for candidates starting at i + 1
            while j < len(notes) and notes[j].onset < offset + 0.0001:
                if (notes[j].key_num == key_num
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

        Parameters
        ----------

        in_place : bool, optional
            If in_place=True, assume Part already has no ties and can be
            modified. Otherwise, return a new Part where deep copies of
            tied notes are merged.
        """
        part = self if in_place else self.merge_tied_notes()
        notes : List[Note] = part.list_all(Note)  # type: ignore (Notes < Events)
        for note in notes:
            note.parent = part
        notes.sort(key=lambda x: (x.onset, x.pitch))
        part.content = notes  # type: ignore (List[Note] < List[Event])
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
        part : Part = (self.merge_tied_notes(score) 
                       if has_ties else self)  # type: ignore
        for staff in part.content:
            if isinstance(staff, Staff):
                staff.remove_measures()
        return part


class Staff(Sequence):
    """A Staff models a musical staff line extending through all systems.
    It can also model one channel of a standard MIDI file track. A Staff
    normally contains Measure objects and is an element of a Part.

    See EventGroup documentation on construction styles.

    Parameters
    ----------
    *args : Optional[Event], optional
        A variable number of Event objects to be added to the group.
    parent : Optional[EventGroup]
        The containing object or None. (Defaults to None)
    onset : Optional[float], optional
        The onset (start) time. If unknown (None), it will be set
        when this Staff is added to a parent. Must be passed as a
        keyword parameter due to `*args`. (Defaults to None)
    duration : Optional[float], optional
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.) Must be passed as a keyword
        parameter due to `*args`. (Defaults to None)
    number : Optional[int], optional
        The staff number. Normally, a Staff is given an integer
        number where 1 is the top staff of the part, 2 is the 2nd,
        etc. Must be passed as a keyword parameter due to `*args`.
        (Defaults to None)
    pack : bool, optional
        If true, Events in `*args` are adjusted to form a sequence
        where the first event onset is the specified group onset
        (which defaults to 0) and the onset of other events is
        the offset of the previous event in the sequence.
        Must be passed as a keyword parameter due to `*args`.
        (Defaults to False).

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : float
        The onset (start) time.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    number : Optional[int]
        The staff number. Normally a Staff is given an integer number
        where 1 is the top staff of the part, 2 is the 2nd, etc.
    """
    __slots__ = ["number"]
    number: Optional[int]

    def __init__(self, *args: Event,
                 parent: Optional[EventGroup] = None,
                 onset: Optional[float] = 0,
                 duration: Optional[float] = None,
                 number: Optional[int] = None,
                 pack: bool = False):
        super().__init__(parent, onset, duration, list(args), pack)
        self.number = number


    def __str__(self) -> str:
        """Short string representation
        """
        nstr = f", number={self.number}" if self.number else ""
        return f"Staff({self._event_onset()}{nstr})"


    def is_measured(self):
        """Test if Staff is measured. Conforms to strict hierarchy of:
        Staff-Measure-(Note or Rest or Chord) and Chord-Note)
        """
        for measure in self.content:
            # Staff can (in theory) contain many objects such as key signature
            # or time signature. We only rule out types that are
            # outside-of-hierarchy:
            if isinstance(measure, (Score, Part, Staff, Note, Rest, Chord)):
                return False
            if isinstance(measure, Measure) and not measure.is_measured():
                return False
        return True


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
