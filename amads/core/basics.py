# fmt: off
# flake8: noqa E129,E303
"""
Basic Symbolic Music Representation Classes

    from amads.core import *

Note: `amads.core` includes `amads.core.basics`, `amads.core.distribution`
and `amads.core.timemap`.

## Overview
The basic hierarchy of a score is [described here](../core.md).

<small>**Author**: Roger B. Dannenberg</small>

<a name=constructor-details>Constructor Details</a>
-------------------

 The safe way to construct a score is to
fully specify onsets for every Event.  These onsets are absolute and
will not be adjusted *provided that* the parent onset is also
specified.

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
from math import isclose
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Optional,
    TextIO,
    Type,
    Union,
    cast,
)

from amads.core.pitch import Pitch
from amads.core.timemap import TimeMap

__author__ = "Roger B. Dannenberg"


class Event:
    """A superclass for Note, Rest, EventGroup, and anything happening in time.

    Parameters
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    onset : float | None
        The onset (start) time. This can be an “idealized” time for a symbolic
        score or an actual “real” time from a performance. Default is None.
    duration : float
        The duration of the event in quarters or seconds. This can be zero for
        objects such as key signatures or time signatures.

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
                 onset: Optional[float], duration: float):
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


    def __repr__(self) -> str:
        """All Event subclasses inherit this to use str().

        Thus, a list of Events is printed using their __str__ methods
        """
        return str(self)

    
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


    def set(self, property : str, value : Any) -> "Event":
        """Set a named property on this Event.

        Every event can be extended with additional properties. Although
        Python objects are already extensible with new attributes, new
        attributes that are not set in `__init__` confuse type checkers
        and other tools, so every `Event` has an `info` attribute as a
        dictionary where additional, application-specific information can
        be stored. The `info` attribute is `None` to save space until the
        first property is set, so you should use `set` and `get` methods
        and avoid writing `event.info[property]`.
        
        Parameters
        ----------
        property : str
            The name of the property to set.
        value : Any
            The value to assign to the property.

        Returns
        -------
        Event
            returns this object (self)

        Examples
        --------
        >>> note = Note()
        >>> note.get("color", "no color")
        'no color'
        >>> _ = note.set("color", "red").set("harmonicity", 0.2)
        >>> (note.has("color"), note.has("shape"))
        (True, False)
        >>> (note.get("color"), note.get("harmonicity"))
        ('red', 0.2)
        """
        if self.info is None:
            self.info = {}
        self.info[property] = value
        return self


    def get(self, property : str, default : Any = None) -> Any:
        """Get the value of a property from this Event.

        See [set][amads.core.basics.Event.set] for more details.

        Parameters
        ----------
        property : str.
            The name of the property to get.
        default : Any
            The default value to return if the property is not found.
            
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

        See [set][amads.core.basics.Event.set] for more details.

        Parameters
        ----------
        property : str
            The name of the property to check.

        Returns
        -------
        bool
            True if the property exists, False otherwise.
        """
        return (self.info is not None) and (property in self.info)
        

    def time_shift(self, increment: float) -> "Event":
        """
        Change the onset by an increment.

        Parameters
        ----------
        increment : float
            The time increment (in quarters or seconds).

        Returns
        -------
        Event
            The object. This method modifies the `Event`.
        """
        self._onset += increment  # type: ignore
        return self


    def insert_copy_into(self,
                         parent: Optional["EventGroup"] = None) -> "Event":
        """
        Make a (mostly) deep copy of the `Event` and add to a new `parent`.

        `Pitch` objects are considered immutable and are shared rather
        than copied.

        Parameters
        ----------
        parent : Optional(EventGroup)
            The copied `Event` will be a child of `parent` if not `None`.
            The parent is modified by this operation.

        Returns
        -------
        Event
            A deep copy (except for parent and pitch) of the Event instance.
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

        Raises
        ------
        ValueError
            If the onset time is not set (None).
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

        This `event` must be in a `Score` (where `_units_are_seconds` is stored).

        Returns
        -------
        bool
            True iff the event's times are in seconds. If not in a score,
            False is returned.
        """
        return self.parent.units_are_seconds if self.parent else False


    @property
    def units_are_quarters(self) -> bool:
        """Check if the times are in quarters.

        This `event` must be in a `Score` (where `_units_are_seconds` is stored).

        Returns
        -------
        bool
            True iff the event's times are in quarters. If not in a score,
            False is returned.
        """
        return self.parent.units_are_quarters if self.parent else False


    def _convert_to_seconds(self, time_map: TimeMap) -> None:
        """Convert the event's duration and onset to seconds.

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
        """Convert the event's duration and onset to quarters.

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
        """Retrieve the Part containing this event.

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
        """Retrieve the Score containing this event.

        Returns
        -------
        Optional[Score]
            The Score containing this event or None if not found."""
        p = self.parent
        while (p is not None) and (not isinstance(p, Score)):
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


    @property
    def measure(self) -> Optional["Measure"]:
        """Retrieve the Measure containing this event

        Returns
        -------
        Optional[Measure]
            The Measure containing this event or None if not found."""
        p = self.parent
        while p and not isinstance(p, Measure):
            p = p.parent
        return p



class Rest(Event):
    """Rest represents a musical rest.

    A `Rest` is normally an element of a `Measure`.

    Parameters
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    onset : float
        The onset (start) time. An initial value of None might
        be assigned when the Note is inserted into an EventGroup.
    duration : float
        The duration of the rest in quarters or seconds.

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : float
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


    def show(self, indent: int = 0, file: Optional[TextIO] = None) -> "Rest":
        """Display the Rest information.

        Parameters
        ----------
        indent : int
            The indentation level for display.

        Returns
        -------
        Rest
            The Rest instance itself.
        """

        print(" " * indent, self, sep="", file=file)
        return self



