# -*- coding: utf-8 -*-
"""
freie_leittoneinstellung.py

Find possible cases of the 'freie Leittoneinstellung'.

Updated and integrated into AMADS from a previous version in YCACL.

<small>**Author**: Mark Gotham.</small>
"""

from dataclasses import dataclass
from typing import Iterable, Optional, Union

from amads.core.chord import Chord
from amads.core.pitch import Pitch, PitchCollection

__author__ = "Mark Gotham"


# `amads.core.chord.QUALITIES` covers everything from power chords to ninths.
# Here we only test `slice_1`/`slice_2` against "plain" tertian sonorities.
# Currently, we take that subset directly.
# TODO we may review this design and the details of which are in the subset.
TRIAD_QUALITIES = frozenset({"major", "minor", "diminished", "augmented"})
SEVENTH_QUALITIES = frozenset(
    {"dominant7", "major7", "minor7", "diminished7", "half-dim7"}
)


PitchesLike = Union[PitchCollection, Iterable[Union[Pitch, int, float, str]]]


def _to_pitch_collection(pitches: PitchesLike) -> PitchCollection:
    """Coerce `pitches` into a `PitchCollection`.

    A single point through which every supported input shape is adapted.
    Given this, the rest of the module only has to work with one type.

    Accepts a few types with an order of preference as follows:

    1. a `PitchCollection` (returned as-is, no copy);
    2. an iterable of `Pitch` objects
    (e.g., `slice.content` mapped to `.pitch`,
    or the output of `score_slices.slice_to_pitch_collection`);
    3. an iterable of anything `Pitch(...)` accepts:
    (MIDI numbers, or note-name strings such as `"E-6"`).

    Parameters
    ----------
    pitches : PitchCollection or Iterable[Pitch | int | float | str]

    Returns
    -------
    PitchCollection
    """
    if isinstance(pitches, PitchCollection):
        return pitches
    pitches = list(pitches)
    if pitches and isinstance(pitches[0], Pitch):
        return PitchCollection(list(pitches))
    return PitchCollection([Pitch(p) for p in pitches])


def pitch_string_to_pitch_collection(
    pitch_string: str, accidental_chars: Optional[str] = "-#"
) -> PitchCollection:
    """
    Convenience parser for space-separated pitch-name strings.

    E.g., `"E-6 G#5 B4 G4"` -> a `PitchCollection` of 4 `Pitch` objects.

    This mirrors the YCACL `pitches_string_to_MIDI_list`-based interface,
    and exists purely for the literature-style doctest examples below.

    It is *not* used internally by `is_freie_Leittoneinstellung`,
    which works on `PitchCollection` from end to end.

    Parameters
    ----------
    pitch_string : str
        Space-separated pitch names, e.g., `"E-6 G#5 B4 G4"`.
    accidental_chars : str, optional
        Passed to `Pitch(..., accidental_chars=...)`. Defaults to `"-#"`
        (flats as `-`, sharps as `#`), matching the format used in this
        module's docstring examples.

    Returns
    -------
    PitchCollection
    """
    return PitchCollection(
        [
            Pitch(name, accidental_chars=accidental_chars)
            for name in pitch_string.split()
        ]
    )


@dataclass
class SpellingRequirements:
    """
    Stub for enharmonic-spelling constraints on a freie Leittoneinstellung.

    `is_freie_Leittoneinstellung` currently works entirely on MIDI pitch numbers
    (i.e., no spelling).

    This class is a placeholder for possible future spelling constraints later.

    Not yet implemented:
    `check` is permissive (always `True`)
    until the criteria below (or others raised in review) are agreed and coded up.

    Parameters
    ----------
    require_slice_1_remote_spelling : bool, default=False
        Reserved; not yet implemented.
    require_simplest_resolution_spelling : bool, default=False
        Reserved; not yet implemented.
    max_alteration : int or None, default=None
        Reserved; not yet implemented.
    """

    require_slice_1_remote_spelling: bool = False
    require_simplest_resolution_spelling: bool = False
    max_alteration: Optional[int] = None

    def check(self, slice_1: PitchCollection, slice_2: PitchCollection) -> bool:
        """Check `slice_1`/`slice_2` against these spelling requirements.

        Currently, this is a stub: always returns True regardless of settings.

        Parameters
        ----------
        slice_1 : PitchCollection
        slice_2 : PitchCollection

        Returns
        -------
        bool
        """
        # TODO: implement the criteria described in the class docstring.
        return True


def _chord_quality(collection: PitchCollection) -> Optional[str]:
    """Return `Chord.from_pitch_collection(collection).quality`, if any."""
    return Chord.from_pitch_collection(collection).quality


