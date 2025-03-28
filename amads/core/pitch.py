# pitch.py -- the Pitch class
# fmt: off
# flake8: noqa E129,E303


import functools


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
    def name(self, flat_char: str = "b") -> str:
        """Return string name including accidentals (# or b) if alt is integral.
        Otherwise, return step name concatenated with "?".
        
        Parameters
        ----------
        flat_char : str, optional
            The character to use for flat accidentals. (Defaults to "b")

        Returns
        -------
        str
            The string representation of the pitch name, including accidentals.
        """
        accidentals = "?"
        if round(self.alt) == self.alt:  # an integer value
            if self.alt > 0:
                accidentals = "#" * self.alt
            elif self.alt < 0:
                accidentals = flat_char * -self.alt
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
