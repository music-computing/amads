"""
Core primitives for implemented Rohrmeier 2011 [1],
shared by the generator and parser.

This module deliberately contains no grammar rules (see `parser.py`).

Here, we define only:
- `Key`: a pitch-class + mode pair, with conversion to/from the string
  format expected by `amads.core.chord.Chord`.
- `FUNCTION_REALIZATION`: the function -> scale-degree table of rules
  (20)-(27) in the paper.
- `psi()`: the key-typecasting function used by the modulation rule (15),
  i.e. psi(X, key) -> the new local key when functional term X becomes
  the new tonic.

Note: some of this may more position in AMADS and or be refactored.

Clear reference is made throughout to the paper's rules (by number) in docstrings/comments.

[1] Martin Rohrmeier. 2011.
Towards a generative syntax of tonal harmony.
J. of Mathematics and Music.
DOI: 10.1080/17459737.2011.573676


"""

from dataclasses import dataclass
from typing import Literal, Optional

from amads.core.chord import (
    MAJOR_SCALE,
    MAJOR_TRIADS,
    MINOR_SCALE,
    MINOR_TRIADS,
    Chord,
)
from amads.core.pitch import Pitch

Mode = Literal["major", "minor"]

#: Regions (rules 4-10)
REGIONS = ("TR", "DR", "SR")

#: Functional terms (F), rules (11)-(14) substitutions plus the three primaries
FUNCTIONS = ("t", "s", "d", "tp", "sp", "dp", "tcp")

DEGREE_NAME = ["I", "II", "III", "IV", "V", "VI", "VII"]


@dataclass(frozen=True)
class Key:
    """A pitch-class + mode pair. `tonic_pc` is 0-11 (0 = C)."""

    tonic_pc: int
    mode: Mode

    def __post_init__(self):
        if self.mode not in ("major", "minor"):
            raise ValueError(
                f"For this module, the mode must be 'major' or 'minor', got {self.mode!r}. "
                "See the Tonfeld module for wider options."
            )
        object.__setattr__(self, "tonic_pc", self.tonic_pc % 12)

    # interoperate with amads.core.chord. TODO may be refactored

    @property
    def tonic_name(self) -> str:
        return Pitch(self.tonic_pc).name

    def as_chord_key_str(self) -> str:
        """String accepted by `Chord.from_roman` / `Chord.from_scale_degree`
        (e.g. 'C' for C major, 'c' for C minor)."""
        name = self.tonic_name
        return name if self.mode == "major" else name.lower()

    @classmethod
    def from_str(cls, s: str) -> "Key":
        """Inverse of as_chord_key_str, e.g. 'C' -> major, 'c' -> minor,
        also accepts 'C major' / 'c minor' / 'C minor' explicit forms."""
        s = s.strip()
        if s.lower().endswith(" minor"):
            return cls(Pitch(s[:-6].strip().capitalize()).key_num % 12, "minor")
        if s.lower().endswith(" major"):
            return cls(Pitch(s[:-6].strip().capitalize()).key_num % 12, "major")
        mode: Mode = "minor" if s[0].islower() else "major"
        return cls(Pitch(s.capitalize()).key_num % 12, mode)

    # diatonic helpers

    def scale(self) -> tuple[int, ...]:
        return MAJOR_SCALE if self.mode == "major" else MINOR_SCALE

    def triads(self) -> tuple[str, ...]:
        return MAJOR_TRIADS if self.mode == "major" else MINOR_TRIADS

    def degree_pc(self, degree: int) -> int:
        """1-indexed scale degree -> absolute pitch class."""
        return (self.tonic_pc + self.scale()[degree - 1]) % 12

    def degree_triad_quality(self, degree: int) -> str:
        return self.triads()[degree - 1]

    def relative_to(self, semitones: int, new_mode: Mode) -> "Key":
        return Key((self.tonic_pc + semitones) % 12, new_mode)

    def __str__(self) -> str:
        return f"{self.tonic_name}{'' if self.mode == 'major' else 'm'}"