class Note(Event):
    """Note represents a musical note.
    
    A `Note` is normally an element of a `Measure` in a full score,
    and an element of a `Part` in a flat score.

    Parameters
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    onset : float
        The onset (start) time. If None (default) is specified, a
        default onset will be calculated when the Note is inserted
        into an EventGroup.
    duration : float
        The duration of the note in quarters or seconds.
    pitch : Union[Pitch, int, float]
        A Pitch object or an integer MIDI key number that will be
        converted to a Pitch object. The default (60) represents middle C.
    dynamic : Optional[Union[int, str]]
        Dynamic level (integer MIDI velocity or arbitrary string).
    lyric : Optional[str]
        Lyric text.

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : Optional[float]
        The onset (start) time. None represents an unspecified onset.
    duration : float
        The duration of the note in quarters or seconds. See the
        property `tied_duration` for the duration of an entire group
        if the note is the first of a tied group of notes.
    pitch :  Pitch | None
        The pitch of the note. Unpitched notes have a pitch of None.
    dynamic : Optional[Union[int, str]]
        Dynamic level (integer MIDI velocity or arbitrary string).
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
        super().__init__(parent, onset, float(duration))
        if isinstance(pitch, (int, float, str)):
            pitch = Pitch(pitch)
        self.pitch = pitch
        self.dynamic = dynamic
        self.lyric = lyric
        self.tie = None


    def __deepcopy__(self, memo: dict) -> "Note":
        """Return a (mostly) deep copy of the Note instance.
        
        Except the pitch is shallow copied to avoid copying
        the entire Pitch object, which is considered immutable.

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
                for slot in base.__slots__:
                    if slot == "pitch":
                        result.pitch = self.pitch
                    else:
                        setattr(result, slot,
                                copy.deepcopy(getattr(self, slot), memo))

        return result

    @property
    def tied_duration(self) -> Union[float, int]:
        """Retrieve the duration of the note in quarters or seconds.

        If the note is the first note of a sequence of tied notes,
        return the duration of the entire sequence. However, if there are
        preceding notes tied to this note, they will not be considered
        part of the tied sequence. If you want to avoid processing notes
        that are tied to from earlier notes, you should either use
        [merge_tied_notes()][amads.core.basics.Score.merge_tied_notes] to
        eliminate them, or follow the `tie` links and add tied-to notes
        to a set as you traverse the score so you can ignore them when
        they are encountered. In some cases, notes can be tied across
        staves, in which case it might require two passes to (1) find
        all tied-to notes, and then (2) enumerate the rest of them.
        [merge_tied_notes()][amads.core.basics.Score.merge_tied_notes]
        handles this case properly.
        
        Returns
        -------
        float
            The duration of the note and those it is tied to directly
            or indirectly, in quarters or seconds. The sum of durations
            is returned without checking whether notes are contiguous.

        """
        duration = self.duration
        if self.tie is not None:  # recursively sum all tied durations:
            duration += self.tie.tied_duration
        return duration  # type: ignore (Note duration is always float)


    def __str__(self) -> str:
        """Short string representation.

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
                f"pitch={self.name_with_octave}/{self.key_num})")


    def show(self, indent: int = 0, file: Optional[TextIO] = None,
             tied: bool = False) -> "Note":
        """Print note information.
        
        Output includes pitch name, onset, duration, and optional
        tie, dynamic, and lyric information.

        Parameters
        ----------
        indent : int
            The indentation level for display.
        tied : bool
            Include information about ties.

        Returns
        -------
        Note
            The Note instance itself.
        """
        tie_info = ""
        if self.tie is not None:
            tie_info = " tied"
        tie_prefix = "  tied to " if tied else ""

        print(" " * indent, tie_prefix, self, tie_info, sep="", file=file)
        if self.tie:
            self.tie.show(indent + 2, tied=True, file=file)
        return self


    @property
    def step(self) -> str:
        """Retrieve the name of the pitch without accidental, e.g., "G".

        If the note is unpitched (pitch is None), return the empty string.
        """
        return self.pitch.step if self.pitch else ""


    @property
    def name(self) -> str:
        """Retrieve the name of the pitch with accidental, e.g., "Bb".

        If the note is unpitched (pitch is None), return the empty string.
        """
        return self.pitch.name if self.pitch else ""


    @property
    def name_with_octave(self) -> str:
        """Retrieve the name of the pitch with octave, e.g., A4 or Bb3.

        If the note is unpitched (pitch is None), return the empty string.
        """
        return self.pitch.name_with_octave if self.pitch else ""


    @property
    def pitch_class(self) -> int:
        """Retrieve the pitch class of the note, e.g., 0, 1, 2, ..., 11.

        If the note is unpitched (pitch is None), raise ValueError.
        """
        if self.pitch is None:
            raise ValueError("Unpitched note has no pitch class.")
        return self.pitch.pitch_class


    @pitch_class.setter
    def pitch_class(self, pc: int) -> None:
        """Set the pitch class of the note. 
        
        Keep the same octave, but not necessarily the same register.
        The octave number is preserved, but the alt is ignored.
        Use `simplest_enharmonic` to get a specific alt or to specify
        a sharp or flat preference.

        Parameters
        ----------
        pc : int
            The new pitch class value.
        """
        self.pitch = Pitch(pc + 12 * (self.octave + 1))


    @property
    def octave(self) -> int:
        """Retrieve the octave number of the note.

        The note name is based on `key_num - alt`, e.g., C4 has
        octave 4 while B#3 has octave 3. See also [Pitch.register]
        [amads.core.pitch.Pitch.register].

        If the note is unpitched (pitch is None), raise ValueError.

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
        if self.pitch is None:
            raise ValueError("Cannot set octave of unpitched note.")
        else:
            self.pitch = Pitch(self.pitch.key_num + (oct - self.octave) * 12,
                               self.pitch.alt)


    @property
    def key_num(self) -> float | int:
        """Retrieve the MIDI key number of the note, e.g., C4 = 60.

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
        """Return a `Pitch` representing the enharmonic.

        The enharmonic `Pitch`'s `alt` will be zero or have the opposite
        sign such that `alt` is minimized. E.g., the enharmonic of
        C-double-flat is A-sharp (not B-flat). If `alt` is zero, return
        a Pitch with alt of +1 or -1 if possible. Otherwise, return a
        Pitch with alt of -2.

        If the note is unpitched (pitch is None), raise ValueError.

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
        """Return a valid enharmonic Pitch with alt decreased, e.g., C#->Db.

        It follows that the alt is decreased by 1 or 2, e.g., C###
        (with `alt` = +3) becomes D# (with `alt` = +1).

        If the note is unpitched (pitch is None), raise ValueError.

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
        """Return a valid enharmonic Pitch with alt increased, e.g., Db->C#.

        It follows that the alt is increased by 1 or 2, e.g., D#
        (with `alt` = +1) becomes C### (with `alt` = +3).

        If the note is unpitched (pitch is None), raise ValueError.

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

        (See [simplest_enharmonic]
         [amads.core.pitch.Pitch.simplest_enharmonic].)

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



class TimeSignature:
    """TimeSignature is an element of Score.time_signatures.
    
    Contains time signature representation and a time in units that match
    Score._units_are_seconds.

    Parameters
    ----------
    time : float
        The time of the TimeSignature.
    upper : Optional[float]
        The “numerator” of the key signature: subdivisions units per
        measure, a number, which may be a fraction. Default is 4.
    lower : Optional[int]
        The “denominator” of the key signature: a whole number power
        of 2, e.g., 1, 2, 4, 8, 16, 32, 64, representing
        the symbol for one subdivision, e.g., 4 implies quarter note.
        Default is 4.

    Attributes
    ----------
    time : float
        The time of the TimeSignature
    upper : float
        The "numerator" of the key signature: subdivisions per measure.
    lower : int
        The "denominator" of the key signature: a whole number power of 2.
    """
    __slots__ = ["time", "upper", "lower"]
    upper: float
    lower: int

    def __init__(self, time: float, upper: float = 4.0, lower: int = 4):
        self.time = time
        self.upper = upper
        self.lower = lower


    def __str__(self) -> str:
        """Short string representation
        """
        upper = self.upper
        if int(upper) == upper:  # convert to integer for better printing
            upper = int(upper)   # but only if it is really an integer
        return (f"TimeSignature(at {self.time}, " +
                f"{self.upper}/{self.lower})")

    @property
    def quarters(self) -> float:
        """Get duration in quarters.

        Returns
        -------
        float
            Duration of one full measure of this time signature in quarters.
        """
        return self.upper * 4 / self.lower


    def show(self, indent: int = 0,
             file: Optional[TextIO] = None) -> "TimeSignature":
        """Display the TimeSignature information.

        Parameters
        ----------
        indent : int
            The indentation level for display.

        Returns
        -------
        TimeSignature
            The TimeSignature instance itself.
        """
        print(" " * indent, self, sep="", file=file)
        return self



