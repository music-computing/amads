# fmt: off
# flake8: noqa E129,E303
"""
Rudimentary `Chord` representation.
This is not intended to compete with fuller representations elsewhere
but to cover here in AMADS ("in house")
the basic functionality needed for the majority of use cases.

Note that the "chord" is almost always a somewhat abstract (often analytic) category,
even when included in notation.
Most symbols define limited elements.
The inclusion of pitch class is a normal minimum.
The root is common.
Spelling is often nominally present but with spelling as a more human-readable short-hand
(C# is clearer than 1)
with enharmonics actually treated arbitrarily (C# = Db).
Specific octaves are almost never specified.

The `Chord` here is defined in relation to the above as a broadly
pitch-class-level concept:
with a set of pitch classes,
and various options (root, quality label, and spelling).

This should explain the distinction of Chord from a `PitchCollection`:

Properties that cannot be determined from the available information are `None`.

We work with a quality registry (see `QUALITIES`) that maps canonical tonal qualities (mostly triads and sevenths)
to the corresponding semitone intervals above the root.
Further aliases normalise to those canonical names (see `_ALIASES`).

"""

import re
from typing import Optional, Sequence, Union

from amads.core.pitch import Pitch, PitchCollection
from amads.core.vector_transforms_checks import indices_to_indicator

QUALITIES: dict[str, tuple[int, ...]] = {
    "major":      (0, 4, 7),
    "minor":      (0, 3, 7),
    "diminished": (0, 3, 6),
    "augmented":  (0, 4, 8),
    "dominant7":  (0, 4, 7, 10),
    "major7":     (0, 4, 7, 11),
    "minor7":     (0, 3, 7, 10),
    "diminished7":(0, 3, 6, 9),
    "half-dim7":  (0, 3, 6, 10),
    "sus2":       (0, 2, 7),  # Note the rotation equivalence ...
    "sus4":       (0, 5, 7),  # ... between these two.
    "major6":     (0, 4, 7, 9),
    "minor6":     (0, 3, 7, 9),
    "dominant9":  (0, 4, 7, 10, 14),
    "major9":     (0, 4, 7, 11, 14),
    "minor9":     (0, 3, 7, 10, 14),
    "power":      (0, 7),  # "Power chord" = root and perfect 5th only. Very common in popular corpora.
    "root":       (0, ),  # Root only. Dubious as a "chord" but good to include e.g., used in Billboard corpus.
}


_ALIASES: dict[str, str] = {
    # triads
    "maj": "major", "M": "major", "": "major",
    "min": "minor", "m": "minor",
    "dim": "diminished", "°": "diminished",
    "aug": "augmented", "+": "augmented",
    # sevenths
    "7": "dominant7", "dom7": "dominant7",
    "maj7": "major7", "M7": "major7", "Δ": "major7", "Δ7": "major7",
    "min7": "minor7", "m7": "minor7",
    "dim7": "diminished7", "°7": "diminished7",
    "ø7": "half-dim7", "ø": "half-dim7", "m7b5": "half-dim7",
    # other
    "5": "power",
    "1": "root",
}

#: Reverse lookup: pitch-class intervals -> canonical quality name.
_INTERVAL_SET_TO_QUALITY: dict[frozenset[int], str] = {
    frozenset(intervals): name
    for name, intervals in QUALITIES.items()
}


# ---------------------------------------------------------------------------

_ROMAN_TO_DEGREE: dict[str, int] = {
    "I": 0, "II": 1, "III": 2, "IV": 3,
    "V": 4, "VI": 5, "VII": 6,
}

_ROMAN_RE = re.compile(
    r'^([b#]?)([IViv]+)([o°]?)(ø?)([\+]?)(\d*)$'
)

#: Scale intervals (minor = natural)
_MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)
_MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)

# Diatonic triad qualities by root
_MAJOR_TRIADS = ("major", "minor", "minor", "major",
                 "major", "minor", "diminished")
_MINOR_TRIADS = ("minor", "diminished", "major", "minor",
                 "minor", "major",  "major")


def _canonical_quality(quality: str) -> str:
    """Resolve a quality string to a canonical name, raising ValueError if unknown."""
    q = quality.strip()
    if q in QUALITIES:
        return q
    if q in _ALIASES:
        return _ALIASES[q]
    raise ValueError(
        f"Unknown chord quality {quality!r}. "
        f"Known qualities: {sorted(QUALITIES)} and aliases: {sorted(_ALIASES)}"
    )


