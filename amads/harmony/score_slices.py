"""
score_slices.py

Turn a score into a sequence of vertical ("salami") slices,
and iterate over successive *pairs* of neighbouring slices
to review voice-leading-style analyses such as `is_freie_Leittoneinstellung`.

Typical use
-----------
>>> slices = get_score_slices("mozart40_i.musicxml")  # doctest: +SKIP
>>> for pc1, pc2 in iter_slice_pair_collections(slices):  # doctest: +SKIP
...     if is_freie_Leittoneinstellung(pc1, pc2):
...         print(slice_to_pitch_string(pc1), "->", slice_to_pitch_string(pc2))

Given an in-memory `Score`
(built programmatically, or read via some other AMADS-connected library),
pass it directly instead of a filename.

>>> slices = get_score_slices(my_score)  # doctest: +SKIP

<small>**Author**: Mark Gotham.</small>
"""

from pathlib import Path
from typing import Iterable, Iterator, List, Tuple, Union

from amads.algorithms.slice.salami import salami_slice
from amads.algorithms.slice.slice import Slice
from amads.core.basics import Note, Score
from amads.core.pitch import PitchCollection
from amads.io.readscore import read_score

__author__ = "Mark Gotham"

# Accidental characters matching the format used by `Pitch.from_name`
# and the docstring examples in `freie_leittoneinstellung`
# (e.g., "E-6 G#5 B4 G4" -- flats as "-", sharps as "#").
_ACCIDENTAL_CHARS = "-#"


def _pitch_name_with_octave(pitch, accidental_chars: str) -> str:
    """
    Render `pitch` as name + octave, honouring `accidental_chars`.

    TODO this currently works around `Pitch.get_name_with_octave()`,
    which currently ignores its own `accidental_chars` parameter
    and always falls back to "b#"
    (it delegates to the `name` property rather than `get_name()`).
    Probably an AMADS upstream bug.
    `Pitch.get_name()` is unaffected and used here directly instead.
    """
    if pitch.midi_num is None:
        return "unpitched"
    return f"{pitch.get_name(accidental_chars=accidental_chars)}{pitch.octave}"


def get_score_slices(
    score: Union[str, Path, Score],
    remove_duplicated_pitches: bool = True,
    include_note_end_slices: bool = True,
    min_slice_duration: float = 0.01,
) -> List[Slice]:
    """
    Split a score into salami (vertical) slices.

    This is broadly the AMADS equivalent of comparable functionality elsewhere
    such as music21's `Score.chordify()`,
    except that it slices at every note
    onset and *offset* (see `include_note_end_slices`)
    and returns AMADS' own `Slice` objects rather than `Chord` objects.

    Parameters
    ----------
    score : str | Path | Score
        Either
        1) an already-loaded AMADS `Score`
        (e.g., built programmatically, via `Score.from_melody`,
        or read by some other AMADS-connected library),
        which is used as-is with no I/O;
        or
        2) a path (or URL) to a score file, in any format AMADS'
        `read_score` supports (musicxml, midi, kern, mei, ...),
        read via `read_score` first.
        Callers who already have `Pitch`/`PitchCollection` data
        and don't need a `Score` at all
        (e.g., loading from a bespoke corpus format)
        can skip this function and build `PitchCollection` pairs directly.
        For instance, `is_freie_Leittoneinstellung` doesn't
        *require* a `Score` or `Slice`.
    remove_duplicated_pitches : bool, default=True
        Whether to remove duplicate pitches (e.g., octave doublings)
        within each slice.
    include_note_end_slices : bool, default=True
        Whether a note *ending* (with no new note starting) triggers
        a new slice.
    min_slice_duration : float, default=0.01
        Minimum duration for a slice to be included; filters out
        near-simultaneous onsets that would otherwise produce
        degenerately short slices.

    Returns
    -------
    List[Slice]
        The score's vertical slices, in time order.
    """
    if not isinstance(score, Score):
        score = read_score(score, flatten=True, collapse=True)
    notes: List[Note] = score.get_sorted_notes()

    return salami_slice(
        notes,
        remove_duplicated_pitches=remove_duplicated_pitches,
        include_note_end_slices=include_note_end_slices,
        min_slice_duration=min_slice_duration,
    )