def is_freie_Leittoneinstellung(
    slice_1: PitchesLike,
    slice_2: PitchesLike,
    require_no_common_tone: bool = False,
    require_slice_1_not_common: bool = True,
    require_slice_2_common: bool = True,
    min_distinct: int = 3,
    max_step: int = 1,
    spelling_requirements: Optional[SpellingRequirements] = None,
):
    """
    Checks if a pair of successive 'slices' (vertical cross-section)
    make a potential case of the 'freie Leittoneinstellung' as defined in the following.

    Reference to this in music theoretic literature lacks a robust and consistent definition;
    this is a first attempt to implement one.

    Here then are the proposed rules based on trial and error for catching
    all and only the relevant cases.

    IN THEORY

    1. `slice_1`: the moment of potential freie Leittoneinstellung.
    Expressed as a chord, this slice may be required to
    - have a certain number of distinct pitch classes
      (`min_distinct`: default = 3)
    - not be triad or a seventh, nor an incomplete case of either.

    2. `slice_2`: the slice after (the 'destination' chord or 'moment of resolution')
    This chord, by contrast, *must* be either a triad or a seventh.

    Note that as long as `slice_1` isn't a (in-)complete triad or seventh,
    and the `slice_2` is,
    then definitely we don't have a simple repetition
    or even a sub-/superset relationship.

    3. Chromatic Motion
    Every pitch may be requried to move by not more than a specific interval
    (`max_step`: default = 1)
    half-step away from at least one note in the second chord.
    This is currently calculated without pitch spelling
    (on MIDI pitch numbers),
    but that may change.
    There can also be a de facto minimum step by excuding common tones ...

    4. No common tones
    By default (`require_no_common_tone`),
    we require that all tones move from the `slice_1` to the resolution.
    Apart from the *maximum* inteval (discussed above),
    this requires that all tones do indeed *move*
    (i.e., have a de facto minimum interval).
    This is for various reasons including that
    chromatic motion over common tones often indicates
    other musical devices such as incomplete neighbour tones and appogiature.

    Parameters
    ----------
    slice_1 : PitchCollection or Iterable[Pitch | int | float | str]
        The candidate moment of freie Leittoneinstellung.
        Anything that `PitchCollection`, `Pitch`, or a `Slice`'s
        notes can supply is accepted;
        see `pitch_string_to_pitch_collection` for a string-based convenience.
    slice_2 : PitchCollection or Iterable[Pitch | int | float | str]
        The resolution chord. Same accepted shapes as `slice_1`.
    require_no_common_tone : bool, default=False
        See point 4 above.
    require_slice_1_not_common : bool, default=True
        See point 1 above.
    require_slice_2_common : bool, default=True
        See point 2 above.
    min_distinct : int, default=3
        Minimum number of distinct pitch classes required in `slice_1`.
        Must be 3 or more.
    max_step : int, default=1
        Maximum semitone distance
        (measured on MIDI pitch numbers, i.e., without spelling)
        permitted between a pitch in `slice_1` and the nearest in `slice_2`.
        See point 3 above.
    spelling_requirements : SpellingRequirements, optional
        Additional, orthogonal constraints on the *spelling*.
         Not yet implemented (stub); see `SpellingRequirements`.

    Classic examples include the following passage in
    measures 148-152 of Mozart 40, movement i.
    We analyse that passage as follows.

    First we have a pair parallel diminished 7ths.
    Our defaults exclude this as the first slice is a common chord:

    >>> is_freie_Leittoneinstellung(
    ...     pitch_string_to_pitch_collection("B5 G#5 D5 E#4"),
    ...     pitch_string_to_pitch_collection("C6 A5 E-5 F#4"),
    ... )
    False

    Then, next time the E-flat to D motion is reversed
    (the notes are "swapped"),
    making for a highly dissonant first chord,
    and a V7 on D as the resolution chord.
    This would not necessarily be enough,
    as "E-6 G#5 B4" can be spelt as "E-6 Ab-5 C-4"
    (i.e., another common chord).
    Mozart also adds a G-F# motion
    (the G being a false-relation against the G#).
    This seals the deal ;)

    >>> is_freie_Leittoneinstellung(
    ...     pitch_string_to_pitch_collection("E-6 G#5 B4 G4"),
    ...     pitch_string_to_pitch_collection("D6 A5 C5 F#4"),
    ... )
    True

    The third iteration sees the same pitches as this second case, re-voiced.
    """

    slice_1 = _to_pitch_collection(slice_1)
    slice_2 = _to_pitch_collection(slice_2)

    if min_distinct < 3:
        raise ValueError("The `min_distinct` value must be 3 or more.")

    # Slice 1
    num_distinct = len(slice_1.pitch_class_set)

    if num_distinct < min_distinct:
        return False

    if require_slice_1_not_common:
        if num_distinct == 3 and _chord_quality(slice_1) in TRIAD_QUALITIES:
            return False
        if num_distinct == 4 and _chord_quality(slice_1) in SEVENTH_QUALITIES:
            return False

    # Slice 2
    if require_slice_2_common:
        if (
            num_distinct == 3 and _chord_quality(slice_2) not in TRIAD_QUALITIES
        ):  # NB: not
            return False
        if (
            num_distinct == 4
            and _chord_quality(slice_2) not in SEVENTH_QUALITIES
        ):  # NB: not
            return False

    slice_pitches_1 = slice_1.pitch_num_multiset
    slice_pitches_2 = slice_2.pitch_num_multiset

    # Voice-leading 1: common tones
    if require_no_common_tone:
        # NB: this is deliberately at the level of exact MIDI pitch
        # (i.e., register-specific), not pitch class.
        # This may change or be user-settable to
        # pitch-class-level "common tone" (ignoring octave).
        intersect = [p for p in slice_pitches_1 if p in slice_pitches_2]
        if intersect:
            return False

    # Voice-leading 2: step size
    expanded = set()
    for x in slice_pitches_1:
        expanded.update(range(x - max_step, x + max_step + 1))
    for p in set(slice_pitches_2):
        if p not in expanded:
            return False

    # Voice-leading 3 (stub): spelling
    if spelling_requirements is not None and not spelling_requirements.check(
        slice_1, slice_2
    ):
        return False

    return True


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