def _parse_root(root: Union[str, int, Pitch]) -> Pitch:
    """Return a pitch-class-level Pitch from a name, int, or Pitch."""
    if isinstance(root, Pitch):
        return Pitch(root.key_num % 12, root.alt)
    if isinstance(root, int):
        return Pitch(root % 12)
    return Pitch(root, octave=None)  # octave=None → pitch-class (key_num 0-11)


def _parse_key(key: Union[str, int, Pitch]) -> tuple[tuple[int, ...], int]:
    """Return (scale, tonic_pc) from a key string, int, or Pitch.

    Key convention:
    Explicit `"… major"` or `"… minor"` overrides anything else.
    With this, we look at the root name case:
    uppercase = major;
    lowercase = minor.

    """
    if isinstance(key, (int, Pitch)):
        return _MAJOR_SCALE, int(_parse_root(key).key_num) % 12
    key_str = str(key).strip()
    if key_str.lower().endswith(" minor"):
        scale, tonic_name = _MINOR_SCALE, key_str[:-6].strip().capitalize()
    elif key_str.lower().endswith(" major"):
        scale, tonic_name = _MAJOR_SCALE, key_str[:-6].strip().capitalize()
    elif key_str[0].islower():
        scale, tonic_name = _MINOR_SCALE, key_str.capitalize()
    else:
        scale, tonic_name = _MAJOR_SCALE, key_str
    return scale, int(_parse_root(tonic_name).key_num) % 12


# ---------------------------------------------------------------------------


