"""
Euler Tonnetz.
See main module notes at `tonnetze/base.py`

<small>**Author**: Mark Gotham</small>

"""

from typing import List, Optional, Tuple, Union

from amads.core.basics import Chord
from amads.core.pitch import PitchCollection
from amads.harmony.root_finding.parncutt import ParncuttRootAnalysis
from amads.harmony.tonnetze._pitch_io import (
    load_pitch_multiset,
    pitch_class_set,
    transform_pitch_multiset,
)
from amads.harmony.tonnetze.base import Tonnetz

__author__ = "Mark Gotham"


class EulerTonnetz(Tonnetz):
    """
    The Euler tonnetz, as an instance of our generic `Tonnetz`.

    12 vertices, one per pitch class.
    24 triangular faces, one per major or minor triad.

    This is the classic triangulation of the torus by fifths and thirds,
    introduced by Euler and later associated with Riemann, Oettingen and others.

    The "neo-Riemannian" P, L and R transforms live here.

    Crossing a face's three edges reaches its P, L and R neighbours.
    Which edge corresponds to which transform depends on the face.
    See `EulerTriad` for the named transforms on actual chords.

    Examples
    --------
    >>> tonnetz = EulerTonnetz()
    >>> len(tonnetz.faces)
    24

    C major, {0, 4, 7}, and its three neighbouring triads.

    >>> neighbor_pcs = [tonnetz.face_pitch_classes(f) for f in tonnetz.neighbors((0, 4, 7)).values()]
    >>> sorted(tuple(sorted(pcs)) for pcs in neighbor_pcs)
    [(0, 3, 7), (0, 4, 9), (4, 7, 11)]

    """

    def __init__(self):
        faces = []
        for root in range(12):
            faces.append((root, (root + 4) % 12, (root + 7) % 12))
            faces.append((root, (root + 3) % 12, (root + 7) % 12))
        super().__init__(faces)


_EULER_TONNETZ = EulerTonnetz()
"""
Module-level singleton, shared by every `EulerTriad`.
The face/edge structure is fixed and stateless, so there is no reason
for each triad to rebuild its own 24 faces.
"""


