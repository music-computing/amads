"""
clef.py implements Clef class and some clef-related functions

<small>**Author**: Roger Dannenberg</small>
"""

__author__ = "Roger Dannenberg"

from typing import Optional, TextIO

from amads.core.basics import Event, EventGroup


class Clef(Event):
    """Clef is a zero-duration Event with clef information.

    All valid clefs are named. For any clef name, you can
    retrieve descriptive information using the `get_symbol`,
    `get_staff_line` and `get_octave` methods. These uniquely
    define the mapping between note name and staff position.

    Clef names are in `_clef_info.keys()` and based on Music21,
    which has these clefs (and a couple of others). For a more
    complete list (but how would we read them?), see
    https://github.com/Chorale-Corpus/Goudimel_C#clefs.

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
    parameters : Optionoal[tuple[str, int, int]]
        If `clef` is `"constructed"`, `parameters` must contain
        a tuple giving the clef symbol (`"F"`, `"G"`, or `"C"`),
        the staff line as the clef position (1 through 5), and
        the octave shift, e.g., 1 for "8va", -1 for "8vb", 0 for
        the normal octave (F3, G4, C4).

    Attributes
    ----------
    parent : Optional["EventGroup"]
        The containing object or None.
    _onset : float
        The onset (start) time.
    duration : float
        Always zero for this subclass.
    clef : str
        The clef name, one of "treble", "alto", "tenor", "bass",
        "treble8va", "treble8vb", "percussion". For uncommon
        clefs, see `_clef_info` in source code for a complete list.
    """

    __slots__ = ["clef"]
    clef: str

    _clef_info = {
        # common clefs:
        "treble": ("G", 2, 0),
        "alto": ("C", 3, 0),
        "tenor": ("C", 4, 0),
        "bass": ("F", 4, 0),
        "treble8va": ("G", 2, 1),
        "treble8vb": ("G", 2, -1),
        "percussion": ("P", None, None),
        # uncommon clefs:
        "bass8va": ("F", 4, 1),
        "bass8vb": ("F", 4, -1),
        "cbaritone": ("C", 5, 0),
        "fbaritone": ("F", 3, 0),
        "french_violin": ("G", 1, 0),
        "gsoprano": ("G", 3, 0),
        "mezzosoprano": ("C", 2, 0),
        "soprano": ("C", 1, 0),
        "subbass": ("F", 5, 0),
        # not even in music21 clef set:
        "treble15va": ("G", 2, 2),
        "bass15va": ("F", 4, 2),
        "bass15vb": ("F", 4, -2),
    }

    def __init__(
        self,
        parent: Optional["EventGroup"] = None,
        onset: float = 0.0,
        clef: str = "treble",
        parameters: Optional[tuple[str, int, int]] = None,
    ):
        super().__init__(parent, onset, 0)
        if clef not in self._clef_info and clef != "constructed":
            raise ValueError(f"Invalid clef: {clef}")
        self.clef = clef
        if clef == "constructed":
            if parameters is None:
                raise ValueError("Must provide parameters for constructed clef")
            self.set("clef_info", parameters)

    def __str__(self) -> str:
        """Short string representation"""
        param_str = ""
        if self.clef == "constructed":
            parameters = self.get("clef_info")
            if parameters is None:
                raise ValueError(
                    "Constructed clef missing clef_info parameters"
                )
            param_str = f"={parameters[0] + str(parameters[1])}"
            if parameters[2] != 0:
                param_str += f" {parameters[2]}"
        return f"Clef({self._event_onset()}, {self.clef}{param_str})"

    @classmethod
    def get_symbol(cls, clef_name: str) -> str:
        """retrieve the symbol used for the clef

        Values are "G" for G clef, "C" for C clef, "F" for F clef, and
        "P" for percussion clef. The G clef position is that of pitch G4,
        the C clef position is that of C4, and the F clef position is
        that of F3, subject to alteration by octave transposition.

        Parameters
        ----------
        clef_name: str
            The clef name.

        Returns
        -------
        str
            The clef symbol, one of "G", "C", "F", "P" (see above).

        Raises
        ------
        ValueError
            If the `clef_name` is not a known clef.
        """
        info = cls._clef_info.get(clef_name)
        if not info:
            raise ValueError(f"Unknown clef name {clef_name}")
        return info[0]

    @classmethod
    def get_staff_line(cls, clef_name: str) -> int:
        """retrieve the staff line where the clef is placed

        Staff lines are numbered 1 through 5, with 1 being the
        bottom line.

        Parameters
        ----------
        clef_name: str
            The clef name.

        Returns
        -------
        int
            The staff line (1 through 5) of the clef symbol.

        Raises
        ------
        ValueError
            If the `clef_name` is not a known clef.
        """
        info = cls._clef_info.get(clef_name)
        if not info:
            raise ValueError(f"Unknown clef name {clef_name}")
        return info[1]

    @classmethod
    def get_octave(cls, clef_name: str) -> int:
        """retrieve the octave transposition for the clef

        An octave transposition of 1 means the staff line with the clef
        symbol represents an octave higher than the nominal pitch of the
        clef symbol (one of G4, C4, F3). I.e., notes on the staff are
        transposed up one octave.

        Parameters
        ----------
        clef_name: str
            The clef name.

        Returns
        -------
        int
            The octave transposition applied to the clef symbol, in the
            range -2 to +2.

        Raises
        ------
        ValueError
            If the `clef_name` is not a known clef.
        """
        info = cls._clef_info.get(clef_name)
        if not info:
            raise ValueError(f"Unknown clef name {clef_name}")
        return info[2]

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


# hide the file organization from users and mkdocs:
Clef.__module__ = "amads.core.basics"