class Clef(Event):
    """Clef is a zero-duration Event with clef information.

    Parameters
    ----------
    parent : Optional["EventGroup"]
        The containing object or None.
    onset : float
        The onset (start) time. An initial value of None might
        be assigned when the Clef is inserted into an EventGroup.
    clef : str
        The clef name, one of "treble", "bass", "alto", "tenor", 
        "percussion", "treble8vb" (Other clefs may be added later.)

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
        super().__init__(parent, onset, 0)
        if clef not in ["treble", "bass", "alto", "tenor",
                      "percussion", "treble8vb"]:
            raise ValueError(f"Invalid clef: {clef}")
        self.clef = clef


    def __str__(self) -> str:
        """Short string representation
        """
        return f"Clef({self._event_onset()}, {self.clef})"


    def show(self, indent: int = 0, file: Optional[TextIO] = None) -> "Clef":
        """Display the Clef information.

        Parameters
        ----------
        indent : int
            The indentation level for display.

        Returns
        -------
        Clef
            The Clef instance itself.
        """
        print(" " * indent, self, sep="", file=file)
        return self



class KeySignature(Event):
    """KeySignature is a zero-duration Event with key signature information.

    Parameters
    ----------
    parent : Optional["EventGroup"]
        The containing object or None.
    onset : float
        The onset (start) time. An initial value of None might
        be assigned when the KeySignature is inserted into an EventGroup.
    key_sig : int
        An integer representing the number of sharps (if positive)
        and flats (if negative), e.g., -3 for Eb major or C minor.

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


    def show(self, indent: int = 0,
             file: Optional[TextIO] = None) -> "KeySignature":
        """Display the KeySignature information.

        Parameters
        ----------
        indent : int
            The indentation level for display.

        Returns
        -------
        KeySignature
            The KeySignature instance itself.
        """
        print(" " * indent, self, sep="", file=file)
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
    group, the content onsets (even “known” ones) will all be shifted
    by the assigned onset. This happens *only* when changing an onset
    from None to a number. Subsequent changes to the group onset will
    not adjust the content onsets, which are considered absolute times
    once the group onset is known.

    EventGroup is subclassed to form Concurrence and Sequence. A
    Concurrence defaults to placing all events at onset 0, while
    Sequence defaults to placing events sequentially such that event
    inter-onset intervals are their durations. The EventGroup behaves
    like Concurrence, so the Concurrence implementation is minimal,
    while the Sequence needs several methods to override EventGroup
    behavior to support sequential behavior.

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
                 content: Optional[list[Event]]):
        # pass 0 for duration because Event constructor wants a number,
        # but we will set duration later based on duration parameter or
        # based on content if duration is None:
        super().__init__(parent=parent, onset=onset, duration=0)
        if content is None:
            content = []
        # member_onset is the default onset for children
        member_onset = 0 if onset is None else onset
        prev_onset = member_onset
        for elem in content:  # check and set parents
            if elem.parent and elem.parent != self:
                raise ValueError("Event already has a (different) parent")
            elem.parent = self  # type: ignore
            if elem._onset is None:
                elem.onset = member_onset
            elif elem._onset < prev_onset:
                raise ValueError("content is not in onset time order")
            # # Rounding can cause notes to get re-ordered when they should
            # # be simultaneous. This finds notes that are within 1 usec and
            # # overwrites the onsets after the first note so they are all
            # # equal. Then get_sorted_notes() will sort these by pitch:
            # elif elem._onset < prev_onset + 1.0e-6:
            #     elem._onset = prev_onset
            else:
                prev_onset = elem._onset

        if duration is None:  # compute duration from content
            max_offset = 0
            for elem in content:
                max_offset = max(max_offset, elem.offset)
            duration = max_offset
            if onset:
                duration = max_offset - onset
        self.duration = duration  # type: ignore (duration is now number)
        self.content = content


    @property
    def onset(self) -> float:
        """Retrieve the onset (start) time.

        If the onset is None, raise an exception. (Events can have None
        onset times, but they must be set before retrieval. onsets that
        are None are automatically set when the Event is added to an
        EventGroup.)
    
        Returns
        -------
        float
            The onset (start) time.

        Raises
        ------
        ValueError
            If the onset time is not set (None).
        """
        if self._onset is None:
            raise ValueError("Onset time is not set")
        return self._onset
    

    @onset.setter
    def onset(self, onset: float) -> None:
        """Set the onset time.

        When an unspecified onset time is set, the content is assumed to
        have offsets that reflect deltas from the beginning of this EventGroup.
        Changing the unspecified (None) onset to a non-zero value will treat
        the content onsets as deltas and shift them by the new onset so that
        the resulting content has correct absolute onset times.

        See [Constructor Details][amads.core.basics--constructor-details].
        """
        if onset is None:
            raise ValueError("onset must be a number. " +
                             "Only constructor can set onset to None.")
        if self._onset == None and onset != 0: # shift content
            for elem in self.content:
                elem.time_shift(onset)
        self._onset = onset


    def ismonophonic(self) -> bool:
        """
        Determine if content is monophonic (non-overlapping notes).

        A monophonic list of notes has no overlapping notes (e.g., chords).
        Serves as a helper function for `ismonophonic` and
        `parts_are_monophonic`.

        Returns
        -------
        bool
            True if the list of notes is monophonic, False otherwise.
        """
        prev = None
        notes = self.list_all(Note)
        # Sort the notes by start time
        notes.sort(key=lambda note: note.onset)
        # Check for overlaps
        for note in notes:
            if prev:
                # 0.01 is to prevent precision errors when comparing floats
                if note.onset - prev.offset < -0.01:
                    return False
            prev = note
        return True


    def time_shift(self, increment: float,
                   content_only: bool = False) -> "EventGroup":
        """
        Change the onset by an increment, affecting all content.

        Parameters
        ----------
        increment : float
            The time increment (in quarters or seconds).
        content_only: bool
            If true, preserves this container's time and shifts only
            the content.

        Returns
        -------
        Event
            The object. This method modifies the `EventGroup`.
        """
        if not content_only:
            self._onset += increment  # type: ignore (onset is now number)
        for elem in self.content:
            elem.time_shift(increment)
        return self


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


    def insert_emptycopy_into(self, 
                parent: Optional["EventGroup"] = None) -> "EventGroup":
        """Create a deep copy of the EventGroup except for content.

        A new parent is provided as an argument and the copy is inserted
        into this parent. This method is  useful for copying an
        EventGroup without copying its content.  See also
        [insert_copy_into][amads.core.basics.Event.insert_copy_into] to
        copy an EventGroup *with* its content into a new parent.

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
        c = self.insert_copy_into(parent)
        self.content = original_content
        return c  #type: ignore (c will always be an EventGroup)


    def expand_chords(self,
                      parent: Optional["EventGroup"] = None) -> "EventGroup":
        """Replace chords with the multiple notes they contain.

        Returns a deep copy with no parent unless parent is provided.
        Normally, you will call `score.expand_chords()` which returns a deep
        copy of Score with notes moved from each chord to the copy of the
        chord's parent (a Measure or a Part). The parent parameter is 
        primarily for internal use when `expand_chords` is called recursively
        on score content.

        Parameters
        ----------
        parent : EventGroup
            The new parent to insert the copied EventGroup into.

        Returns
        -------
        EventGroup
            A deep copy of the EventGroup instance with all
            Chord instances expanded.
        """
        group = self.insert_emptycopy_into(parent)
        for item in self.content:
            if isinstance(item, Chord):
                for note in item.content:  # expand chord
                    note.insert_copy_into(group)
            if isinstance(item, EventGroup):
                item.expand_chords(group)  # recursion for deep copy/expand
            else:
                item.insert_copy_into(group)  # deep copy non-EventGroup
        return group


    def find_all(self, elem_type: Type[Event]) -> Generator[Event, None, None]:
        """Find all instances of a specific type within the EventGroup.

        Assumes that objects of type `elem_type` are not nested within
        other objects of the same type. (The first `elem_type` encountered
        in a depth-first enumeration is returned without looking at any
        children in its `content`).

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


    def get_sorted_notes(self, has_ties: bool = True) -> List[Note]:
        """Return a list of sorted notes with merged ties.

        This should generally be called on Parts and Scores since
        in all other EventGroups, Events are in time order and
        Notes retrieved with `find_all()` or `list_all()` are in
        time order. However, `get_sorted_notes` *also* sorts notes
        into increasing pitch (`keynum`) where note onsets are equal.

        Parameters
        ----------
        has_ties: bool
            If True (default), copy the score, merge the ties, and
            return a list of these merged copies. If False, assume
            there are no ties and return a list of original notes.

        Raises
        ------
        ValueError
            If has_ties is False, but a tie is encountered.

        Returns
        -------
        list(Note)
            a list of sorted notes with merged ties
        """
        if has_ties:
            # score will have one Part, content of which is all Notes:
            return self.flatten(collapse=True).content[0].content  # type: ignore
        else:
            notes : List[Note] = cast(List[Note], self.list_all(Note))
            for note in notes:
                if note.tie is not None:
                    raise ValueError(
                            "tie found by get_sorted_notes with has_ties=False")
            notes.sort(key=lambda x: (x.onset, x.pitch))
            return notes


    def has_instanceof(self, the_class: Type[Event]) -> bool:
        """Test if EventGroup contains any instances of `the_class`.

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
        """Test if EventGroup (e.g., Score, Part, ...) has any `Rest` objects.

        Returns
        -------
        bool
            True iff the EventGroup contains any Rest objects.
        """
        return self.has_instanceof(Rest)


    def has_chords(self) -> bool:
        """Test if EventGroup (e.g., Score, Part, ...) has any Chord objects.

        Returns
        -------
        bool
            True iff the EventGroup contains any Chord objects.
        """
        return self.has_instanceof(Chord)


    def has_ties(self) -> bool:
        """Test if EventGroup (e.g., Score, Part, ...) has any tied notes.

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
        """Test if EventGroup (e.g., Score, Part, ...) has any Measures.

        Returns
        -------
        bool
            True iff the EventGroup contains any Measure objects.
        """
        return self.has_instanceof(Measure)


    def inherit_duration(self) -> "EventGroup":
        """Set the duration of this EventGroup according to maximum offset.

        The `duration` is set to the maximum offset (end) time of the
        children. If the EventGroup is empty, the duration is set to 0.
        This method modifies this `EventGroup` instance.

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
        """Insert an event.

        Sets the `parent` of `event` to this `EventGroup` and makes `event`
        be a member of this `EventGroup.content`. No changes are made to
        `event.onset` or `self.duration`. Insert `event` in `content` just
        before the first element with a greater onset. The method modifies
        this object (self).

        Parameters
        ----------
        event : Event
            The event to be inserted.

        Returns
        -------
        EventGroup
            The EventGroup instance (self) with the event inserted.

        Raises
        ------
        ValueError
            If event._onset is None (it must be a number)
        """
        assert not event.parent
        if event._onset is None:  # must be a number
            raise ValueError(f"event's _onset attribute must be a number")
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

        Because the `content` list is sorted by `onset`, the returned
        `Event` is simply the last element of `content`, but not
        necessarily the event with the greatest *`offset`*.

        Returns
        -------
        Optional[Event]
            The last event in the content list or None if the list is empty.
        """
        return self.content[-1] if len(self.content) > 0 else None


    def list_all(self, elem_type: Type[Event]) -> list[Event]:
        """Find all instances of a specific type within the EventGroup.

        Assumes that objects of type `elem_type` are not nested within
        other objects of the same type.  See also
        [find_all][amads.core.basics.EventGroup.find_all], which returns
        a generator instead of a list.

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
        """Create a new `EventGroup` with tied notes replaced by single notes.

        If ties cross staffs, the replacement is placed in the staff of the
        first note in the tied sequence. Insert the new `EventGroup` into
        `parent`.

        Ordinarily, this method is called on a Score with no parameters. The
        parameters are used when `Score.merge_tied_notes()` calls this method
        recursively on `EventGroup`s within the Score such as `Part`s and
        `Staff`s.

        Parameters
        ----------
        parent: Optional(EventGroup)
            Where to insert the result.

        ignore: Optional(list[Note])
            This parameter is used internally. Caller should not use
            this parameter.

        Returns
        -------
        EventGroup
            A copy with tied notes replaced by equivalent single notes.
        """
        # Algorithm: Find all notes, removing tied notes and updating
        # duration when ties are found. These tied notes are added to
        # ignore so they can be skipped when they are encountered.

        group = self.insert_emptycopy_into(parent)
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
                        # copy note into group:
                        event_copy = event.insert_copy_into(group)
                        event.tie = tied_note  # restore original event
                        # this is subtle: event.tied_duration (a property) will
                        # sum up durations of all the tied notes. Since
                        # event_copy is not tied, the sum of durations is
                        # stored on that one event_copy:
                        event_copy.duration = event.tied_duration
                    else:  # put the untied note into group
                        event.insert_copy_into(group)
            elif isinstance(event, EventGroup):
                event.merge_tied_notes(group, ignore)
            else:
                event.insert_copy_into(group)  # simply copy to new parent
        return group
    

    def pack(self, onset: float = 0.0, sequential : bool = False) -> float:
        """Adjust the content to onsets starting with the onset parameter.

        By default onsets are set to `onset` and the duration of self is set to
        the maximum duration of the content. pack() works recursively on
        elements that are EventGroups. Setting sequential to True implements
        sequential packing, where events are placed one after another.

        Parameters
        ----------
        onset : float
            The onset (start) time for this object.

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
                elem.duration = elem.pack(onset)  #type: ignore
            if sequential:
                onset += elem.duration
            else:
                self.duration = max(self.duration, elem.duration)
        if sequential:
            self.duration = onset - self.onset
        return self.duration


    def _quantize(self, divisions: int) -> "EventGroup":
        """"Since `_quantize` is called recursively on children, this method is
        needed to redirect `EventGroup._quantize` to `quantize`
        """
        return self.quantize(divisions)


    def quantize(self, divisions: int) -> "EventGroup":
        """Align onsets and durations to a rhythmic grid.

        Assumes time units are quarters. (See [Score.convert_to_quarters](
                basics.md#amads.core.basics.Score.convert_to_quarters).)

        Modify all times and durations to a multiple of divisions
        per quarter note, e.g., 4 for sixteenth notes. Onsets and offsets
        are moved to the nearest quantized time. Any resulting duration
        change is less than one quantum, but not necessarily less than
        0.5 quantum, since the onset and offset can round in opposite
        directions by up to 0.5 quantum each. Any non-zero duration that would
        quantize to zero duration gets a duration of one quantum since
        zero duration is almost certainly going to cause notation and
        visualization problems.
        
        Special cases for zero duration:

        1. If the original duration is zero as in metadata or possibly
               grace notes, we preserve that.
        2. If a tied note duration quantizes to zero, we remove the
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

        super()._quantize(divisions)
        # iterating through content is tricky because we may delete a
        # Note, shifting the content:
        i = 0
        while i < len(self.content):
            event = self.content[i]
            event._quantize(divisions)
            if event == self.content[i]:
                i += 1
            # otherwise, we deleted event so the next event to
            # quantize is at index i; don't incremenet i
        return self


    def remove(self, element: Event) -> "EventGroup":
        """Remove an element from the content list. 

        The method modifies this object (self).

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
        """Remove all Rest objects from content.

        Returns a deep copy with no parent unless parent is provided.

        Parameters
        ----------
        parent : EventGroup
            The new parent to insert the copied Event into.

        Returns
        -------
        EventGroup
            A deep copy of the EventGroup instance with all Rest
            objects removed.
        """
        # implementation detail: when called without argument, remove_rests
        # makes a deep copy of the subtree and returns the copy without a
        # parent. remove_rests calls itself recursively *with* a parameter
        # indicating that the subtree copy should be inserted into a
        # parent which is the new copy at the next level up. Of course,
        # we check for and ignore Rests so they are never copied.
        group = self.insert_emptycopy_into(parent)
        for item in self.content:
            if isinstance(item, Rest):
                continue  # skip the Rests while making deep copy
            if isinstance(item, EventGroup):
                item.remove_rests(group)  # recursion for deep copy
            else:
                item.insert_copy_into(group)  # deep copy non-EventGroup
        return group


    def __str__(self) -> str:
        """Short string representation
        """
        return f"{self.__class__.__name__}({self._event_times()})"


    def show(self, indent: int = 0,
            file: Optional[TextIO] = None) -> "EventGroup":
        """Print the EventGroup information.

        Parameters
        ----------
        indent : int
            The indentation level for display.

        Returns
        -------
        EventGroup
            The EventGroup instance itself.
        """
        print(" " * indent, self, sep="", file=file)
        for elem in self.content:
            elem.show(indent + 4, file=file)  # type: ignore (show exists)
        return self



