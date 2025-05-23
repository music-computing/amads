# pitch.py -- the Pitch class
# fmt: off
# flake8: noqa E129,E303


import functools
from dataclasses import dataclass
from math import floor
from numbers import Number
from typing import Optional, Tuple, Union

from amads.core.vectors_sets import multiset_to_vector, weighted_to_indicator

LETTER_TO_NUMBER = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


@functools.total_ordering
class Pitch:
    """A Pitch represents a symbolic musical pitch. It has two parts:
    The `key_num` is a number that corresponds to the MIDI convention
    where C4 is 60, C# is 61, etc. The alt is an alteration, where +1
    represents a sharp and -1 represents a flat. Alterations can also
    be, for example, 2 (double-sharp) or -0.5 (quarter-tone flat).
    The symbolic note name is derived by *subtracting* `alt` from `key_num`.
    e.g., C#4 has `key_num=61`, `alt=1`, so 61-1 gives us 60, corresponding
    to note name C. A Db has the same `key_num=61`, but alt=-1, and 61-(-1)
    gives us 62, corresponding to note name D. There is no representation
    for the "natural sign" (other than `alt=0`, which could imply no
    accidental) or "courtesy accidentals."  Because accidentals normally
    "stick" within a measure or are implied by key signatures, accidentals
    are often omitted in the score presentation. Nonetheless, these
    implied accidentals are encoded in the `alt` attribute and `key_num`
    is the intended pitch with the accidental applied.

    Parameters
    ----------
        pitch : Union[float, str, None], optional
            MIDI key_num or string Pitch name. Syntax is A-G followed by
            accidentals followed by octave number.
            (Defaults to 60)
        alt: Union[float, None], optional
            If pitch is a number, alt is an optional alteration (Defaults to 0).
            If `pitch - alt` does not result in a diatonic pitch number, alt is
            adjusted, normally choosing spellings C#, Eb, F#, Ab, and Bb.
            If pitch is a string, alt is the optional octave (an integer)
            (Overridden by any octave specification in pitch,
            otherwise defaults to -1, which yields pitch class `key_num`s 0-11).
        accidental_chars: Union[str, None], optional
            Allows parsing of pitch names with customized accidental characters.
            (Defaults to None, which admits '♭', 'b' or '-' for flat, and
            '♯', '#', and '+' for sharp, but does not accept 'f' and 's'.

    Attributes
    ----------
        key_num : float
            MIDI key number, e.g., C4 = 60, generalized to float.
        alt : float
            Alteration, e.g., flat = -1.

    Properties
    ----------
        step : str
            The name of the pitch without octave or accidentals, e.g., A or G.
        name : str
            The string representation of the pitch name, including accidentals.
        name_with_octave : str
            The string representation of the pitch name with octave.
        octave : int
            The octave number of the note name, based on `key_num` and `alt`.
        pitch_class : int
            The pitch class of the note
        register : int
            The absolute octave of `key_num`, e.g. octave of B#3 is 4.

    Examples
    --------
    >>> p = Pitch(64)
    >>> p
    Pitch(name='E4', key_num=64)

    >>> p.octave
    4

    >>> p = Pitch("E4")
    >>> p.octave
    4

    >>> p = Pitch("F#################2")
    >>> p.alt
    17

    >>> p.octave
    2

    >>> p = Pitch("E--------------------4")
    >>> p.alt
    -20

    >>> p.octave
    4

    >>> p.register
    2
    """
    __slots__ = ["key_num", "alt"]

    def _fix_alteration(self) -> None:
        """Fix the alteration to ensure it is a valid value, i.e.
        that `(key_num - alt) % 12` denotes one of {C D E F G A B}.
        """
        unaltered = self.key_num - self.alt
        if int(unaltered) != unaltered:  # not a whole number
            # fix alt so that unaltered is an integer
            diff = unaltered - round(unaltered)
            self.alt -= diff
            unaltered = round(self.key_num - self.alt)
        # make sure pitch class of unaltered is in {C D E F G A B}
        pc = unaltered % 12
        if pc in [6, 1]:  # F#->F, C#->C
            self.alt += 1
        elif pc in [10, 3, 8]:  # Bb->B, Eb->E, Ab->A
            self.alt -= 1
        # now `(key_num + alt) % 12` is in {C D E F G A B}


    def __init__(self, pitch: Union["Pitch", Number, str] = 60,
                 alt: Union[Number, None] = None,
                 accidental_chars: Optional[str] = None):
        if isinstance(pitch, str):
            self.key_num, self.alt = Pitch.from_name(pitch, alt, accidental_chars)
        elif isinstance(pitch, Pitch):
            self.key_num = pitch.key_num
            self.alt = pitch.alt
        else:
            # this will raise a ValueError if pitch is not some kind of number:
            pitch = float(pitch)  # converts numpy.int64, nympy.floating, etc.
            if pitch.is_integer():  # for nicer printing, represent "exact" 12-TET
                pitch = int(pitch)  # pitch numbers as integers.
            self.key_num = pitch
            self.alt = (0 if alt is None else alt)
            self._fix_alteration()


    def __repr__(self):
        return f"Pitch(name='{self.name_with_octave}', key_num={self.key_num})"

    
    def as_tuple(self):
        """Return a tuple representation of the `Pitch` instance.

        Returns
        -------
        tuple
            A tuple containing the `key_num` and `alt` values.
        """
        return (self.key_num, self.alt)


    def __eq__(self, other):
        """Check equality of two Pitch instances. Pitches are equal if
        both `key_num` and `alt` are equal. Enharmonics are therefore
        not equal, but enharmonic equivalence can be written simply as
        `p1.key_num == p2.key_num`

        Parameters
        ----------
        other : Pitch
            The other Pitch instance to compare with.

        Returns
        -------
        bool
            True if the `key_num` and `alt` values are equal, False otherwise.
        """
        return self.as_tuple() == other.as_tuple()


    def __hash__(self) -> int:
        """Return a hash value for the Pitch instance.

        Returns
        -------
        int
            A hash value representing the Pitch instance.
        """
        return hash(self.as_tuple())


    def __lt__(self, other) -> bool:
        """Check if this Pitch instance is less than another Pitch instance.
        Pitches are compared first by `key_num` and then by `alt`. Pitches
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
        return (self.key_num, -self.alt) < (other.key_num, -other.alt)


    @classmethod
    def from_name(cls, name: str,
                  octave: Optional[float],
                  accidental_chars: Optional[str] = None
                  ) -> Tuple[float, float]:
        """
        Converts a string like 'Bb' to the corresponding pitch (10)
        and alteration, e.g., 'Bb' returns (10, -1).
        If the string has an octave number or octave is given, the
        octave will be applied, e.g., "C4" yields (60, 0). octave takes
        effect if it is a number and name does not include an octave.
        If both `name` has no octave and `octave` is None, the octave is
        -1, yielding pitch class numbers 0-11.

        The first character must be one of the unmodified base pitch names:
        C, D, E, F, G, A, B (not case-sensitive).

        Subsequent characters must indicate a single accidental type:
        one of '♭', 'b' or '-' for flat, and '♯', '#', and '+' for sharp,
        unless accidental_chars specified exactly the acceptable flat
        and sharp chars, e.g., "fs" indicates 'f' for flat, 's' for sharp.

        Note that 's' is not a default accidental type as it is ambiguous:
        'Fs' probably indicates F#, but Es is more likely Eb (German).

        Also unsupported are:
        mixtures of sharps and flats (e.g., B#b);
        symbols for double sharps, quarter sharps, naturals, etc.;
        any other characters (except space, tab and underscore,
        which are allowed but ignored).

        Following accidentals (if any) is an optional single-digit octave
        number. Note that MIDI goes below C0; if the octave number is
        omitted, the octave will be -1, which corresponds to pitch class
        numbers 0-11 and octave -1 (which you can also specify as octave).

        Instructive error messages are given for invalid input.
        """
        name = name.replace(" ", "").replace("\t", "").replace("_", "")
        if name == "":
            return 60, octave if octave else 0
        pitch_base = name[0].upper()  # error if non-string
        if pitch_base not in "ABCDEFG":
            raise ValueError("Invalid first character: must be one of ABCDEFG")
        pitch_class = LETTER_TO_NUMBER[pitch_base]

        name = name[1:]  # trim the note letter
        if len(name) > 0:
            if name[-1].isdigit():  # final character indicates octave
                octave = int(name[-1])  # overrides octave parameter
                name = name[:-1]  # remove octave from working
        if octave is None:  # no octave given in name or 2nd parameter
            octave = -1

        # parse the accidentals, if any
        if accidental_chars:
            flat_chars = [accidental_chars[0]]
            sharp_chars = [accidental_chars[1]]
        else:
            flat_chars = ["♭", "b", "-"]
            sharp_chars = ["♯", "#", "+"]
        if all(x in flat_chars for x in name):  # flats
            alteration = -len(name)
        elif all(x in sharp_chars for x in name):  # sharps
            alteration = len(name)
        else:
            raise ValueError("Invalid accidentals: must be only " +
                             f"{flat_chars} or {sharp_chars}.")

        # note that octave applies to pitch_class before alteration, so B#3=C4
        return pitch_class + 12 * (octave + 1) + alteration, alteration


    def get_name(self, accidental_chars: str = "b#") -> str:
        """Return string name including accidentals (# or b) but no
        octave. See the `name` property for details.

        Parameters
        ----------
        accidental_chars : str, optional
            The characters to use for flat and sharp accidentals.
            (Defaults to "b#")

        Returns
        -------
        str
            The string representation of the pitch name, including accidentals.
        """
        accidentals = "?"
        sharp_char = (accidental_chars[1] if len(accidental_chars) > 1 else "#")
        if round(self.alt) == self.alt:  # an integer value
            if self.alt > 0:
                accidentals = sharp_char * round(self.alt)
            elif self.alt < 0:
                accidentals = accidental_chars[0] * round(-self.alt)
            else:
                accidentals = ""  # natural
        return self.step + accidentals


    def get_name_with_octave(self, accidental_chars: str = "b#") -> str:
        """Return string name with octave, e.g., C4, B#3, etc.
        See the `name_with_octave` property for details.

        Parameters
        ----------
        accidental_chars : str, optional
            The characters to use for flat and sharp accidentals.
            (Defaults to "b#")

        Returns
        -------
        str
            The string representation of the pitch name with octave.
        """
        return self.name + str(self.octave)


    @property
    def step(self) -> str:
        """Retrieve the diatonic name of the pitch, e.g., A, B, C, D,
        E, F, G corresponding to letter names without accidentals.

        Returns
        -------
        str
            The name of the pitch, a letter in "A" through "G".
        """
        unaltered = round(self.key_num - self.alt)
        return ["C", "?", "D", "?", "E", "F", "?", "G", "?", "A", "?", "B"][
            unaltered % 12]


    @property
    def name(self) -> str:
        """Return string name including accidentals (# or b) if alt
        is integral.  Otherwise, return step name concatenated with
        "?". The octave number is omitted. See `get_name`, which
        accepts a parameter to specify accidental characters.
        """
        return self.get_name()


    @property
    def name_with_octave(self) -> str:
        """Return string name with octave, e.g., C4, B#3, etc.
        The octave number is calculated by
            `(key_num - alteration) / 12 + 1`  (with integer division)
        and refers to the pitch before alteration, e.g., C4 is
        enharmonic to B#3 and represents the same (more or less)
        pitch even though the octave numbers differ.

        See `get_name_with_octave`, which accepts a parameter to
        specify custom characters to represent accidentals.
        """
        return self.get_name_with_octave()


    @property
    def octave(self) -> int:
        """Returns the octave number based on `key_num - alt`, e.g.,
        C4 has octave 4 while B#3 has octave 3.
        """
        unaltered = round(self.key_num - self.alt)
        return (unaltered // 12) - 1


#    @octave.setter
#    def octave(self, oct: int) -> None:
#        """Set the octave number of the note.
#
#        Parameters
#        ----------
#        oct : int
#            The new octave number.
#        """
#        old_oct = self.octave
#        self.key_num += (oct - old_oct) * 12


    @property
    def pitch_class(self) -> int:
        """Retrieve the pitch class of the note, e.g., 0, 1, 2, ..., 11.
        The pitch class is the `key_num modulo 12`, which gives the
        class of this pitch in the range 0-11. If the `key_num` is
        non-integer, it is rounded.

        Returns
        -------
        int
            The pitch class of the note.
        """
        return round(self.key_num) % 12


# setters seem dangerous since Pitch is nominally immutable and
# often shared across multiple Note objects.
#
#    @pitch_class.setter
#    def pitch_class(self, pc: int) -> None:
#        """Set the pitch class of the note. The resulting
#        `register` will be the same. E.g., for B#3
#        (`key_num == 60`, `register == 4`), setting the
#        `pitch_class` to 2 will yield `key_num == 62`, 
#        `register == 4`, although the `octave` changes from
#        3 to 4. Setting the pitch class to 0 will result
#        in a pitch name of "C4".  The resulting `alt`
#        (accidental) values result in names of 
#        C, C#, D, Eb, E, F, F#, G, Ab, A, Bb, and B.
#
#        Parameters
#        ----------
#        pc : int
#            The new pitch class value.
#        """
#        self.key_num = (self.octave + 1) * 12 + pc % 12
#        self.alt = 0
#        self._fix_alteration()


    @property
    def register(self) -> int:
        """Returns the absolute octave number based on
        `floor(key_num)`, e.g., both C4 and B#3 have
        register 4.
        """
        return floor(self.key_num) // 12 - 1


#    @register.setter
#    def register(self, reg: int) -> None:
#        """Set the register of the note.
#
#        Parameters
#        ----------
#        reg : int
#            The new register
#        """
#        old_reg = self.register
#        self.key_num += (reg - old_reg) * 12

    def enharmonic(self) -> "Pitch":
        """If alt is non-zero, return a Pitch where alt is zero
        or has the opposite sign and where alt is minimized. E.g.
        enharmonic(Cbb) is A# (not Bb). If alt is zero, return a
        Pitch with alt of +1 or -1 if possible. Otherwise, return
        a Pitch with alt of -2 (Ebb, Abb or Bbb).
        Note the difference between this and `to_simplest_enharmonic`.

        Returns
        -------
        Pitch
            A new Pitch object representing the enharmonic equivalent.

        Examples
        --------
        >>> Pitch("C4").enharmonic()
        Pitch(name='B#3', key_num=60)

        >>> Pitch("B3").enharmonic()
        Pitch(name='Cb4', key_num=59)

        >>> Pitch("B#3").enharmonic()
        Pitch(name='C4', key_num=60)

        >>> bds = Pitch("B##3")
        >>> bds.enharmonic() # change of direction
        Pitch(name='Db4', key_num=61)

        >>> bds.upper_enharmonic()  # note the difference
        Pitch(name='C#4', key_num=61)

        >>> Pitch("Dbb4").enharmonic()
        Pitch(name='C4', key_num=60)
        """
        alt = self.alt
        unaltered = round(self.key_num - alt)
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
        return Pitch(self.key_num, alt=alt)


    def simplest_enharmonic(self,
            sharp_or_flat: Optional[str] = 'default') -> "Pitch":
        """
        Create a new Pitch object with the simplest enharmonic representation
        of the current pitch. I.e., if there exists an enharmonic-equivalent
        pitch with no-alterations, then use that. If an alteration is needed,
        then use sharps or flats depending on `sharp_or_flat`.

        Parameters
        ----------
        sharp_or_flat: str
            This is only relevant if the pitch needs an alteration, otherwise
            it is unused. The value can be "sharp" (use sharps), "flat" (use
            flats), and otherwise use the same enharmonic choice as the Pitch
            constructor.

        Examples
        --------

        >>> bds = Pitch("B##3")
        >>> bds.simplest_enharmonic()
        Pitch(name='C#4', key_num=61)

        >>> bds.simplest_enharmonic(sharp_or_flat="flat")
        Pitch(name='Db4', key_num=61)

        >>> Pitch("C4").simplest_enharmonic()
        Pitch(name='C4', key_num=60)

        Returns
        -------
        Pitch
            A Pitch object representing the enharmonic equivalent.
        """
        if self.alt in [None, 0]:
            return self

        if self.pitch_class in [0, 2, 4, 5, 7, 9, 11]:  # C, D, E, F, G, A, B
            return Pitch(self.key_num)
        elif sharp_or_flat == "sharp":  # unaltered in 1, 3, 6, 8, 10
            return Pitch(self.key_num, alt=1)
        elif sharp_or_flat == "flat":
            return Pitch(self.key_num, alt=-1)
        else:  # let Pitch figure out which enharmonic spelling (alt) to use:
            return Pitch(self.key_num)


    def upper_enharmonic(self) -> "Pitch":
        """
        Return a valid Pitch object based on the note name above the input
        and with `alt` accordingly decreased by 1 or 2,
        e.g., C#->Db, C##->D, Cb->Dbbb.

        Returns
        -------
        Pitch
            A Pitch object representing the upper enharmonic equivalent.


        Examples
        --------
        >>> bds = Pitch("B##3")
        >>> bds
        Pitch(name='B##3', key_num=61)

        >>> cis = bds.upper_enharmonic()
        >>> cis
        Pitch(name='C#4', key_num=61)

        >>> des = cis.upper_enharmonic()
        >>> des
        Pitch(name='Db4', key_num=61)

        >>> des.upper_enharmonic()
        Pitch(name='Ebbb4', key_num=61)

        >>> Pitch("D4").upper_enharmonic()
        Pitch(name='Ebb4', key_num=62)

        """
        alt = self.alt
        unaltered = round(self.key_num - alt) % 12
        if unaltered in [0, 2, 4, 7, 9]:  # C->D, D->E, F->G, G->A, A->B
            alt -= 2
        else:  # E->F, B->C
            alt -= 1
        return Pitch(self.key_num, alt=alt)

    def lower_enharmonic(self) -> "Pitch":
        """Return a valid Pitch with alt increased by 1 or 2, e.g., Db->C#,
        D->C##, D#->C###

        Returns
        -------
        Pitch
            A Pitch object representing the lower enharmonic equivalent.

        Examples
        --------
        >>> Pitch("Db4").lower_enharmonic()
        Pitch(name='C#4', key_num=61)

        >>> Pitch("D4").lower_enharmonic()
        Pitch(name='C##4', key_num=62)

        >>> Pitch("C#4").lower_enharmonic()
        Pitch(name='B##3', key_num=61)

        """
        alt = self.alt
        unaltered = round(self.key_num - alt) % 12
        if unaltered in [2, 4, 7, 9, 11]:  # D->C, E->D, G->F, A->G, B->A
            alt += 2
        else:  # F->E, C->B
            alt += 1
        return Pitch(self.key_num, alt=alt)


@dataclass
class PitchCollection:
    """
    Combined representations of more than one pitch. Differs from Chord
    which has onset, duration, and contains Notes, not Pitches.

    >>> test_case = ['G#4', 'G#4', 'B4', 'D4', 'F4', 'Ab4']
    >>> pitches = [Pitch(p) for p in test_case]
    >>> pitches_gathered = PitchCollection(pitches)

    >>> pitches_gathered.pitch_name_multiset
    ['G#4', 'G#4', 'B4', 'D4', 'F4', 'Ab4']

    >>> pitches_gathered.pitch_num_multiset
    [68, 68, 71, 62, 65, 68]

    >>> pitches_gathered.pitch_class_multiset
    [2, 5, 8, 8, 8, 11]

    >>> pitches_gathered.pitch_class_set
    [2, 5, 8, 11]

    >>> pitches_gathered.pitch_class_vector
    (0, 0, 1, 0, 0, 1, 0, 0, 3, 0, 0, 1)

    >>> pitches_gathered.pitch_class_indicator_vector
    (0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1)
    """

    pitches: list[Pitch]

    @property
    def pitch_num_multiset(self):
        return [p.key_num for p in self.pitches]

    @property
    def pitch_name_multiset(self):
        return [p.name_with_octave for p in self.pitches]

    @property
    def pitch_class_multiset(self):
        return sorted([p.pitch_class for p in self.pitches])

    @property
    def pitch_class_set(self):
        return sorted(list(set(self.pitch_class_multiset)))

    @property
    def pitch_class_vector(self):
        return multiset_to_vector(self.pitch_class_multiset, max_index=11)

    @property
    def pitch_class_indicator_vector(self):
        return weighted_to_indicator(self.pitch_class_vector)