class EulerTriad:
    """
    A major or minor triad, located on the `EulerTonnetz`,
    together with the neo-Riemannian P, L and R transforms.

    Parameters
    ----------
    chord : Union[List[int], Chord, PitchCollection]
        The chord to analyze.
        Can be a list of MIDI pitches,
        a `Chord` object,
        or a `PitchCollection` object.

    Attributes
    ----------
    pitch_multiset : Tuple[int, ...]
        The chord's pitches as MIDI key numbers.
        Can include octave-specific entries, such as 60,
        and duplicate entries, such as 60 and 60 together.
    pc_set : FrozenSet[int]
        The chord's pitch class set.
    root : int
        The pitch class of the chord's root,
        as estimated by Parncutt's root-finding algorithm.
    major_not_minor : bool
        True for a major chord, False for a minor chord.
    l_transform : Optional[Tuple[int, ...]]
        The L-transform of `pitch_multiset`, once computed.
        Octave and duplicate pitches are preserved.
    p_transform : Optional[Tuple[int, ...]]
        The P-transform, see `l_transform`.
    r_transform : Optional[Tuple[int, ...]]
        The R-transform, see `l_transform`.

    Examples
    --------
    >>> d_major = [2, 62, 6, 9]
    >>> triad = EulerTriad(d_major)
    >>> triad.root
    2

    >>> triad.leading_tone_exchange()
    >>> triad.l_transform
    (1, 61, 6, 9)

    >>> triad.parallel()
    >>> triad.p_transform
    (2, 62, 5, 9)

    >>> triad.relative()
    >>> triad.r_transform
    (2, 62, 6, 11)

    Transforms are involutions, so applying the same transform twice
    (or any even number of times)
    returns the original chord.

    >>> roundtrip = EulerTriad(list(triad.r_transform))
    >>> roundtrip.relative()
    >>> roundtrip.r_transform == tuple(d_major)
    True

    `Chord` and `PitchCollection` inputs work identically.

    >>> from amads.core.basics import Chord, Note
    >>> chord = Chord(Note(pitch=60), Note(pitch=64), Note(pitch=67))
    >>> EulerTriad(chord).root
    0

    """

    def __init__(
        self,
        chord: Union[List[int], Chord, PitchCollection],
    ):
        self.pitch_multiset = load_pitch_multiset(chord)
        self.pc_set = pitch_class_set(self.pitch_multiset)
        self.major_not_minor, self.root = self._quality_and_root()

        self.l_transform: Optional[Tuple[int, ...]] = None
        self.p_transform: Optional[Tuple[int, ...]] = None
        self.r_transform: Optional[Tuple[int, ...]] = None

    def _quality_and_root(self) -> Tuple[bool, int]:
        """
        Finds the chord's root.
        and checks that the chord is a major or minor triad.

        Internally this uses Parncutt's algorithm,
        which is probably overkill for this task and may be refactored.
        """
        if len(self.pc_set) != 3:
            raise ValueError("Not a major or minor triad.")

        analysis = ParncuttRootAnalysis(list(self.pc_set))
        root = analysis.root

        reference = sorted((pc - root) % 12 for pc in self.pc_set)
        if reference == [0, 4, 7]:
            return True, root
        if reference == [0, 3, 7]:
            return False, root
        raise ValueError("Not a major or minor triad.")

    def _face(self) -> Tuple[int, int, int]:
        """
        Returns this triad's face on `_EULER_TONNETZ`:
        the (root, third, fifth) pitch classes, in the exact tuple form
        `EulerTonnetz` builds its faces in, so it can be looked up
        directly rather than searched for.
        """
        third_interval = 4 if self.major_not_minor else 3
        return (
            self.root,
            (self.root + third_interval) % 12,
            (self.root + 7) % 12,
        )

    def _cross_edge(self, pitch_class_to_change: int) -> Tuple[int, ...]:
        """
        Finds the neighbouring triad reached by moving away from
        `pitch_class_to_change`, via `EulerTonnetz.transform`,
        and applies the resulting semitone shift to `pitch_multiset`.

        The edge crossed is the one *not* touching `pitch_class_to_change`,
        i.e. the edge joining the other two (shared, unchanged) pitch classes of the face.
        The transposition applied is not hardcoded:
        it is read off as the difference between the old and new pitch class,
        i.e., whatever `EulerTonnetz`'s face structure says it is.
        The difference is canonicalized to the smaller-magnitude
        representative mod 12 (e.g. a shift of 11 is treated as -1),
        matching the small up/down semitone moves P, L and R make.
        """
        face = self._face()
        edge = frozenset(face) - {pitch_class_to_change}
        try:
            new_face = _EULER_TONNETZ.transform(face, edge)
        except ValueError as error:
            # Should be unreachable
            # EulerTonnetz's 24 faces are fixed and always meet in well-formed pairs.
            raise ValueError(
                f"Could not find a neighbouring triad for face {face} across edge {set(edge)}."
                "This points to a bug in `EulerTriad`'s face construction,"
                f"not to the input chord {self.pitch_multiset}."
            ) from error
        (new_pitch_class,) = frozenset(new_face) - edge
        transposition = (new_pitch_class - pitch_class_to_change) % 12
        if transposition > 6:
            transposition -= 12
        return transform_pitch_multiset(
            self.pitch_multiset, pitch_class_to_change, transposition
        )

    def leading_tone_exchange(self) -> None:
        """
        The L-transform (leading-tone exchange).
        Moves a major chord's root down a semitone, e.g. F major to A minor.
        Moves a minor chord's fifth up a semitone, e.g. A minor to F major.
        Sets the `l_transform` attribute.
        """
        if self.major_not_minor:
            pitch_class_to_change = self.root
        else:
            pitch_class_to_change = (self.root + 7) % 12
        self.l_transform = self._cross_edge(pitch_class_to_change)

    def parallel(self) -> None:
        """
        The P-transform (parallel).
        Moves between major and minor chords on the same root,
        e.g. F major to f minor and vice versa.
        Note this is not how German music theory uses the term "parallel".
        Sets the `p_transform` attribute.
        """
        if self.major_not_minor:
            pitch_class_to_change = (self.root + 4) % 12
        else:
            pitch_class_to_change = (self.root + 3) % 12
        self.p_transform = self._cross_edge(pitch_class_to_change)

    def relative(self) -> None:
        """
        The R-transform (relative).
        Moves between major and minor chords sharing a key signature,
        e.g. F major to d minor and vice versa.
        Sets the `r_transform` attribute.
        """
        if self.major_not_minor:
            pitch_class_to_change = (self.root + 7) % 12
        else:
            pitch_class_to_change = self.root
        self.r_transform = self._cross_edge(pitch_class_to_change)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