class Sequence(EventGroup):
    """Sequence (abstract class) represents a temporal sequence of music events.

    Parameters
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    onset : Optional[float]
        The onset (start) time. None means unknown, to be
        set when Sequence is added to a parent.
    duration : Optional[float]
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset in content, or 0
        if there is no content.)
    content : Optional[list[Event]]
        A list of Event objects to be added to the group. Content
        events with onsets of None are set to the offset of the
        previous event in the sequence. The first event onset is
        the specified group onset, or zero if onset is None.

    Attributes
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    _onset : Optional[float]
        The onset (start) time. None represents “unknown” and to
        be determined when this object is added to a parent.
    duration : float
        The duration in quarters or seconds.
    content : list[Event]
        Elements contained within this collection.
    """
    __slots__ = []

    def __init__(self, parent: Optional[EventGroup],
                 onset: Optional[float] = None,
                 duration: Optional[float] = None,
                 content: Optional[list[Event]] = None):
        # if onset is given, we need to set all content onsets to form a
        # sequence before running super().__init__()
        if content is None:
            content = []
        prev_onset : float = 0.0
        prev_offset : float = 0.0
        if not onset is None:
            prev_onset = onset
            prev_offset = onset
        for elem in content:
            # parent will be set in EventGroup's constructor
            if elem._onset is None:
                 elem.onset = prev_offset
            elif elem.onset < prev_onset:
                raise ValueError("Event onsets are not in time order")
            prev_onset = elem.onset
            prev_offset = elem.offset
        # now that onset times are all set, we can run EventGroup's
        # constructor to set parents, duration, content
        super().__init__(parent, onset, duration, content)


    # last_offset is likely to be confusing or used incorrectly, e.g., it is
    # not the same as duration, not the same as the last sounding time of
    # any note (since earlier notes could overlap later notes), and it is
    # not even the offset of the last note since last_offset only looks at
    # the top-level of the Sequence content.
    # @property
    # def last_offset(self) -> float:
    #     """Return the offset (end) time of the last content element.
        
    #     If the Sequence is empty, return the Sequence onset (start) time.

    #     This function is similar in function to the `duration` property,
    #     but distinctly different. For example, a `Measure` could have a
    #     duration of 4 quarters, but the content could be just one half
    #     note, in which case the `last_offset` would be 2. If the measure
    #     ends with a tied note and ties are removed, the last note will
    #     be given a duration that extends beyond the end of the measure,
    #     and `measure.last_offset` will be greater than 4.

    #     Returns
    #     -------
    #     The offset time of the last event in this `EventGroup.content`.
    #     """
    #     if len(self.content) == 0:
    #         return self.onset
    #     else:  # last() is not None because len(content) > 0
    #         return self.last().offset  # type: ignore


    def pack(self, onset: float = 0.0, sequential: bool = True) -> float:
        """Adjust the content to be sequential.

        The resulting content will begin with the parameter `onset`
        (defaults to 0), and each other object will get an onset equal
        to the offset of the previous element. The duration of self is
        set to the offset of the last element.  This method essentially
        arranges the content to eliminate gaps. pack() works recursively
        on elements that are `EventGroups`.

        Be careful not to pack `Measures` (directly or through
        recursion) if the Measure's content durations do not add up to
        the intended quarters per measure.

        To override the sequential behavior, set the `sequential` 
        parameter to False.  In that case, pack behaves like the
        `Concurrence.pack()` method.

        The pack method alters self and its content in place.

        Parameters
        ----------
        onset : float
            The onset (start) time for this object.

        Returns
        -------
        float
            duration of self
        """
        return super().pack(onset, sequential)


