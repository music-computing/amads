# pitch.py -- the Pitch class
# fmt: off
# flake8: noqa E129,E303


import functools
from dataclasses import dataclass
from math import floor
from typing import Optional, Tuple, Union

from amads.utils import set_to_vector, weighted_to_indicator

LETTER_TO_NUMBER = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


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
        pitch : Union[float, str, None], optional
            MIDI keynum or string Pitch name. Syntax is A-G followed by
            accidentals followed by octave number.
            (Defaults to 60)
        alt: Union[float, None], optional
            If pitch is a number, alt is an optional alteration (Defaults to 0);
            if pitch is a string, alt is the optional octave (an integer)
            (Overridden by any octave specification in pitch,
            otherwise defaults to -1, which yields pitch class keynums 0-11).
        accidental_chars: Union[str, None], optional
            Allows parsing of pitch names with customized accidental characters.
            (Defaults to None, which admits '♭', 'b' or '-' for flat, and 
            '♯', '#', and '+' for sharp, but does not accept 'f' and 's'.

    Attributes
    ----------
        keynum : float
            MIDI key number, e.g. C4 = 60, generalized to float.
        alt : float
            Alteration, e.g. flat = -1.
   
    Properties
    ----------
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
    __slots__ = ["keynum", "alt"]

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


    def __init__(self, pitch: Union[float, str, None] = 60,
                 alt: Union[float, None] = None,
                 accidental_chars: Optional[str] = None):
        if isinstance(pitch, (int, float)):
            self.keynum = pitch
            self.alt = 0 if alt is None else alt
            self._fix_alteration()
        elif isinstance(pitch, str):
            self.keynum, self.alt = Pitch.from_name(pitch, alt, accidental_chars)
        elif isinstance(pitch, Pitch):
            self.keynum = pitch.keynum
            self.alt = pitch.alt
        else:
            raise ValueError(f"invalid pitch specification: {pitch}")
            

    def __repr__(self):
        return f"Pitch(name='{self.name}', keynum={self.keynum})"


    def as_tuple(self):
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


    @classmethod
    def from_name(cls, name: str, 
                  octave: Optional[float],
                  accidental_chars: Optional[str] = None
                 ) -> Tuple[float, float]:
        """
        Converts a string like 'Bb' to the corresponding pitch (10)
        and alteration, e.g. 'Bb' returns (10, -1).
        If the string has an octave number or octave is given, the
        octave will be applied, e.g. "C4" yields (60, 0). octave takes
        effect if it is a number and name does not include an octave.
        If both name has no octave and octave is None, the octave is
        -1, yeilding pitch class numbers 0-11.

        First character must be one of the unmodified base pitch names:
        C, D, E, F, G, A, B (not case-sensitive).

        Subsequent characters must indicate a single accidental type:
        one of '♭', 'b' or '-' for flat, and '♯', '#', and '+' for sharp,
        unless accidental_chars specified exactly the acceptable flat
        and sharp chars, e.g. "fs" indicates 'f' for flat, 's' for sharp.

        Note that 's' is not a default accidental type as it is ambiguous:
        'Fs' probably indicates F#, but Es is more likely Eb (German).

        Also unsupported are:
        mixtures of sharps and flats (e.g. B#b);
        symbols for double sharps, quarter sharps, naturals, etc.;
        any other characters (except space, tab and underscore,
        which are allowed but ignored).

        Following accidentals (if any) is an optional single-digit octave
        number. Note that MIDI goes below C0; if the octave number is
        omitted, the octave will be -1, which corresponds to pitch class
        numbers 0 - 11 and octave -1 (which you can also specify as octave).

        Instructive error messages are given for invalid input.
        """
        name = name.replace(" ", "").replace("\t", "").replace("_", "")
        if name == "":
            return (60, octave if octave else 0)
        pitch_base = name[0].upper();  # error if non-string
        if pitch_base not in "ABCDEFG":
            raise ValueError("Invalid first character: must be one of ABCDEFG")
        pitch_class = LETTER_TO_NUMBER[pitch_base]

        name = name[1:]  # trim the note letter
        if name[-1].isdigit():  # final character indicates octave
            octave = int(name[-1])  # overrides octave parameter

        # parse the accidentals, if any
        alteration = 0
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

        if octave == None:  # no octave given in name or 2nd parameter
            octave = -1

        return (pitch_class + alteration + 12 * (octave + 1), alteration)


    @property
    def step(self) -> str:
        """Retrieve the name of the pitch, e.g. A, B, C, D, E, F, G
        corresponding to letter names without accidentals.

        Returns
        -------
        int
            The name of the pitch, e.g. 0, 2, 4, 5, 7, 9, 11.
        """
        unaltered = round(self.keynum - self.alt)
        return ["C", "?", "D", "?", "E", "F", "?", "G", "?", "A", "?", "B"][
                unaltered % 12]


    @property
    def name(self, accidental_chars: str = "b#") -> str:
        """Return string name including accidentals (# or b) if alt is integral.
        Otherwise, return step name concatenated with "?".
        
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
                accidentals = sharp_char * self.alt
            elif self.alt < 0:
                accidentals = accidental_chars[0] * -self.alt
            else:
                accidentals = ""  # natural
        return self.step + accidentals


    @property
    def name_with_octave(self) -> str:
        """Return string name with octave, e.g. C4, B#3, etc.
        The octave number is calculated by subtracting 1 from the
        integer division of keynum by 12. The octave number is
        independent of enharmonics. E.g. C4 is enharmonic to B#3 and
        represent the same (more or less) pitch, but BOTH have an
        octave of 4. On the other hand name() will return "C4"
        and "B#3", respectively.

        Returns
        -------
        str
            The string representation of the pitch name with octave.
        """
        unaltered = round(self.keynum - self.alt)
        octave = (unaltered // 12) - 1
        return self.name + str(octave)


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
        octave of 4. On the other hand name() will return "C4" and "B#3",
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


@dataclass
class PitchCollection:
    """
    Combined representations of more than one pitch. Differs from Chord
    which has onset, duration, and contains Notes, not Pitches.

    >>> test_case = ["G#", "G#", "B", "D", "F", "Ab"]
    >>> pitches = [Pitch(p) for p in test_case]
    >>> pitches_gathered = PitchCollection(pitches)

    >>> pitches_gathered.pitch_multi_set
    ['G#', 'G#', 'B', 'D', 'F', 'Ab']

    >>> pitches_gathered.MIDI_multi_set
    [68, 68, 71, 62, 65, 68]

    >>> pitches_gathered.pitch_class_multi_set
    [2, 5, 8, 8, 8, 11]

    >>> pitches_gathered.pitch_class_set
    [2, 5, 8, 11]

    >>> pitches_gathered.pitch_class_vector
    (0, 0, 1, 0, 0, 1, 0, 0, 3, 0, 0, 1, 0)

    >>> pitches_gathered.pitch_class_indicator_vector
    (0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0)
    """

    pitches: list[Pitch]


    @property
    def pitch_multi_set(self):
        return [p.name for p in self.pitches]


    @property
    def pc_multi_set(self):
        return sorted([p.pitch_class for p in self.pitches])


    @property
    def pc_set(self):
        return sorted(set(self.pc_multi_set))


    @property
    def pitch_class_vector(self):
        return set_to_vector(self.pc_multi_set, max_index=11)


    @property
    def pitch_class_indicator_vector(self):
        return weighted_to_indicator(self.pitch_class_vector)