def slice_to_pitch_collection(a_slice: Slice) -> PitchCollection:
    """Render a `Slice`'s pitches as a `PitchCollection`.

    This is the primary bridge to `is_freie_Leittoneinstellung`
    (and any other `PitchCollection`-based analysis):
    it carries full `Pitch` objects (spelling included),
    with no lossy round-trip through a string or bare MIDI-number representation.

    Parameters
    ----------
    a_slice : Slice
        The slice to render.

    Returns
    -------
    PitchCollection
    """
    return PitchCollection([note.pitch for note in a_slice.content])


def slice_to_pitch_string(
    a_slice_or_collection: Union[Slice, PitchCollection]
) -> str:
    """
    Render a `Slice` (or `PitchCollection`)
    as a human-readable pitch-name string (e.g., "E-6 G#5 B4 G4")
    for logging, printing, or writing doctest-style examples.
    Not otherwise used internally
    (`PitchCollection`/`Pitch` objects direct via `slice_to_pitch_collection`).

    Parameters
    ----------
    a_slice_or_collection : Slice | PitchCollection
        The slice (or already-converted collection) to render.

    Returns
    -------
    str
        Space-separated pitch names with octave.
    """
    if isinstance(a_slice_or_collection, PitchCollection):
        pitches = a_slice_or_collection.pitches
    else:
        pitches = [note.pitch for note in a_slice_or_collection.content]
    return " ".join(
        _pitch_name_with_octave(p, _ACCIDENTAL_CHARS) for p in pitches
    )


def iter_slice_pairs(slices: Iterable[Slice]) -> Iterator[Tuple[Slice, Slice]]:
    """Yield each pair of temporally successive slices.

    Given slices [s0, s1, s2, s3, ...],
    yields (s0, s1), (s1, s2), (s2, s3), ...

    Parameters
    ----------
    slices : Iterable[Slice]
        Slices in time order (e.g., from `get_score_slices`).

    Yields
    ------
    Tuple[Slice, Slice]
        Each successive pair of slices.
    """
    slices = list(slices)
    for slice_1, slice_2 in zip(slices, slices[1:]):
        yield slice_1, slice_2


def iter_slice_pair_collections(
    slices: Iterable[Slice],
) -> Iterator[Tuple[PitchCollection, PitchCollection]]:
    """Like `iter_slice_pairs`,
    but each slice is rendered as a `PitchCollection`,
    ready to hand straight to `PitchCollection`-based analyses
    such as `is_freie_Leittoneinstellung`.

    Parameters
    ----------
    slices : Iterable[Slice]
        Slices in time order (e.g., from `get_score_slices`).

    Yields
    ------
    Tuple[PitchCollection, PitchCollection]
        (slice_1_collection, slice_2_collection) for each successive pair.
    """
    for slice_1, slice_2 in iter_slice_pairs(slices):
        yield slice_to_pitch_collection(slice_1), slice_to_pitch_collection(
            slice_2
        )


def iter_slice_pair_strings(
    slices: Iterable[Slice],
) -> Iterator[Tuple[str, str]]:
    """
    Like `iter_slice_pairs`, but each slice is rendered as a pitch-name string.
    Kept as a convenience for logging/printing;
    prefer `iter_slice_pair_collections` when feeding an analysis function.

    Parameters
    ----------
    slices : Iterable[Slice]
        Slices in time order (e.g., from `get_score_slices`).

    Yields
    ------
    Tuple[str, str]
        (slice_1_string, slice_2_string) for each successive pair.
    """
    for slice_1, slice_2 in iter_slice_pairs(slices):
        yield slice_to_pitch_string(slice_1), slice_to_pitch_string(slice_2)