class Concurrence(EventGroup):
    """Concurrence (abstract class) represents a group of simultaneous children.

    However, children can have a non-zero onset to represent events
    organized in time).  Thus, the main distinction between Concurrence
    and Sequence is that a Sequence can be constructed with pack=True to
    force sequential timing of the content. Note that a Sequence can
    have overlapping or entirely simultaneous Events as well.

    Parameters
    ----------
    parent : Optional[EventGroup]
        The containing object or None.
    onset : Optional[float]
        The onset (start) time. None means unknown, to be
        set when Sequence is added to a parent.
    duration : Optional[float]
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset in content, or 0
        if there is no content.)
    content : Optional[list[Event]]
        A list of Event objects to be added to the group. Content
        events with onsets of None are set to the offset of the
        concurrence, or zero if onset is None.

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
        super().__init__(parent, onset, duration, content)
 


class Chord(Concurrence):
    """A collection of notes played together.

    Typically, chords represent notes that would share a stem, and note
    start times and durations match the start time and duration of the
    chord, but none of this is enforced.  The order of notes is arbitrary.

    Normally, a Chord is a member of a Measure. There is no requirement
    that simultaneous or overlapping notes be grouped into Chords,
    so the Chord class is merely an optional element of music structure
    representation.

    See <a href="#constructor-details">Constructor Details</a>.

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
        chord, or zero if onset is None.
    parent : Optional[EventGroup]
        The containing object or None. Must be passed as a keyword
        parameter due to `*args`.
    onset : Optional[float]
        The onset (start) time. None means unknown, to be
        set when Sequence is added to a parent.  Must be passed
        as a keyword parameter due to `*args`.
    duration : Optional[float]
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.) Must be passed as a keyword
        parameter due to `*args`.

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


    def _is_well_formed(self):
        """Test if Chord conforms to strict hierarchy of Chord-Note
        """
        for note in self.content:
            # Chord can (in theory) contain many object types, so we can
            # only rule out things that are outside of the strict hierarchy:
            if isinstance(note, (Score, Part, Staff, Measure, Rest, Chord)):
                return False
        return True