# ---------------------------------------------------------------------------

FUNCTION_REALIZATION: dict[str, dict[Mode, list[tuple[int, Optional[str]]]]] = {
    "t": {"major": [(1, None)], "minor": [(1, None)]},  # rule 20
    "s": {"major": [(4, None)], "minor": [(4, None)]},  # rule 22
    "d": {
        "major": [(5, "dominant7"), (7, "diminished7")],  # rule 23: V | VII
        "minor": [(5, "dominant7"), (7, "diminished7")],
    },
    "tp": {"major": [(6, None)], "minor": [(3, None)]},  # rule 24
    "dp": {"minor": [(7, None)]},  # rule 25 (major: undefined)
    "sp": {"major": [(2, None)], "minor": [(6, None), (2, None)]},  # rule 26
    "tcp": {"major": [(3, None)], "minor": [(6, None)]},  # rule 27
}


def function_to_chord(
    function: str, key: Key, degree_choice: int = 0, seventh: bool = False
) -> Chord:
    """
    Function -> scale degree / Chord as per, rules (20)-(27).

    Each entry: function label -> {mode: [(degree, quality_override), ...]}

    Internally uses a `quality_override` which is usually None
    (this meaning "use the diatonic triad quality", i.e. whatever Key.degree_triad_quality gives).

    Where `quality_override` is specified,
    a fixed Chord quality name is locally hard-coded to override diatonic stacking.
    This is currently needed only for `d` due to the perennial issue of
    raised leading tone dominants in minor.

    Where a rule lists multiple options (e.g. sp in minor: "VI, II"), all options are listed.
    The generator picks one from this list; the parser will try all.
    """
    options = FUNCTION_REALIZATION[function].get(key.mode)
    if not options:
        raise ValueError(
            f"Function {function!r} has no realization in {key.mode} (see rule 20-27)."
        )
    degree, quality_override = options[degree_choice % len(options)]

    if (
        function == "d" and degree == 7
    ):  # Special case, cf Rule 19's "missing fundamental" VII substitute.
        root_pc = (key.tonic_pc + 11) % 12
        return Chord(Pitch(root_pc), quality_override)
    if quality_override is not None:
        root_pc = key.degree_pc(degree)
        return Chord(Pitch(root_pc), quality_override)
    return Chord.from_scale_degree(
        degree, key.as_chord_key_str(), seventh=seventh
    )


# ---------------------------------------------------------------------------


def psi(function: str, key: Key, degree_choice: int = 0) -> Optional[Key]:
    """
    Modulation type-casting, rule (15):
    X_key=y -> TR_key=psi(X,y)   for any X in F (except t), y in K

    psi(X, key) = the new key whose tonic is X's scale-degree root in `key`,
    and whose mode is the diatonic triad quality on that degree.

    Note that
    - a diminished triad cannot define a mode, so it cannot instantiate a modulation
    - Returns None if `function` cannot license a modulation from `key`
    either because the target is diminished (as above), or it's the tonic itself.
    """
    if function == "t":
        return None  # tonic is excluded by definition (paper, section 3.2.3)
    options = FUNCTION_REALIZATION[function].get(key.mode)
    if not options:
        return None
    degree, quality_override = options[degree_choice % len(options)]
    quality = quality_override or key.degree_triad_quality(degree)
    new_mode = _QUALITY_TO_MODE.get(quality)
    if new_mode is None:
        return (
            None  # e.g. diminished/half-diminished triads cannot define a mode
        )
    return key.relative_to(key.scale()[degree - 1], new_mode)


#: Which triad/seventh qualities can license a mode for modulation purposes.
_QUALITY_TO_MODE: dict[str, Mode] = {
    "major": "major",
    "dominant7": "major",
    "major7": "major",
    "minor": "minor",
    "minor7": "minor",
    # diminished / diminished7 / half-dim7 / augmented: no valid mode -> excluded
}
