"""
Pitch Processing for Tonnetze.
See module notes at `tonnetze/base.py`

<small>**Author**: Mark Gotham</small>

"""

from typing import FrozenSet, List, Tuple, Union

from amads.core.basics import Chord, Note
from amads.core.pitch import PitchCollection

__author__ = "Mark Gotham"


def load_pitch_multiset(
    chord: Union[List[int], Chord, PitchCollection],
) -> Tuple[int, ...]:
    """
    Converts a chord-like input into a multiset of MIDI key numbers.
    Octave and duplicate pitches are preserved.

    This is the shared entry point used by every tonnetz transform class,
    accepting the same input types as `ParncuttRootAnalysis`.

    Parameters
    ----------
    chord : Union[List[int], Chord, PitchCollection]
        The chord to convert.
        Can be a list of MIDI pitches,
        a `Chord` object,
        or a `PitchCollection` object.

    Returns
    -------
    Tuple[int, ...]
        The chord's pitches as MIDI key numbers,
        in the same order as the input,
        including octave placement and duplicates.

    Raises
    ------
    TypeError
        If `chord` is not a list, a `Chord`, or a `PitchCollection`.
    ValueError
        If `chord` contains no pitches,
        or contains a negative pitch number.

    Examples
    --------
    >>> load_pitch_multiset([60, 64, 67])
    (60, 64, 67)

    >>> from amads.core.basics import Chord, Note
    >>> chord = Chord(Note(pitch=60), Note(pitch=64), Note(pitch=67))
    >>> load_pitch_multiset(chord)
    (60, 64, 67)

    >>> from amads.core.pitch import Pitch, PitchCollection
    >>> pitches = PitchCollection([Pitch(x) for x in ["D4", "F4", "A4"]])
    >>> load_pitch_multiset(pitches)
    (62, 65, 69)
    """
    if isinstance(chord, list):
        pitch_multiset = tuple(chord)
    elif isinstance(chord, Chord):
        pitch_multiset = tuple(
            note.pitch.midi_num for note in chord.find_all(Note)
        )
    elif isinstance(chord, PitchCollection):
        pitch_multiset = tuple(chord.pitch_num_multiset)
    else:
        raise TypeError(
            "chord must be a list of MIDI pitches, a Chord, or a PitchCollection, "
            f"not {type(chord).__name__}."
        )
    if len(pitch_multiset) == 0:
        raise ValueError("chord must contain at least one pitch.")
    if any(p < 0 for p in pitch_multiset):
        raise ValueError("chord must not contain negative pitch numbers.")
    return pitch_multiset


def pitch_class_set(pitch_multiset: Tuple[int, ...]) -> FrozenSet[int]:
    """
    Returns the distinct pitch classes present in a pitch multiset.

    Examples
    --------
    >>> pitch_class_set((60, 64, 67, 72))
    frozenset({0, 4, 7})

    Note: not prime form (e.g., no transposiiton or re-ordering).
    >>> pitch_class_set((61, 64, 68))
    frozenset({8, 1, 4})

    """
    return frozenset(p % 12 for p in pitch_multiset)


def transform_pitch_multiset(
    pitch_multiset: Tuple[int, ...],
    pitch_class_to_change: int,
    transposition: int,
) -> Tuple[int, ...]:
    """
    Shifts every occurrence of one pitch class within a pitch multiset.
    Every pitch equal to `pitch_class_to_change`, modulo 12, is shifted,
    all other pitches are left unchanged,
    octave placement and duplicates are preserved throughout.

    IMPORTANT NOTE:
    Numbers 0-11 are treated as bare pitch classes rather than key numbers,
    and are wrapped modulo 12 rather than shifted below 0.
    This matters iff `pitch_multiset` mixes bare pitch classes
    with full key numbers, which is a bit odd, but not enforced against.
    In that narrow case, a bare pitch class of, say, 11 shifted by +2
    wraps to 1, rather than becoming the key number 13.
    The alternative, treating 0-11 as key numbers too,
    would risk returning negative key numbers,
    ... which is clearly worse.

    Parameters
    ----------
    pitch_multiset : Tuple[int, ...]
        The pitches to transform,
        as returned by `load_pitch_multiset`.
    pitch_class_to_change : int
        The pitch class, 0-11, whose occurrences should be shifted.
    transposition : int
        The number of semitones to shift each matching pitch by.
        May be negative.

    Returns
    -------
    Tuple[int, ...]
        The transformed pitches,
        in the same order as `pitch_multiset`.

    Examples
    --------
    Shift the root of a C major triad down a semitone, an L-transform move.

    >>> transform_pitch_multiset((60, 64, 67), 0, -1)
    (59, 64, 67)

    A bare pitch class wraps rather than going negative.

    >>> transform_pitch_multiset((0, 4, 7), 0, -1)
    (11, 4, 7)
    """
    new_pitches = []
    for pitch in pitch_multiset:
        if pitch % 12 != pitch_class_to_change:
            new_pitches.append(pitch)
        elif pitch in range(12):
            new_pitches.append((pitch + transposition) % 12)
        else:
            new_pitches.append(pitch + transposition)
    return tuple(new_pitches)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
