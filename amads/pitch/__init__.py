"""
The 'pitch' module contains functions and classes related to pitch.
"""

from __future__ import annotations

from amads.core.vectors_sets import multiset_to_vector, weighted_to_indicator

from .transformations import *


class Pitch:
    """
    Combined representations of a single pitch,
    serving to organize various conversion routines among the representation of pitch.

    To be clear: we're not talking about a note in a score, but only the pitch,
    there's no duration or position in this class.
    """

    def __init__(
        self,
        midi: int | None,
        name: str | None,
        octave: int | None,
    ):
        """
        Initializes a `Pitch` object.

        Parameters
        ----------
        midi (int | None): The MIDI number of the pitch.
        name (str | None): The pitch name in the form
            <Base name><Sharps_flats><Octave>
            (e.g., "C4", "A#", "Bbb3").
            The octave may or may not be specified and any number of sharps/flats is permitted.
            If the octave is not specified, the MIDI number will be assiged in octave 4,
            but the octave attribute will be None.

        Examples
        --------
        >>> Pitch.from_midi(60)
        Pitch(name='C4', midi=60)

        >>> c4 = Pitch.from_name("C4")
        >>> c4
        Pitch(name='C4', midi=60)

        >>> c4.octave
        4

        >>> c = Pitch.from_name("C")
        >>> c.midi
        60

        >>> c.octave is None
        True

        >>> Pitch.from_name("C###")
        Pitch(name='C###', midi=63)

        >>> Pitch.from_name("Cbbb")
        Pitch(name='Cbbb', midi=69)

        """
        self.midi = midi
        self.name = name
        self.octave = octave

    def __repr__(self):
        return f"Pitch(name='{self.name}', midi={self.midi})"

    @classmethod
    def from_midi(cls, midi: int | None):
        """
        Creates a Pitch object from a MIDI number where provided.
        """
        if midi is None:
            return
        if not isinstance(midi, int):
            raise TypeError("MIDI number must be an integer.")
        if not 0 <= midi <= 127:
            raise ValueError("MIDI number must be between 0 and 127.")
        name, octave = cls._midi_to_name_octave(midi)
        return cls(midi, name, octave)

    @staticmethod
    def _midi_to_name_octave(midi):
        """
        Converts a MIDI number to a pitch name
        Always default to no sharps/flat or single sharps.
        """
        base_names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
        base_name = base_names[midi % 12]
        octave = midi // 12 - 1
        return f"{base_name}{octave}", octave

    @classmethod
    def from_name(cls, name: str | None):
        """
        Converts a string like 'Bb' to the corresponding pc integer (10).

        The first character must be one of the unmodified base pitch names: C, D, E, F, G, A, B
        (not case-sensitive).

        Any subsequent characters must indicate a single accidental type: one of
        '♭', 'b' or '-' for flat;
        '♯', '#', and '+' for sharp.

        Note that 's' is not a supported accidental type as it is ambiguous:
        'Fs' probably indicates F#, but Es is more likely Eb (German).

        The following are also unsupported:
        mixtures of sharps and flats (e.g., B#b);
        special symbols (e.g., for double sharps);
        any other symbols (including white space).

        Subsequent characters either:
        indicate octave (added as an attribute to the Pitch object, ignored in the pitch_class)
        or are unknown and raise a value error.

        No regex to provide instructive error messages.
        """
        pitch_base = name[
            0
        ].upper()  # catches len=0 by index error and non-string type check
        name.replace(" ", "")
        pitch_base_dict = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        pitch_class = pitch_base_dict[name[0]]
        if pitch_base not in pitch_base_dict.keys():
            raise ValueError(
                f"Invalid first character: must be one of {pitch_base_dict.keys()}."
            )

        if len(name) == 1:  # no accidental or octave, done.
            midi = (
                60 + pitch_class
            )  # Create a MIDI number in octave 4, but leave the octave attr as None.
            return cls(midi=midi, name=name, octave=None)

        # len > 1
        if name[-1].isdigit():  # final character indicating octave
            octave = int(name[-1])
            if len(name) == 2:  # e.g., C4, done.
                return cls(
                    midi=12 * (octave + 1) + pitch_class, name=name, octave=octave
                )
            remaining_string = name[1:-1]  # len > 2 e.g., C##4
        else:
            remaining_string = name[1:]  # e.g., C##
            octave = None

        if all(x in ["♭", "b", "-"] for x in remaining_string):  # flats
            modifier = -len(remaining_string)
            alteration = "b" * len(remaining_string)  # standardise
        elif all(x in ["♯", "#", "+"] for x in remaining_string):  # sharps
            modifier = len(remaining_string)
            alteration = "#" * len(remaining_string)  # standardise
        else:
            raise ValueError(
                "Invalid central characters: must be only sharps or flats."
            )

        pitch_class += modifier
        pitch_class %= 12
        name = pitch_base + alteration

        if octave is None:
            midi = (
                60 + pitch_class
            )  # Create a MIDI number in octave 4, but leave the octave attr as None.
        else:
            name += str(octave)
            midi = 12 * (octave + 1) + pitch_base_dict[name]

        return cls(midi=midi, name=name, octave=octave)


class PitchCollection:
    """
    Combined representations of more than one pitch.

    >>> test_case = ["G#", "G#", "B", "D", "F", "Ab"]
    >>> pitches = [Pitch.from_name(p) for p in test_case]
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

    def __init__(self, pitches: list[Pitch]):
        self.pitch_multi_set = [p.name for p in pitches]
        self.MIDI_multi_set = [p.midi for p in pitches]
        self.pitch_class_multi_set = [
            midi % 12 for midi in self.MIDI_multi_set
        ]  # TODO or make pc attr on Pitch.
        self.pitch_class_multi_set.sort()
        self.pitch_class_set = list(set(self.pitch_class_multi_set))
        self.pitch_class_set.sort()
        self.pitch_class_vector = multiset_to_vector(
            self.pitch_class_multi_set, max_index=12
        )
        self.pitch_class_indicator_vector = weighted_to_indicator(
            self.pitch_class_vector
        )

    # def retrieve_derivatives(self):
    #     from pc_set_functions import pitches_to_prime
    #     # TODO consider this kind of method for deriving secondary representations like prime form.


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