class Measure(Sequence):
    """A Measure models a musical measure (bar).

    A Measure can contain many object types including Note, Rest, Chord,
    and (in theory) custom Events. Measures are elements of a Staff.

    See <a href="#constructor-details">Constructor Details</a>.

    Parameters
    ----------
    *args:  Event
        A variable number of Event objects to be added to the group.
    parent : Optional[EventGroup]
        The containing object or None. Must be passed as a keyword
        parameter due to `*args`.
    onset : Optional[float]
        The onset (start) time. None means unknown, to be set when
        Sequence is added to a parent. Must be passed as a keyword
        parameter due to `*args`.
    duration : Optional[float]
        The duration in quarters or seconds. Must be passed as a
        keyword parameter due to `*args`.
    number : Optional[str]
        A string representing the measure number. Must be passed as
        a keyword parameter due to `*args`.

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
                 number: Optional[str] = None):
        super().__init__(parent, onset, duration, list(args))
        self.number = number


    def __str__(self) -> str:
        """Short string representation
        """
        nstr = f", number={self.number}" if self.number else ""
        return f"Measure({self._event_times()}{nstr})"


    def _is_well_formed(self) -> bool:
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
            if isinstance(item, Chord) and not item._is_well_formed():
                return False
        return True


    def time_signature(self) -> TimeSignature:
        """Retrieve the time signature that applies to this measure.

        Returns
        -------
        TimeSignature
            The time signature from the score corresponding to the
            time of this measure.

        Raises
        ------
        ValueError
            If there is no Score or no onset time.
        """
        score = self.score
        if score is None:
            raise ValueError("Measure has no Score")
        else:  # find time sig at onset + a little to avoid rounding error:
            return score._find_time_signature(self.onset + 0.001)



class Score(Concurrence):
    """A Score (abstract class) represents a musical work.

    Normally, a Score contains Part objects, all with onsets zero, and
    has no parent.

    See <a href="#constructor-details">Constructor Details</a>.

    Additional properties may be assigned, e.g., 'title', 'source_file',
    'composer', etc. (See [set][amads.core.basics.Event.set].)

    Parameters
    ----------
    *args : Event
        A variable number of Event objects to be added to the group.
    onset : Optional[float]
        The onset (start) time. If unknown (None), onset will be set
        when the score is added to a parent, but normally, Scores do
        not have parents, so the default onset is 0. You can override
        this using keyword parameter (due to `*args`).
    duration : Optional[float]
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.) Must be passed as a keyword
        parameter due to `*args`.
    time_map : TimeMap
        A map from quarters to seconds (or seconds to quarters).
        Must be passed as a keyword parameter due to `*args`.

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
    time_signatures : list[TimeSignature]
        A list of all time signature changes
    _units_are_seconds : bool
        True if the units are seconds, False if the units are quarters.
    """
    __slots__ = ["time_map", "_units_are_seconds", "time_signatures"]
    time_map: TimeMap
    _units_are_seconds: bool

    def __init__(self, *args: Event,
                 onset: Optional[float] = 0,
                 duration: Optional[float] = None,
                 time_map: Optional["TimeMap"] = None,
                 time_signatures: Optional[List[TimeSignature]] = None):
        super().__init__(None, onset, duration, list(args))  # parent is None
        self.time_map = time_map if time_map else TimeMap()
        self.time_signatures = (
                time_signatures if time_signatures else [TimeSignature(0)])
        self._units_are_seconds = False


    def __str__(self) -> str:
        """Short string representation
        """
        return f"{self.__class__.__name__}({self._event_times()}, " + \
               f"units={'seconds' if self._units_are_seconds else 'quarters'})"
    

    @classmethod
    def from_melody(cls,
                    pitches: list[Union[Pitch, int, float, str]],
                    durations: Union[float, list[float]] = 1.0,
                    iois: Optional[Union[float, list[float]]] = None,
                    onsets: Optional[list[float]] = None,
                    ties: Optional[list[bool]] = None) -> "Score":
        """Create a Score from a melody specified by pitches and timing.

        Parameters
        ----------
        pitches : list of int or list of Pitch
            MIDI note numbers or Pitch objects for each note.
        durations : float or list of float
            Durations in quarters for each note. If a scalar value,
            it will be repeated for all notes.
        iois : float or list of float or None Inter-onset
            intervals between successive notes. If a scalar value,
            it will be repeated for all notes. If not provided and
            onsets is None, takes values from the durations argument,
            assuming that notes are placed sequentially without overlap.
        onsets : list of float or None
            Start times. Cannot be used together with iois.
            If both are None, defaults to using durations as IOIs.
        ties : list of bool or None
            If provided, a list of booleans indicating whether each
            note is tied to the next note. The last note's tie value
            is ignored. If None, no ties are created.

        Returns
        -------
        Score
            A new (flat) Score object containing the melody. If pitches
            is empty, returns a score with an empty part.

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
            return cls._from_melody(pitches=[], onsets=[], durations=[], ties=None)

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

        return cls._from_melody(pitches, onsets, durations, ties)


    def copy(self):
        """Make a deep copy.

        This is equivalent to [EventGroup.insert_copy_into](
            basics_more.md#amads.core.basics.EventGroup.insert_emptycopy_into),
        and provided
        because scores do not normally have a parent and there is nothing
        to "copy into."

        Returns
        -------
        Score
            a copy of the score.
        """
        return self.insert_copy_into(None)
        

    def emptycopy(self):
        """Copy score without content.

        See [insert_emptycopy_into](
             basics_more.md#amads.core.basics.EventGroup.insert_emptycopy_into).

        Since a Score does not normally have a parent, it is normal for the
        parent to be None, so `emptycopy()` is provided to make code more
        readable.

        Returns
        -------
        Score
            a copy of the score with no content
        """
        return self.insert_emptycopy_into(None)


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


    def append_time_signature(self, time_signature: TimeSignature) -> None:
        """Append a time signature change to the score.

        If there is already a time signature at the given time, it is
        replaced.

        Parameters
        ----------
        time_signature : TimeSignature
            The time signature to append.
        """
        # Remove any existing time signature at the same time
        if isclose(self.time_signatures[-1].time, time_signature.time,
                   abs_tol=0.003):
            self.time_signatures.pop()
        self.time_signatures.append(time_signature)


    def calc_differences(self, what: List[str]) -> List[List[Note]]:
        """Calculate inter-onset intervals (IOIs), IOI-ratios and intervals.

        This method is a convenience function that calls Part.calc_differences()
        on each Part of the Score. Since this method requires that Notes have
        no ties and are not concurrent (IOI == 0), the Score will normally be
        flat, which means only one Part.

        Parameters
        ----------
        what : list of str
            A list of strings indicating what differences to compute.
            Valid strings are: 'ioi' (for inter-onset intervals),
            'ioi_ratio' (for ratio of successive IOIs), and
            'interval' (for pitch intervals in semitones).
        
        Returns
        -------
        list of List[Note]
            A list of Notes from each Part with the requested difference
            properties set.
        """
        notes: List[List[Note]] = []
        parts: Generator = self.find_all(Part)
        for part in parts:
            part_notes = part.calc_differences(what)
            notes.append(part_notes)
        return notes
        

    def convert_to_seconds(self) -> None:
        """Convert the score to represent time in seconds.

        This function modifies Score without making a copy.
        """
        if self.units_are_seconds:
            return
        for ts in self.time_signatures:
            ts.time = self.time_map.quarter_to_time(ts.time)
        super()._convert_to_seconds(self.time_map)
        self._units_are_seconds = True   # set the flag


    def convert_to_quarters(self) -> None:
        """Convert the score to represent time in quarters.

        This function modifies Score without making a copy.
        """
        if not self.units_are_seconds:
            return
        for ts in self.time_signatures:
            ts.time = self.time_map.time_to_quarter(ts.time)
        super()._convert_to_quarters(self.time_map)
        self._units_are_seconds = False   # clear the flag


    def collapse_parts(self, part=None, staff=None, has_ties=True):
        """Merge the notes of selected Parts and Staffs.

        This function is used to extract only selected parts or staffs
        from a Score and return the data as a flat Score (only
        one part containing only Notes, with ties merged).

        The `flatten()` method is similar and generally preferred. Use
        this `collapse_parts()` only if you want to select an individual
        Staff (e.g., only the left hand when left and right appear as
        two staffs) or when you only want to process one Part and avoid
        the cost of flattening *all* Parts with `flatten()`.

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
        part : Union[int, str, list[int], None]
            If part is not None, only notes from the selected part are
            included:

            1. part may be an integer to match a part number (`number` is an
                  attribute of `Part`), or
            2. part may be a string to match a part instrument, or
            3. part may be a list with an index, e.g., [3] will select the 4th
                  part (because indexing is zero-based).
        staff : Union[int, List[int], None]
            If staff is given, only the notes from selected staves are
            included. Note that staff selection requires part selection.
            Thus, if staff is given without part, an Exception is raised.
            Also, if staff is given and this is a flat score (no staves),
            an Exception is raised.
            Staff selection works as follows:

            1. staff may be an integer to match a staff number, or
            2. staff may be a list with an index, e.g., [1] will select
                 the 2nd staff.
        has_ties : bool
            Indicates the possibility of tied notes, which must be merged
            as part of flattening. If the parts are flat already,
            setting has_ties=False will save some computation.

        Raises
        ------
        ValueError
            A ValueError is raised if:

            - staff is given without a part specification
            - staff is given and this is a flat score (no staves)

        Note
        ----
        The use of lists like [1] for part and staff index notation
        is not ideal, but parts can be assigned a designated number that
        is not the same as the index, so we need a way to select by
        designated number, e.g., 1, and by index, e.g., [1]. Initially, I
        used tuples, but they are error prone. E.g., part=(0) means part=0,
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
                copies.append(note.insert_copy_into(new_part))
            notes = copies
        # notes can be modified, so reuse them in the new_part:
        for note in notes:
            note.parent = new_part
        notes.sort(key=lambda x: (x.onset, x.pitch))
        new_part.content = notes
        # remove all the parts that we merged, leaving only new_part
        score.content = [new_part]
        return score

    

    def _find_time_signature(self, when : float) -> TimeSignature:
        """Look up TimeSignature in effect at time `when`

        Parameters
        ----------
        when : float
            The time to look up the time signature for. Be careful
            about rounding errors at time signature change times.

        Returns
        -------
        TimeSignature
            The time signature in effect at time `when`.
        """
        for ts in reversed(self.time_signatures):
            if ts.time <= when:
                return ts
        assert False, "No time signature found"

    
    def flatten(self, collapse=False):
        """Deep copy notes in a score to a flat score.

        A flat score consists of only Parts containing Notes
        (ties are merged).

        See [collapse_parts][amads.core.basics.Score.collapse_parts]
        to select specific Parts or Staffs and flatten them.

        Parameters
        ----------
        collapse : bool
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
            offset = max((part.offset for part in self.find_all(Part)),
                         default=0)
            new_part.duration = offset - score.onset

        else:  # flatten each part separately
            for part in score.find_all(Part):
                part.flatten(in_place=True)  # type: ignore (part is a Part)
        return score


    @classmethod
    def _from_melody(cls,
                     pitches: list[Union[Pitch, int, float, str]],
                     onsets: list[float],
                     durations: list[float],
                     ties: Optional[list[bool]]) -> "Score":
        """Helper function to create a Score from preprocessed lists of pitches,
        onsets, durations and ties.

        All inputs must be lists of the same length, with numeric values already
        converted to float, except for ties, which may be None or of any length
        of booleans (extras are ignored, missing values are treated as False).
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

        tied = False
        for pitch, onset, duration in zip(pitches, onsets, durations):
            if not isinstance(pitch, Pitch):
                pitch = Pitch(pitch)

            note = Note(part, onset, duration, pitch)
            if tied:
                prev_note.tie = note  # type: ignore (prev_note is Note)
            prev_note = note
            if ties and len(ties) > 0:
                tied = ties.pop(0)
            else:
                tied = False

        # Set the score duration to the end of the last note
        if len(onsets) > 0:
            score.duration = float(max(onset + duration for onset, duration
                                                   in zip(onsets, durations)))
        else:
            score.duration = 0.0

        return score


    def is_flat(self):
        """Test if Score is flat.

        a flat Score conforms to strict hierarchy of:
        Score-Part-Note with no tied notes.

        Returns
        -------
        bool
            True iff the score is flat.
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
        """Determine if score has been flattened into one part

        Returns
        -------
        bool
            True iff the score is flat and has one part.
        """
        return self.part_count() == 1 and self.is_flat()


    def is_well_formed_full_score(self) -> bool:
        """Test if Score is a well-formed full score.

        A well-formed full score is measured and conforms to a strict
        hierarchy of: Score-Part-Staff-Measure-(Note or Rest or Chord)
        and Chord-Note.

        Returns
        -------
        bool
            True iff the Score is a well-formed full Score.
        """
        for part in self.content:
            # only Parts are expected, but things outside of the hierarchy
            # are allowed, so we only rule out violations of the hierarchy:
            if isinstance(part, (Score, Staff, Measure, Note, Rest, Chord)):
                return False
            if isinstance(part, Part) and not part.is_well_formed_full_part():
                return False
        return True
    

    def note_containers(self):
        """Returns a list of non-empty note containers.

        For full (measured) Scores, these are the Staff objects.
        For flat Scores, these are the Part objects. This is mainly
        useful for extracting note sequences where each part or staff
        represents a separate sequence. This method will retrieve
        either parts or staffs, whichever applies. This implementation
        also handles a mix of Parts with and without Staffs, returning
        a list of whichever is the direct parent of a list of Notes.

        Returns
        -------
        list(EventGroup)
            list of (recursively) contained EventGroups that contain Notes
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
    

    def pack(self, onset: float = 0.0, sequential: bool = False) -> float:
        """Adjust onsets to pack events in the entire Score.

        This method modifies the Score in place, adjusting onsets
        so that events occur sequentially without gaps. By default,
        self is assumed to be a full score containing Parts with Staffs
        and Measures, so all contained Parts are concurrent, starting
        at `onset`, and Parts are also packed, making all Staffs start
        concurrently.

        If the Score is flat (Parts contain only Notes), set `sequential`
        to True, which overrides the packing of Parts, making their
        content sequential (Notes) instead of concurrent (Staffs).

        Note that the direct content of this Score starts concurrently
        at `onset` in either case. Pack is recursive, but it makes
        content concurrent in Concurrences like Chords and sequential
        is Sequences like Staffs and Measures.

        Parameters
        ----------
        onset : float
            The onset time for the Score after packing.
        sequential : bool
            If true, Parts are conconcurrently started at `onset`, but
            each Part is packed sequentially, so that the first event
            in each Part starts at `onset`, and subsequent events
            start at the offset of the previous event. Use False for
            full scores (with Parts and Staffs) and True for flat scores
            (with Parts containing only Notes).
        Returns
        -------
        Score
            The modified Score instance itself.
        """
        dur = 0.0
        for part in self.content:  # type: ignore (score contains Parts)
            part.onset = onset
            if isinstance(part, Part):
                dur = max(dur, part.pack(onset, sequential))
            # anything but Part follows default packing behavior:
            elif isinstance(part, EventGroup):
                dur = max(dur, part.pack(onset))
            else:
                dur = max(dur, part.duration)
        self.duration = dur
        return dur
    

    def part_count(self):
        """How many parts are in this score?
        
        Returns
        -------
        int
            The number of parts in this score.
        """
        return len(self.list_all(Part))


    def parts_are_monophonic(self) -> bool:
        """
        Determine if each part of a musical score is monophonic.

        A monophonic part has no overlapping notes (e.g., chords).

        Returns
        -------
        bool
            True if each part is monophonic, False otherwise.
        """
        for part in self.find_all(Part):
            part = cast(Part, part)
            if not part.ismonophonic():
                return False
        return True


    def remove_measures(self) -> "Score":
        """Create a new Score with all Measures removed.

        Preserves Staffs in the hierarchy. Notes are "lifted" from Measures
        to become direct content of their Staff. The result satisfies neither
        `is_flat()` nor `is_well_formed_full_score()`, but it could be useful
        in preserving a separation between staves. See also `collapse_parts`,
        which can be used to extract individual staves from a score. The result
        will have ties merged. (If you want to preserve ties and access the
        notes in a Staff, consider using find_all(Staff), and then for each staff,
        find_all(Note), but note that ties can cross between staves.)

        Returns
        -------
        Score
            A new Score instance with all Measures removed.
        """
        score : Score = self.emptycopy()  # type: ignore
        for part in self.content:  # type: ignore (score contains Parts)
            if isinstance(part, Part):
                # puts a copy of Part with merged_notes into score and
                # then removes measures from each staff:
                part.remove_measures(score)
            else:  # non-Part objects are simply copied
                part.insert_copy_into(score)
        return score


    def show(self, indent: int = 0,
             file: Optional[TextIO] = None) -> "Score":
        """Print the Score information.

        Parameters
        ----------
        indent : int
            The indentation level for display.

        Returns
        -------
        Score
            The Score instance itself.
        """

        print(" " * indent, self, sep="", file=file)
        self.time_map.show(indent + 4, file=file)

        print(" " * indent, "    time_signatures [", sep="", end="") 
        need_blank = ""
        col = indent + 21
        for ts in self.time_signatures:
            tss = str(ts)
            if len(tss) + col > 79:
                print("\n", " " * (indent + 20), end="")
                col = indent + 21
            print(need_blank, tss, sep="", end="")
            col += len(tss)
            need_blank = " "
        print("]")  # newline after time signatures
    
        for elem in self.content:
            elem.show(indent + 4, file=file)  # type: ignore
            # type ignore because (all Events have show())
        return self



class Part(EventGroup):
    """A Part models a staff or staff group such as a grand staff.

    For that reason, a Part contains one or more Staff objects. It should
    not contain any other object types. Parts are normally elements of a
    Score. Note that in a flat score, a Part is a collection of Notes,
    not Staffs, and it should be organized more sequentially than
    concurrently, so the default assignment of onset times may not be
    appropriate.

    See <a href="#constructor-details">Constructor Details</a>.

    Part is an EventGroup rather than a Sequence or Concurrence because
    in flat scores, it acts like a Sequence of notes, but in full
    scores, it is like a Concurrence of Staff objects.

    Parameters
    ----------
    *args : Optional[Event]
        A variable number of Event objects to be added to the group.
        parent : Optional[EventGroup]
        The containing object or None. Must be passed as a keyword
        parameter due to `*args`.
    onset : Optional[float]
        The onset (start) time. If unknown (None), it will be set
        when this Part is added to a parent. Must be passed as a
        keyword parameter due to `*args`.
    duration : Optional[float]
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.)  Must be passed as a keyword
        parameter due to `*args`.
    number : Optional[str]
        A string representing the part number.
    instrument : Optional[str]
        A string representing the instrument name.        
    flat : bool
        If true, content in `*args` with onset None are modified to start
        at the offset of the previous note (or at `onset` if this is the
        first Event in `*args`, or at 0.0 if `onset` is unspecified).
        Otherwise, this is assumed to be a Part in a full score, `*args`
        is assumed to contain `Staff`s, and their default onset times are
        given `onset` by onset (or 0.0 if `onset` is unspecified). This 
        must be passed as a keyword argument due to `*args`.

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
        A string representing the part number (if any). E.g., "22a".
    instrument : Union[str, None]
        A string representing the instrument name (if any).

    Notes
    -----
        Standard MIDI File tracks often have text instrument names in
        type 4 meta events. These are stored in the `instrument` attribute.
        Tracks often contain events for a single MIDI channel and a single
        “program” that is another representation of “instrument.” In fact,
        the `pretty_midi` library considers MIDI program to be a property
        of the track rather than a timed event within the track (many
        sequencers use this model as well). Therefore, if there is a
        single MIDI program in a track (or an AMADS Part), the program
        number (int) is stored in `info` using the key `"midi_program"`.
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
                 flat: bool = False):
        content = list(args)
        if flat:  # adjust onsets to form a sequence (must be done before
            prev_onset : float = 0.0  # onset of previous note
            prev_offset : float = 0.0  # offset of previous note
            if not onset is None:
                prev_onset = onset
                prev_offset = onset
            for elem in content:
                if elem.parent and elem.parent != self:
                    raise ValueError("Event already has a parent")
                elem.parent = self  # type: ignore
                if elem.onset is None:
                    elem.onset = prev_offset
                elif elem.onset < prev_onset:
                    raise ValueError("Event onsets are not in time order")
                prev_onset = elem.onset
                prev_offset = elem.offset
            packed_args = []
        super().__init__(parent, onset, duration, content)
        self.number = number
        self.instrument = instrument


    def __str__(self) -> str:
        """Short string representation
        """
        nstr = f", number={self.number}" if self.number else ""
        name = f", instrument={self.instrument}" if self.instrument else ""
        return f"Part({self._event_times()}{nstr}{name})"


    def is_well_formed_full_part(self):
        """Test if Part is measured and well-formed.

        Part must conform to a strict hierarchy of:
        Part-Staff-Measure-(Note or Rest or Chord) and Chord-Note.
        """
        for staff in self.content:  # type: ignore (Part contains Staffs)
            staff : Staff
            # only Staffs are expected, but things outside of the hierarchy
            # are allowed, so we only rule out violations of the hierarchy:
            if isinstance(staff, (Score, Part, Measure, Note, Rest, Chord)):
                return False
            if isinstance(staff, Staff) and not staff._is_well_formed():
                return False
        return True


    def flatten(self, in_place=False):
        """Build a flat Part where content will consist of notes only.

        Parameters
        ----------
        in_place : bool
            If in_place=True, assume Part already has no ties and can be
            modified. Otherwise, return a new Part where deep copies of
            tied notes are merged.
            
        Returns
        -------
        Part
            a new part that has been flattened
        """
        part = self if in_place else self.merge_tied_notes()
        notes : List[Note] \
              = part.list_all(Note)  # type: ignore (Notes < Events)
        for note in notes:
            note.parent = part
        notes.sort(key=lambda x: (x.onset, x.pitch))
        part.content = notes  # type: ignore (List[Note] < List[Event])
        return part


    def is_flat(self):
        """Test if Part is flat (contains only notes without ties).
        
        Returns
        -------
        bool
            True iff the Part is flat
        """
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
        """Return a Part with all Measures removed.

        Preserves Staffs in the hierarchy. Notes are “lifted” from Measures
        to become direct content of their Staff. Uses `merge_tied_notes()`
        to copy this Part unless `has_ties` is False, in which case
        there must be no tied notes and this Part is modified. (Note: it is
        harmless for `has_ties` to be True even if there are no ties. This
        will simply copy the Part before removing measures.)

        Parameters
        ----------
        score : Union[Score, None]
            The Score instance (if any) to which the new Part will be added.
        has_ties : bool
            If False, assume this is a copy we are free to modify,
            there are tied notes, and this Part is already contained
            by `score`. If True, this Part will be copied into `score`.

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


    def calc_differences(self, what: List[str]) -> List[Note]:
        """Calculate inter-onset intervals (IOIs), IOI-ratios and intervals.

        This method modifies the Part in place, calculating several
        differences between notes. Onset differences (IOIs) are the
        time differences between a Note's onset and the onset of the
        previous Note in the same Part (regardless of Staff). The IOI
        of the first Note in the Part is set to None. The IOI values
        are computed when `what` contains "ioi" or "ioi_ratio" and
        stored as `"ioi"` in the Note's `info` dictionary.

        The IOI-ratio of a Note is the ratio of its IOI to the IOI of
        the previous Note. The IOI-ratios of the first two Notes are set
        to None. The IOI-ratio values are computed when `what` contains
        "ioi_ratio" and stored as `"ioi_ratio"` in the Note's `info`
        dictionary.

        The pitch interval of a Note is the difference in semitones between
        its pitch and the pitch of the previous Note in the same Part. The
        interval of the first Note in the Part is set to None. The interval
        values are computed when `what` contains "interval" and stored
        as `"interval"` in the Note's `info` dictionary.

        Note that this method assumes that the Part has no concurrent
        Notes (IOI == 0) and no ties. In either case, a ValueError is raised.

        Parameters
        ----------
        what : list of str
            A list of strings indicating what differences to compute.
            Valid strings are: 'ioi' (for inter-onset intervals),
            'ioi_ratio' (for ratio of successive IOIs), and
            'interval' (for pitch intervals in semitones).

        Raises
        ------
        ValueError
            If there are tied notes or concurrent notes in the Part or if
            `what` does not contain any of "ioi", "ioi_ratio" or "interval".

        Returns
        -------
        List[Note]
            The sorted list of Notes with calculated IOIs and IOI-ratios.
        """
        # this will raise an exception if there are ties:
        notes : List[Note] = self.get_sorted_notes(has_ties=False)
        do_ioi = "ioi" in what or "ioi_ratio" in what
        do_interval = "interval" in what
        do_ioi_ratio = "ioi_ratio" in what
        if not (do_ioi or do_interval or do_ioi_ratio):
            raise ValueError(
                    "what must contain 'ioi', 'ioi_ratio' or 'interval'")
        if len(notes) == 0:
            return []  # nothing to do
        else:
            if do_ioi:
                notes[0].set("ioi", None)
            if do_ioi_ratio:
                notes[0].set("ioi_ratio", None)
            if do_interval:
                notes[0].set("interval", None)
    
        prev_ioi : Optional[float] = None
        prev_note : Note = notes[0]
        for note in notes[1 : ]:
            if do_ioi:
                ioi = note.onset - prev_note.onset
                if ioi <= 0:
                    raise ValueError(
                            "Part is not monophonic; cannot compute IOIs")
                note.set("ioi", ioi)
            if do_ioi_ratio:
                if prev_ioi is None:
                    note.set("ioi_ratio", None)
                else:  # ignore typing because ioi is bound earlier:
                    note.set("ioi_ratio", ioi / prev_ioi)  # type: ignore
                prev_ioi = ioi  # type: ignore (ioi is bound if do_ioi) 
            if do_interval:
                note.set("interval", note.key_num - prev_note.key_num)
            prev_note = note
        return notes



class Staff(Sequence):
    """A Staff models a musical staff.

    This can also model one channel of a standard MIDI file track. A Staff
    normally contains Measure objects and is an element of a Part.

    See <a href="#constructor-details">Constructor Details</a>.

    Parameters
    ----------
    *args : Optional[Event]
        A variable number of Event objects to be added to the group.
    parent : Optional[EventGroup]
        The containing object or None.
    onset : Optional[float]
        The onset (start) time. If unknown (None), it will be set
        when this Staff is added to a parent. Must be passed as a
        keyword parameter due to `*args`.
    duration : Optional[float]
        The duration in quarters or seconds.
        (If duration is omitted or None, the duration is set so
        that self.offset ends at the max offset of args, or 0
        if there is no content.) Must be passed as a keyword
        parameter due to `*args`.
    number : Optional[int]
        The staff number. Normally, a Staff is given an integer
        number where 1 is the top staff of the part, 2 is the 2nd,
        etc. Must be passed as a keyword parameter due to `*args`.

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
                 number: Optional[int] = None):
        super().__init__(parent, onset, duration, list(args))
        self.number = number


    def __str__(self) -> str:
        """Short string representation
        """
        nstr = f", number={self.number}" if self.number else ""
        return f"Staff({self._event_times()}{nstr})"


    def _is_well_formed(self):
        """Test if Staff is well-formed, conforming to a strict hierarchy of:
        Staff-Measure-(Note or Rest or Chord) and Chord-Note)
        """
        for measure in self.content:
            # Staff can (in theory) contain many objects such as key signature
            # or time signature. We only rule out types that are
            # outside-of-hierarchy:
            if isinstance(measure, (Score, Part, Staff, Note, Rest, Chord)):
                return False
            if isinstance(measure, Measure) and not measure._is_well_formed():
                return False
        return True


    def remove_measures(self) -> "Staff":
        """Modify Staff by removing all Measures.

        Notes are “lifted” from Measures to become direct content of this
        Staff. There is no special handling for notes tied to or from another
        Staff, so normally this method should be used only on a Staff where
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