class Chord:
    """
    Represents a chord as a set of pitch classes,
    with optional root, quality, and spelling.
    Properties that cannot be determined are set to `None`.

    Parameters
    ----------
    root : str | int | Pitch | None
        The root of the chord, as a pitch name ("C"), pitch-class int (0), or Pitch.
        If `None`, a rootless chord is created from `pitches`.
    quality : str | None
        Quality string, e.g. "major", "min7", "°"
        typically as imported from some user provided string, or corpus source.
        If both `root` and `quality` are given, `pitches` is derived automatically.
        If only `root` is given, quality remains `None`
        unless it can be inferred from `pitches`.
    pitches : sequence of (str | int | Pitch) | None
        Explicit pitch members.
        Each element may be a pitch name ("Bb"), a pitch-class int (10), or a Pitch.
        If given alongside `root` and `quality`, these are stored as the chord's spelling.
    bass : str | int | Pitch | None
        The bass note if it differs from the root (slash chords, inversions).

    Attributes
    ----------
    root : Pitch | None
    quality : str | None
        Canonical quality name, e.g. "major", "minor7".
    pitches : tuple[Pitch, ...] | None
        Spelling as pitch-class Pitches (octave == -1), in the order given.
    bass : Pitch | None
    key : str | None
        Set when constructed via :meth:`from_roman`.

    Examples
    --------
    These examples demonstrate different ways to build `Chord` objects, and some of the attributes.

    1. From a root + quality string:

    >>> c = Chord("C", "major")
    >>> c
    Chord(C major)

    >>> c == Chord("C", "maj")
    True

    Here are some derived properties:

    >>> c.pitch_class_set
    [0, 4, 7]

    >>> c.intervals
    (0, 4, 7)

    >>> c.pitch_class_vector
    (1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0)

    Here is a different quality exmaple (see `QUALTIES` for all options):

    >>> Chord("G", "dominant7").label
    'G7'

    2. From a Roman numeral, given a key.

    >>> Chord.from_roman("IV", "C").root.name
    'F'

    >>> Chord.from_roman("V7", "G").label
    'D7'

    Roman numerals are complex and not consistent across standards.
    This illustrates a case in point:
    The triad in a minor key on the second degree is diminshed diatonically,
    and the seventh is a half-diminshed.
    Parsing routines vary.
    Here we take "ii7" to imply the diatonic half-diminshed,
    "iiø7" is equivalent (not needed to specify the half-diminshed)
    and "iio7" modifies to diminished.
    See also the `from_scale_degree` method (also demo'd here).

    >>> Chord.from_roman("ii", "d").label
    'Eo'

    >>> Chord.from_roman("ii7", "d").label
    'Eø7'

    >>> Chord.from_roman("iiø7", "d").label
    'Eø7'

    >>> Chord.from_scale_degree(2, "d").label
    'Eo'

    Explicit suffix takes priority over scale-stacking
    >>> Chord.from_roman("iio7", "d").label
    'Eo7'

    3. From pitches directly, either as pitch name or pitch class:

    >>> Chord(pitches=["C", "Eb", "G"]).quality
    'minor'

    >>> Chord(pitches=[0, 3, 7]).quality
    'minor'

    >>> Chord(pitches=["C", "E", "G", "Bb"]).label
    'C7'
    """

    __slots__ = ["root", "quality", "pitches", "bass", "key"]

    root:    Optional[Pitch]
    quality: Optional[str]
    pitches: Optional[tuple[Pitch, ...]]
    bass:    Optional[Pitch]
    key:     Optional[str]

    def __init__(
        self,
        root:    Union[str, int, Pitch, None] = None,
        quality: Optional[str]                = None,
        pitches: Optional[Sequence]           = None,
        bass:    Union[str, int, Pitch, None] = None,
    ) -> None:

        self.key = None
        self.root = _parse_root(root) if root is not None else None
        self.quality = _canonical_quality(quality) if quality is not None else None
        if pitches is not None: # Pitches explicitly supplied:
            self.pitches = tuple(_parse_root(p) for p in pitches)
        elif self.root is not None and self.quality is not None: # Derive pitches from root + quality:
            intervals = QUALITIES[self.quality]
            root_pc   = self.root.key_num % 12
            self.pitches = tuple(
                Pitch((root_pc + i) % 12)
                for i in intervals
            )
        else:
            self.pitches = None

        # Derive quality from pitches:
        if self.quality is None and self.pitches is not None:
            self.quality = self._infer_quality()

        # Derive root from pitches + quality:
        if self.root is None and self.quality is not None and self.pitches is not None:
            self.root = self._infer_root()

        self.bass = _parse_root(bass) if bass is not None else None

    @classmethod
    def from_roman(cls, numeral: str, key: Union[str, int, Pitch], *, seventh: bool = False) -> "Chord":
        scale, tonic_pc = _parse_key(key)
        key_str = str(key).strip()  # preserved for chord.key attribute only
        raw = numeral.strip()

        m = _ROMAN_RE.match(raw)
        if not m:
            raise ValueError(f"Unrecognised Roman numeral {numeral!r}.")
        accidental, core_raw, dim_flag, hdim_flag, aug_flag, num_str = m.groups()

        core = core_raw.upper()
        if core not in _ROMAN_TO_DEGREE:
            raise ValueError(f"Unrecognised Roman numeral {numeral!r}.")

        add7 = bool(num_str) or seventh
        degree = _ROMAN_TO_DEGREE[core]

        # Handle chromatic roots (bVII, #IV etc.)
        root_pc = (tonic_pc + scale[degree]) % 12
        if accidental == 'b':
            root_pc = (root_pc - 1) % 12
        elif accidental == '#':
            root_pc = (root_pc + 1) % 12

        # Explicit suffix takes priority over scale-stacking
        if hdim_flag:
            quality = "half-dim7" if add7 else "diminished"  # ø alone = diminished triad conventionally
        elif dim_flag:  # o or °
            quality = "diminished7" if add7 else "diminished"
        elif aug_flag:
            quality = "augmented"
        else:
            # Derive quality by stacking scale tones
            n_tones = 4 if add7 else 3
            stacked_pcs = [
                (tonic_pc + scale[(degree + 2 * i) % 7]) % 12
                for i in range(n_tones)
            ]
            intervals = frozenset((pc - root_pc) % 12 for pc in stacked_pcs)
            quality = _INTERVAL_SET_TO_QUALITY.get(intervals)
            if quality is None:
                raise ValueError(
                    f"Scale-stacked intervals {intervals} for {numeral!r} in {key!r} "
                    f"don't match any known quality."
                )

        chord = cls(Pitch(root_pc), quality)
        chord.key = key_str
        return chord

    @classmethod
    def from_scale_degree(
            cls,
            degree: int,
            key: Union[str, int, Pitch],
            *,
            seventh: bool = False,
    ) -> "Chord":
        """
        Alternate constructor for making a `Chord` from a scale degree and key.

        Parameters
        ----------
        degree : int
            Scale degree.
            Note that this is 1-indexed (1 = tonic, ..., 7 = leading tone).
        key : str | int | Pitch
            Key, e.g. `"C"`, `"d"` (lower-case = minor) ...
        seventh : bool
            If True, stack the diatonic seventh above the triad.

        Returns
        -------
        Chord

        Raises
        ------
        ValueError
            If *degree* is outside 1–7.

        Examples
        --------
        >>> Chord.from_scale_degree(2, "C").label
        'Dm'

        >>> ii7 = Chord.from_scale_degree(2, "C", seventh=True)
        >>> ii7.label
        'Dm7'

        >>> ii7.intervals
        (0, 3, 7, 10)

        >>> Chord.from_scale_degree(7, "C").label
        'Bo'

        >>> Chord.from_scale_degree(2, "d").label
        'Eo'

        >>> Chord.from_scale_degree(2, "d", seventh=True).label
        'Eø7'
        """
        if not 1 <= degree <= 7:
            raise ValueError(f"Scale degree must be between 1 and 7, got {degree!r}.")
        numeral = ["I", "II", "III", "IV", "V", "VI", "VII"][degree - 1]
        return cls.from_roman(numeral, key, seventh=seventh)

    @classmethod
    def from_pitch_collection(cls, collection: PitchCollection) -> "Chord":
        """
        Alternate constructor for making a `Chord` from a PitchCollection.

        Quality is identified by matching the pitch-class set against the
        quality registry under all rotations (potential roots).  If exactly
        one root yields a known quality, both are set; if multiple match
        (e.g. augmented triads), root is left None.  Spelling is preserved
        from the collection.

        Parameters
        ----------
        collection : PitchCollection

        Returns
        -------
        Chord
        """
        pitches = collection.pitches
        pc_pitches: list[Pitch] = [Pitch(p.key_num % 12, p.alt) for p in pitches]
        pc_set = frozenset(p.key_num % 12 for p in pc_pitches)

        # try each member as potential root
        matches: list[tuple[Pitch, str]] = []
        for candidate_root in pc_set:
            intervals = tuple(sorted((pc - candidate_root) % 12 for pc in pc_set))
            key = frozenset(intervals)
            if key in _INTERVAL_SET_TO_QUALITY:
                matches.append((Pitch(candidate_root), _INTERVAL_SET_TO_QUALITY[key]))

        chord = cls.__new__(cls)
        chord.key  = None
        chord.bass = pc_pitches[0] if pc_pitches else None
        chord.pitches = tuple(pc_pitches)

        if len(matches) == 1:
            chord.root, chord.quality = matches[0]
        elif len(matches) > 1:
            # ambiguous (e.g. augmented): no single root
            chord.root    = None
            chord.quality = matches[0][1]  # at least quality is unambiguous
        else:
            chord.root    = None
            chord.quality = None

        return chord

    def _infer_quality(self) -> Optional[str]:
        """
        Helper to try and identify quality from self.pitches, trying each member as root."""
        if not self.pitches:
            return None
        pc_set = frozenset(int(p.key_num) % 12 for p in self.pitches)
        # try root first if known
        candidates = (
            [int(self.root.key_num) % 12] if self.root is not None
            else [int(p.key_num) % 12 for p in self.pitches]
        )
        for r in candidates:
            intervals = frozenset(sorted((pc - r) % 12 for pc in pc_set))
            if intervals in _INTERVAL_SET_TO_QUALITY:
                return _INTERVAL_SET_TO_QUALITY[intervals]
        return None

    def _infer_root(self) -> Optional[Pitch]:
        """
        Helper to find the root that makes self.quality consistent with self.pitches.
        """
        if not self.pitches or not self.quality:
            return None
        target = frozenset(QUALITIES[self.quality])
        for p in self.pitches:
            r = int(p.key_num) % 12
            intervals = frozenset((int(q.key_num) % 12 - r) % 12 for q in self.pitches)
            if intervals == target:
                return Pitch(r)
        return None

    @property
    def pitch_class_set(self) -> Optional[list[int]]:
        """Sorted list of pitch classes, or None if pitches unknown."""
        if self.pitches is None:
            return None
        return sorted(set(int(p.key_num) % 12 for p in self.pitches))

    @property
    def pitch_class_vector(self) -> Optional[tuple[int, ...]]:
        """12-dimensional indicator vector, or None if pitches unknown."""
        if self.pitch_class_set is None:
            return None
        return indices_to_indicator(self.pitch_class_set, indicator_length=12)

    @property
    def pitch_names(self) -> Optional[list[str]]:
        """Spelled pitch names (e.g. ["C", "Eb", "G"]), or None."""
        if self.pitches is None:
            return None
        return [p.name for p in self.pitches]

    def __contains__(self, item: Union[str, int, Pitch]) -> bool:
        pc = _parse_root(item).key_num % 12
        if self.pitches is not None:
            return any(int(p.key_num) % 12 == pc for p in self.pitches)
        if self.root is not None and self.quality is not None:
            root_pc = int(self.root.key_num) % 12
            return ((pc - root_pc) % 12) in QUALITIES[self.quality]
        return False

    def __len__(self) -> int:
        """Number of distinct pitch classes."""
        return len(self.pitch_class_set) if self.pitch_class_set is not None else 0

    # Hereafter the properties move to those usable when root is known

    @property
    def intervals(self) -> Optional[tuple[int, ...]]:
        """Semitone intervals above the root, or None if root unknown."""
        if self.root is None or self.pitches is None:
            return None
        r = int(self.root.key_num) % 12
        return tuple(sorted((int(p.key_num) % 12 - r) % 12 for p in self.pitches))

    @property
    def inversion(self) -> Optional[int]:
        """0 = root position, 1 = first inversion, etc.; None if undetermined."""
        if self.root is None or self.pitches is None or not self.pitches:
            return None
        bass_pc = int(self.pitches[0].key_num) % 12
        root_pc = int(self.root.key_num) % 12
        if bass_pc == root_pc:
            return 0
        if self.intervals is None:
            return None
        intervals_list = list(self.intervals)
        bass_interval = (bass_pc - root_pc) % 12
        try:
            return intervals_list.index(bass_interval)
        except ValueError:
            return None

    @property
    def label(self) -> Optional[str]:
        """
        Short label like "Cmaj7", "Dmin", "G7".
        Broadly matches leadsheet notation.

        Returns `None` if either or both of root or quality unknown.
        """
        if self.root is None or self.quality is None:
            return None
        root_name = self.root.name

        # Concise suffixes for common qualities
        _LABEL_SUFFIX: dict[str, str] = {
            "major":       "",
            "minor":       "m",
            "diminished":  "o",
            "augmented":   "+",
            "dominant7":   "7",
            "major7":      "M7",
            "minor7":      "m7",
            "diminished7": "o7",
            "half-dim7":   "ø7",
            "sus2":        "sus2",
            "sus4":        "sus4",
            "major6":      "6",
            "minor6":      "min6",
            "dominant9":   "9",
            "major9":      "maj9",
            "minor9":      "min9",
            "power":       "5",
        }
        suffix = _LABEL_SUFFIX.get(self.quality, self.quality)

        bass_str = ""
        if self.bass is not None:
            bass_pc = int(self.bass.key_num) % 12
            root_pc = int(self.root.key_num) % 12
            if bass_pc != root_pc:
                bass_str = f"/{self.bass.name}"

        return f"{root_name}{suffix}{bass_str}"

    def roman_numeral(self, key: Union[str, int, Pitch]) -> Optional[str]:
        """Return the Roman numeral of this chord in the given key, or None."""
        if self.root is None or self.quality is None:
            return None

        scale, tonic_pc = _parse_key(key)
        root_pc  = int(self.root.key_num) % 12
        interval = (root_pc - tonic_pc) % 12

        if interval not in scale:
            return None  # chromatic root — don't attempt diatonic numeral

        degree = scale.index(interval)
        numerals = ["I", "II", "III", "IV", "V", "VI", "VII"]
        numeral  = numerals[degree]

        # lowercase for minor/diminished
        if self.quality in ("minor", "minor7", "diminished", "diminished7", "half-dim7"):
            numeral = numeral.lower()
        if self.quality in ("diminished", "diminished7"):
            numeral += "°"
        if self.quality in ("dominant7", "major7", "minor7",
                            "diminished7", "half-dim7"):
            numeral += "7"

        return numeral

    # Dunder / display

    def __repr__(self) -> str:
        parts = []
        if self.root is not None:
            parts.append(self.root.name)
        if self.quality is not None:
            parts.append(self.quality)
        if not parts and self.pitches is not None:
            parts.append(str(self.pitch_names))
        inner = " ".join(parts) if parts else "unknown"
        return f"Chord({inner})"

    def __eq__(self, other: object) -> bool:
        """Enharmonic pitch-class equality: same pc set, root, quality."""
        if not isinstance(other, Chord):
            return False
        return (
            self.pitch_class_set == other.pitch_class_set
            and (
                (self.root is None and other.root is None)
                or (
                    self.root is not None
                    and other.root is not None
                    and self.root.key_num % 12 == other.root.key_num % 12
                )
            )
            and self.quality == other.quality
        )

    def __hash__(self) -> int:
        pcs = tuple(self.pitch_class_set or [])
        root_pc = int(self.root.key_num) % 12 if self.root is not None else None
        return hash((pcs, root_pc, self.quality))


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
