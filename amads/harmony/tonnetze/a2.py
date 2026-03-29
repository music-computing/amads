from typing import List, Union

from amads.core.basics import Chord, Note
from amads.pitch import PitchCollection

from ..root_finding.parncutt import ParncuttRootAnalysis

__author__ = "Mark Gotham"


class A2VertexTonnetz:
    """
    This class encodes the so-called "neo-Riemannian" transforms between
    triads made of triangles between neighboring verices on the "Euler" (A2 triangulation) Tonnetz,
    where each vertex represents a pitch-class.

    Parameters
    ----------
    chord : Union[List[int], Chord, PitchCollection]
        The chord to analyze. Can be represented as:
        - A list of MIDI pitches representing a chord,
        - A Chord object,
        - A PitchCollection object.

    Attributes
    ----------
    pitch_multi_set : tuple
        The chord's pitches as MIDI numbers.
        This can include octave-specific entries (60) and duplicate entries (60, 60).
    pc_set : set
        The chord's pitch class set.
    root : int
        The pitch class of the derived chord root as estimated by Parncutt's algorithm.
    major_not_minor : bool
        Major chord if True, minor if False, error otherwise.
    l_transform : set
        The L-transform mapping of the original set `pitch_multi_set`, including duplicates.
    p_transform : set
        The P-transform (see notes at `l_transform`).
    r_transform : set
        The R-transform (see notes at `l_transform`).


    Examples
    --------
    >>> d_major = [2, 62, 6, 9]
    >>> euler = A2VertexTonnetz(d_major)
    >>> euler.root
    2

    >>> euler.leading_tone_exchange()
    >>> euler.l_transform
    (1, 61, 6, 9)

    >>> euler.parallel()
    >>> euler.p_transform
    (2, 62, 5, 9)

    >>> euler.relative()
    >>> euler.r_transform
    (2, 62, 6, 11)

    >>> roundtrip = A2VertexTonnetz(list(euler.r_transform))
    >>> roundtrip.relative()
    >>> roundtrip.r_transform == tuple(d_major)
    True


    References
    ----------
    [1] Euler, Leonhard (1739). Tentamen novae theoriae musicae ex certissismis harmoniae principiis
    dilucide expositae. Saint Petersburg Academy.
    """

    def __init__(
        self,
        chord: Union[List[int], Chord, PitchCollection],
    ):
        self.pitch_multi_set, self.pc_set = self.load_chord(chord)
        self.major_not_minor, self.root = self.get_quality_and_root()

        self.l_transform = None
        self.p_transform = None
        self.r_transform = None

    @staticmethod
    def load_chord(
        chord: Union[List[int], Chord, PitchCollection]
    ) -> tuple[tuple[int], set[int]]:
        """
        Creates initial chord information from supported sources:
        a list of MIDI pitches,
        a `Chord` object, or
        a `PitchCollection` object.
        """
        if isinstance(chord, List):
            pitch_multi_set = tuple(chord)
        elif isinstance(chord, Chord):
            pitch_multi_set = tuple(
                [note.pitch.keynum for note in chord.find_all(Note)]
            )
        elif isinstance(chord, PitchCollection):
            pitch_multi_set = chord.pitch_class_multi_set
        else:
            raise TypeError(
                "Chord must be a list of MIDI pitches, a `Chord` object, or a `PitchCollection` object."
            )

        if len(pitch_multi_set) == 0:
            raise ValueError("Chord must contain at least one pitch.")
        if any(x < 0 for x in pitch_multi_set):
            raise ValueError("Chord must not contain negative integers.")

        pc_set = set(pitch % 12 for pitch in list(pitch_multi_set))
        return pitch_multi_set, pc_set

    def get_quality_and_root(self):
        """
        Get the prime form of the pitch collection,
        verify that it is major or minor (if not raise an error),
        and calculate the root using the Parncutt algorithm.
        """
        if len(self.pc_set) != 3:
            raise ValueError("Not a major or minor triad.")

        analysis = ParncuttRootAnalysis(
            list(self.pc_set)
        )  # TODO have Parncutt accept any Iterable
        root = analysis.root

        reference = sorted(set(((x - root) % 12 for x in self.pc_set)))
        if reference == [0, 4, 7]:
            major_not_minor = True
        elif reference == [0, 3, 7]:
            major_not_minor = False
        else:
            raise ValueError("Not a major or minor triad.")
        return major_not_minor, root

    def leading_tone_exchange(self):
        """
        The "Leading-Tone exchange" maps
        a major chord by moving its root down a semi-tone (e.g., F major to a minor)
        or (equivalently) a minor triad by moving its 5th up a semi-tone (e.g., a minor to F major).
        This function takes a `Chord` object
        (raises an error if that chord is not a major/minor triad)
        and returns a new `Chord` that is the L-transform version.
        This can include duplicate pitches as shown in the examples.
        This method creates an `l_transform` attribute on the class: a tuple of `key_nums` only:
        pitch spelling is ambiguous in this case and rarely useful for our purposes.
        """
        if self.major_not_minor:
            pitch_class_to_change = self.root
            transposition = -1
        else:  # minor
            pitch_class_to_change = (self.root + 7) % 12  # fifth
            transposition = 1

        self.l_transform = self.transform(pitch_class_to_change, transposition)

    def parallel(self):
        """
        The "Parallel" (in English) maps between
        major and minor chords on the same root (e.g., F major to f minor or vice versa).
        Note that this is not how German music theory uses the term parallel.
        """
        if self.major_not_minor:
            pitch_class_to_change = (self.root + 4) % 12
            transposition = -1
        else:  # minor
            pitch_class_to_change = (self.root + 3) % 12  # fifth
            transposition = 1

        self.p_transform = self.transform(pitch_class_to_change, transposition)

    def relative(self):
        """
        The "Relative" (in English) maps between the
        major and minor chords whose keys share a key signature,
        (e.g., F major to d minor and vice versa).
        """
        if self.major_not_minor:
            pitch_class_to_change = (self.root + 7) % 12  # fifth
            transposition = 2
        else:  # minor
            pitch_class_to_change = self.root
            transposition = -2

        self.r_transform = self.transform(pitch_class_to_change, transposition)

    def transform(self, pitch_class_to_change: int, transposition: int) -> tuple:
        """
        Shared method for all single pitch class transforms.
        Run multiple times for 2+ pitch class transforms.

        Transforms move constituent pitches of the multiset in place, preserving octave.
        The exception is for numbers in the range 0–11.
        These numbers are taken to be pitch classes rather than true key numbers.
        This prevents the return of negative numbers (e.g., 0-2 = 10).
        We considered the counterargument that one might have, say, a key number of 11 to be treated as such.
        In that case, 11+2=13 rather than 1.
        That is both an extremely narrow use case, and the consequences are very small:
        you still end up with right pitch class, but at an even lower octave than intended.
        The upsides of this design outweigh that small detraction:
        the system handles any pitch and never returns a negative,
        and it is flexible wrt pitch class versus key num.
        """
        new_key_nums = []
        for kn in self.pitch_multi_set:
            if kn % 12 == pitch_class_to_change:  # transform
                if kn in range(12):
                    new_key_nums.append((kn + transposition) % 12)  # See docs.
                else:
                    new_key_nums.append(kn + transposition)  # See docs.
            else:  # don't transform
                new_key_nums.append(kn)

        return tuple(new_key_nums)


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
