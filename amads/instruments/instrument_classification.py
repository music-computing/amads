"""
instruments.core
================
Core dataclasses and logic for instrument classification.

Hornbostel-Sachs (HS) classification system overview
-----------------------------------------------------
1  – Idiophones      (sound from the body itself)
2  – Membranophones  (sound from a stretched membrane)
3  – Chordophones    (sound from stretched strings)
4  – Aerophones      (sound from vibrating air)
    42  – Woodwinds (edge-blown or reed)
        421 – flutes / edge aerophones
        422 – reed aerophones
            4221 – single-reed
            4222 – double-reed
    423 – Brass / lip-vibrated aerophones
5  – Electrophones   (electrically generated sound)
(6) – Voice          (not in original HS but commonly appended)


<small>**Author**: Mark Gotham (2026)</small>

"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

__author__ = "Mark Gotham"


# ---------------------------------------------------------------------------

# Enumerations


class Family(str, Enum):
    """High-level organological family."""

    WOODWIND = "Woodwind"
    BRASS = "Brass"
    PERCUSSION = "Percussion"
    STRINGS = "Strings"
    VOICE = "Voice"
    KEYBOARD = "Keyboard"
    UNKNOWN = "Unknown"


# ---------------------------------------------------------------------------

# Hornbostel-Sachs classification


@dataclass(frozen=True)
class HSClass:
    """A single node in the Hornbostel-Sachs classification tree."""

    code: str  # e.g. "4222"
    name: str  # e.g. "Double-reed aerophone"
    description: str  # human-readable description

    def __str__(self) -> str:
        return f"[{self.code}] {self.name}"

    def top_level(self) -> str:
        """Return the top-level HS digit (e.g. '4' for Aerophones)."""
        return self.code[0] if self.code else ""


# Canonical HS class table (subset relevant to orchestral instruments)
HS_CLASSES: Dict[str, HSClass] = {
    "1": HSClass(
        "1",
        "Idiophones",
        "Instruments that produce sound from their own rigid body.",
    ),
    "11": HSClass(
        "11",
        "Concussion idiophones",
        "Two or more complementary parts struck together (e.g. cymbals).",
    ),
    "111": HSClass(
        "111",
        "Concussion idiophones – plates",
        "Flat plates struck together (e.g. orchestral cymbals).",
    ),
    "112": HSClass(
        "112",
        "Concussion idiophones – sticks",
        "Sticks or rods struck together (e.g. claves).",
    ),
    "12": HSClass(
        "12",
        "Struck idiophones",
        "A single object struck against another (e.g. triangle, bass drum rim).",
    ),
    "111.1": HSClass(
        "111.1",
        "Cymbals",
        "Concave metal plates clashed or suspended and struck.",
    ),
    "112.1": HSClass(
        "112.1", "Triangle", "Bent metal rod struck with a metal beater."
    ),
    "2": HSClass(
        "2",
        "Membranophones",
        "Instruments that produce sound through a vibrating stretched membrane.",
    ),
    "21": HSClass(
        "21",
        "Struck membranophones",
        "The membrane is struck directly or indirectly (e.g. drums).",
    ),
    "211": HSClass(
        "211",
        "Tubular drums – one-headed",
        "Single-headed drums (e.g. bass drum, timpani).",
    ),
    "211.1": HSClass(
        "211.1",
        "Kettledrums / Timpani",
        "Hemispherical bowl drums with tunable membrane.",
    ),
    "211.2": HSClass(
        "211.2", "Bass drum", "Large, low-pitched cylindrical drum."
    ),
    "3": HSClass(
        "3",
        "Chordophones",
        "Instruments that produce sound through vibrating strings.",
    ),
    "31": HSClass(
        "31", "Simple chordophones", "The string bearer is also the resonator."
    ),
    "32": HSClass(
        "32",
        "Composite chordophones",
        "Separate resonator attached to string bearer.",
    ),
    "321": HSClass(
        "321",
        "Lutes",
        "Strings run parallel to the soundboard (e.g. violin family).",
    ),
    "321.3": HSClass(
        "321.3",
        "Bowed lutes",
        "Strings excited by a bow (violin, viola, cello, bass).",
    ),
    "322": HSClass(
        "322",
        "Harps",
        "Strings perpendicular to the soundboard (e.g. orchestral harp).",
    ),
    "314": HSClass(
        "314",
        "Keyboard chordophones",
        "Strings set in motion via a keyboard mechanism (e.g. piano, harpsichord).",
    ),
    "4": HSClass(
        "4",
        "Aerophones",
        "Instruments that produce sound through vibrating air.",
    ),
    "42": HSClass(
        "42",
        "Wind instruments (proper)",
        "The player's air-stream is the primary vibrator.",
    ),
    "421": HSClass(
        "421",
        "Edge aerophones (flutes)",
        "Air is split against an edge to produce sound.",
    ),
    "421.1": HSClass(
        "421.1",
        "Side-blown flutes",
        "The embouchure hole is on the side of the tube (e.g. concert flute, piccolo).",
    ),
    "421.2": HSClass(
        "421.2",
        "End-blown flutes",
        "The player blows across the top of the tube (e.g. recorder).",
    ),
    "422": HSClass(
        "422", "Reed aerophones", "Sound produced by a vibrating reed or reeds."
    ),
    "4221": HSClass(
        "4221",
        "Single-reed aerophones",
        "One reed vibrates against a mouthpiece (e.g. clarinet, saxophone).",
    ),
    "4222": HSClass(
        "4222",
        "Double-reed aerophones",
        "Two reeds vibrate against each other (e.g. oboe, bassoon, contrabassoon).",
    ),
    "423": HSClass(
        "423",
        "Lip-reed aerophones (brass)",
        "The player's lips act as the reed (e.g. trumpet, horn, trombone, tuba).",
    ),
    "423.1": HSClass(
        "423.1",
        "Horns",
        "Conical-bore lip-vibrated aerophones (e.g. French/natural horn, cornet).",
    ),
    "423.2": HSClass(
        "423.2",
        "Trumpets",
        "Predominantly cylindrical-bore brass instruments (e.g. trumpet, cornet).",
    ),
    "423.3": HSClass(
        "423.3", "Trombones", "Slide-operated lip-vibrated aerophones."
    ),
    "423.4": HSClass(
        "423.4", "Tubas", "Low-pitched, wide-bore conical brass instruments."
    ),
    "6": HSClass(
        "6", "Voice", "The human singing voice (extension beyond original HS)."
    ),
    "6.1": HSClass(
        "6.1", "Soprano voice", "Highest female (or unchanged male) voice."
    ),
    "6.2": HSClass("6.2", "Alto voice", "Lower female voice (contralto)."),
    "6.3": HSClass("6.3", "Tenor voice", "Higher adult male voice."),
    "6.4": HSClass("6.4", "Bass voice", "Lowest adult male voice."),
}


# ---------------------------------------------------------------------------

# Instrument definitions


@dataclass
class Instrument:
    """
    A parsed, classified orchestral instrument.

    Attributes
    ----------
    raw        : original string as provided (e.g. "Bb Clarinet 2")
    canonical  : normalised instrument name without index (e.g. "Clarinet")
    display    : human-friendly full name (e.g. "Bb Clarinet 2")
    transposition : key transposition if present (e.g. "Bb", "D", "A")
    index      : number if present (e.g. 1, 2)
    family     : high-level instrument family (see `Family` enum)
    hs_class   : primary HSClass node
    is_solo    : True if the part is a labelled solo (e.g. "Soprano solo")
    notes      : any additional parenthetical annotation (e.g. "basso")
    """

    raw: str
    canonical: str
    display: str
    transposition: Optional[str]
    index: Optional[int]
    family: Family
    hs_class: HSClass
    is_solo: bool = False
    notes: str = ""

    # comparison / hashing on canonical + index
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Instrument):
            return NotImplemented
        return self.canonical == other.canonical and self.index == other.index

    def __hash__(self) -> int:
        return hash((self.canonical, self.index))

    def __repr__(self) -> str:
        solo = " [solo]" if self.is_solo else ""
        idx = f" #{self.index}" if self.index else ""
        trans = f" ({self.transposition})" if self.transposition else ""
        return (
            f"Instrument({self.canonical!r}{trans}{idx}{solo} | "
            f"{self.family.value} | {self.hs_class.code})"
        )

    def __str__(self) -> str:
        return (
            f"{self.display:<28} "
            f"family={self.family.value:<12} "
            f"hs={self.hs_class.code:<6} "
            f"({self.hs_class.name})"
        )


@dataclass
class InstrumentGroup:
    """
    A collection of Instrument objects sharing the same canonical name.

    Example: all "Violin" desks → InstrumentGroup("Violin", [inst1, inst2])
    """

    canonical: str
    members: List[Instrument] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"InstrumentGroup({self.canonical!r}, count={len(self.members)})"

    def __iter__(self):
        return iter(self.members)

    def __len__(self) -> int:
        return len(self.members)


# ---------------------------------------------------------------------------
# Lookup tables used by the parser


# (pattern, canonical, family, hs_code, notes_key)
# Patterns are matched case-insensitively against the *cleaned* token.
# Order matters: more specific entries first.
_INSTRUMENT_TABLE: List[Tuple[str, str, Family, str]] = [
    # Woodwind
    ("piccolo", "Piccolo", Family.WOODWIND, "421.1"),
    ("flute", "Flute", Family.WOODWIND, "421.1"),
    ("oboe d'amore", "Oboe d'amore", Family.WOODWIND, "4222"),
    ("cor anglais", "Cor anglais", Family.WOODWIND, "4222"),
    ("english horn", "English Horn", Family.WOODWIND, "4222"),
    ("oboe", "Oboe", Family.WOODWIND, "4222"),
    ("contrabassoon", "Contrabassoon", Family.WOODWIND, "4222"),
    ("bassoon", "Bassoon", Family.WOODWIND, "4222"),
    ("e-flat clarinet", "Eb Clarinet", Family.WOODWIND, "4221"),
    ("eb clarinet", "Eb Clarinet", Family.WOODWIND, "4221"),
    ("bass clarinet", "Bass Clarinet", Family.WOODWIND, "4221"),
    ("clarinet", "Clarinet", Family.WOODWIND, "4221"),
    ("soprano saxophone", "Soprano Sax", Family.WOODWIND, "4221"),
    ("alto saxophone", "Alto Sax", Family.WOODWIND, "4221"),
    ("tenor saxophone", "Tenor Sax", Family.WOODWIND, "4221"),
    ("baritone saxophone", "Baritone Sax", Family.WOODWIND, "4221"),
    ("saxophone", "Saxophone", Family.WOODWIND, "4221"),
    ("recorder", "Recorder", Family.WOODWIND, "421.2"),
    # Brass -------------------------------------------------------------
    ("horn", "Horn", Family.BRASS, "423.1"),
    ("trumpet", "Trumpet", Family.BRASS, "423.2"),
    ("cornet", "Cornet", Family.BRASS, "423.2"),
    ("flugelhorn", "Flugelhorn", Family.BRASS, "423.1"),
    ("alto trombone", "Alto Trombone", Family.BRASS, "423.3"),
    ("tenor trombone", "Tenor Trombone", Family.BRASS, "423.3"),
    ("bass trombone", "Bass Trombone", Family.BRASS, "423.3"),
    ("trombone", "Trombone", Family.BRASS, "423.3"),
    ("tuba", "Tuba", Family.BRASS, "423.4"),
    ("euphonium", "Euphonium", Family.BRASS, "423.4"),
    ("baritone horn", "Baritone Horn", Family.BRASS, "423.4"),
    # Percussion
    ("timpani", "Timpani", Family.PERCUSSION, "211.1"),
    ("bass drum", "Bass Drum", Family.PERCUSSION, "211.2"),
    ("snare drum", "Snare Drum", Family.PERCUSSION, "21"),
    ("cymbals", "Cymbals", Family.PERCUSSION, "111.1"),
    ("triangle", "Triangle", Family.PERCUSSION, "112.1"),
    ("xylophone", "Xylophone", Family.PERCUSSION, "1"),
    ("marimba", "Marimba", Family.PERCUSSION, "1"),
    ("vibraphone", "Vibraphone", Family.PERCUSSION, "1"),
    ("glockenspiel", "Glockenspiel", Family.PERCUSSION, "1"),
    ("tam-tam", "Tam-tam", Family.PERCUSSION, "1"),
    ("gong", "Gong", Family.PERCUSSION, "1"),
    ("tambourine", "Tambourine", Family.PERCUSSION, "2"),
    ("castanets", "Castanets", Family.PERCUSSION, "11"),
    ("crotales", "Crotales", Family.PERCUSSION, "1"),
    # Strings
    ("violin", "Violin", Family.STRINGS, "321.3"),
    ("viola", "Viola", Family.STRINGS, "321.3"),
    ("violoncello", "Violoncello", Family.STRINGS, "321.3"),
    ("cello", "Violoncello", Family.STRINGS, "321.3"),
    ("contrabass", "Contrabass", Family.STRINGS, "321.3"),
    ("double bass", "Contrabass", Family.STRINGS, "321.3"),
    ("harp", "Harp", Family.STRINGS, "322"),
    ("guitar", "Guitar", Family.STRINGS, "321.3"),
    # Voice -------------------------------------------------------------
    ("soprano", "Soprano", Family.VOICE, "6.1"),
    ("alto", "Alto", Family.VOICE, "6.2"),
    ("mezzo-soprano", "Mezzo-soprano", Family.VOICE, "6.1"),
    ("counter-tenor", "Counter-tenor", Family.VOICE, "6.3"),
    ("tenor", "Tenor", Family.VOICE, "6.3"),
    ("baritone", "Baritone", Family.VOICE, "6.4"),
    ("bass", "Bass", Family.VOICE, "6.4"),
    # Keyboard
    ("piano", "Piano", Family.KEYBOARD, "314"),
    ("harpsichord", "Harpsichord", Family.KEYBOARD, "314"),
    ("organ", "Organ", Family.KEYBOARD, "4"),
    ("celesta", "Celesta", Family.KEYBOARD, "314"),
]

# ---------------------------------------------------------------------------

# Token-level patterns


# Parenthetical notes e.g. "(basso)"
_PAREN_RE = re.compile(r"\(([^)]+)\)")

# Multi-pitch timpani specs like "D, A Timpani" — comma-joined so handled
# as a pre-pass before tokenisation.
_MULTI_PITCH_RE = re.compile(r"^([A-Ga-g][#b♯♭]?(?:,\s*[A-Ga-g][#b♯♭]?)+)\s+")

# A standalone transposition-key token: Bb / B-flat / Bflat / Eb / E-flat /
# Eflat / or any of the natural keys F G A D C.
_KEY_TOKEN_RE = re.compile(
    r"^(B(?:b|-?flat)?|E(?:b|-?flat)?|[FGADC])$",
    re.IGNORECASE,
)

# A standalone integer, optionally with an ordinal
# suffix so "1st", "2nd", "3rd", "4th" … also match.
_NUMBER_TOKEN_RE = re.compile(r"^(\d+)(?:st|nd|rd|th)?\.?$", re.IGNORECASE)

# Punctuation to strip from the edges of each token before classification.
_TOKEN_STRIP_RE = re.compile(r"^[^\w♭♯#]+|[^\w♭♯#]+$")

# Words that are pure syntax and carry no musical meaning.
_FILLER: frozenset = frozenset(
    {
        "in",
        "for",
        "di",
        "en",
        "im",
        "auf",
        "the",
        "a",
        "an",
        "und",
        "and",
    }
)


# ---------------------------------------------------------------------------
# Helpers


def _normalise_key(raw: str) -> str:
    """Return a canonical key label: 'Bb', 'Eb', or upper-case single letter.

    >>> _normalise_key("bb")
    'Bb'
    >>> _normalise_key("B-flat")
    'Bb'
    >>> _normalise_key("eb")
    'Eb'
    >>> _normalise_key("f")
    'F'
    >>> _normalise_key("D")
    'D'
    """
    s = raw.lower()
    if s in ("bb", "b-flat", "bflat"):
        return "Bb"
    if s in ("eb", "e-flat", "eflat"):
        return "Eb"
    return raw.upper()


def _strip_multi_pitch(text: str) -> Tuple[str, str]:
    """
    Remove a leading comma-joined pitch spec like 'D, A '.
    Returns (pitch_spec_without_trailing_space, remainder).

    >>> _strip_multi_pitch("D, A Timpani")
    ('D, A', 'Timpani')
    >>> _strip_multi_pitch("C, G, D Strings")
    ('C, G, D', 'Strings')
    >>> _strip_multi_pitch("Timpani")
    ('', 'Timpani')
    """
    m = _MULTI_PITCH_RE.match(text)
    if m:
        return m.group(1).strip(), text[m.end() :]
    return "", text


def _match_span(
    words: List[str], start: int, end: int
) -> Optional[Tuple[str, Family, str]]:
    """Exact-match a contiguous slice of words against the instrument table."""
    candidate = " ".join(words[start:end]).lower()
    for pattern, canonical, family, hs_code in _INSTRUMENT_TABLE:
        if candidate == pattern:
            return canonical, family, hs_code
    return None


def _tokenise(text: str) -> List[str]:
    """
    Split on whitespace, then strip leading/trailing punctuation from each
    piece, dropping empty results.  Preserves tokens like 'Bb', 'D', '1.',
    "cor", "anglais" as separate items.

    >>> _tokenise("1. Clarinet, Bb")
    ['1', 'Clarinet', 'Bb']
    >>> _tokenise("Bb Clarinet 1")
    ['Bb', 'Clarinet', '1']
    >>> _tokenise("Clarinet in Bb")
    ['Clarinet', 'in', 'Bb']
    """
    tokens = []
    for piece in text.split():
        cleaned = _TOKEN_STRIP_RE.sub("", piece)
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _parse_tokens(
    tokens: List[str],
) -> Tuple[Optional[Tuple[str, Family, str]], Optional[str], Optional[int]]:
    """
    Classify a flat token list into (instrument_match, key, index).

    Algorithm
    ---------
    1. Try every contiguous sub-span, longest first; take the first (longest)
       hit against the instrument table.  This naturally handles multi-word
       names ("Cor Anglais", "Bass Clarinet") and the Cor/Cor-Anglais
       ambiguity — the longer span wins.
    2. From the remaining tokens: a KEY_TOKEN becomes the transposition,
       a NUMBER_TOKEN becomes the index.  Filler words are silently dropped.
       Any unrecognised leftover is also silently ignored.
    """
    n = len(tokens)

    # 1. Greedy longest-span instrument search
    best_match: Optional[Tuple[str, Family, str]] = None
    best_span: Tuple[int, int] = (0, 0)
    best_len = 0

    for start in range(n):
        for end in range(n, start, -1):
            if (end - start) <= best_len:
                break  # inner loop descends; no longer span possible
            m = _match_span(tokens, start, end)
            if m:
                best_match = m
                best_span = (start, end)
                best_len = end - start
                break  # found longest span starting at `start`

    instrument_indices = (
        set(range(best_span[0], best_span[1])) if best_match else set()
    )

    # 2. Classify residual tokens
    key: Optional[str] = None
    index: Optional[int] = None

    for i, tok in enumerate(tokens):
        if i in instrument_indices:
            continue
        if _KEY_TOKEN_RE.match(tok):
            key = _normalise_key(tok)
        elif m_num := _NUMBER_TOKEN_RE.match(tok):
            index = int(m_num.group(1))
        elif tok.lower() in _FILLER:
            pass  # silently discard
        # anything else (unknown qualifier) is also silently discarded

    return best_match, key, index


# ---------------------------------------------------------------------------

# InstrumentRegistry


class InstrumentRegistry:
    """
    Central registry for parsing, classifying and grouping instruments.

    Methods
    -------
    parse(raw)          : parse a single instrument string → Instrument
    parse_roster(text)  : parse a comma-separated roster string → List[Instrument]
    group_by_family()   : group last parsed roster by Family
    group_by_canonical(): group last parsed roster by canonical name
    summary()           : print a formatted summary of the last parsed roster
    """

    def __init__(self) -> None:
        self._last_roster: List[Instrument] = []

    def parse(self, raw: str) -> Instrument:
        """
        Parse a single instrument string and return an Instrument dataclass.

        Handles tokens in any order, e.g. all of the following are equivalent:
          "Bb Clarinet 1" /  "Clarinet in Bb 1" /  "1. Clarinet, Bb"

        Pre-passes (order-sensitive by nature, applied before tokenisation):
          1. Parenthetical notes  e.g. "(basso)"
          2. 'solo' keyword
          3. Comma-joined multi-pitch specs  e.g. "D, A Timpani"

        The remaining text is then split into tokens and classified in a
        single bag-of-tokens pass (_parse_tokens).

        >>> reg = InstrumentRegistry()
        >>> reg.parse("Bb Clarinet 1").canonical
        'Clarinet'
        >>> reg.parse("Clarinet in Bb 1").transposition
        'Bb'
        >>> reg.parse("1. Clarinet, Bb").index
        1
        >>> reg.parse("Horn in F").family.value
        'Brass'
        >>> reg.parse("Cor anglais").canonical
        'Cor anglais'
        >>> reg.parse("Soprano solo").is_solo
        True
        """
        text = raw.strip()

        # 1. Extract parenthetical notes e.g. "(basso)"
        paren_notes = ""
        paren_matches = _PAREN_RE.findall(text)
        if paren_matches:
            paren_notes = ", ".join(paren_matches)
            text = _PAREN_RE.sub("", text).strip()

        # 2. Detect and remove 'solo'
        is_solo = bool(re.search(r"\bsolo\b", text, re.IGNORECASE))
        text = re.sub(r"\bsolo\b", "", text, flags=re.IGNORECASE).strip()

        # 3. Multi-pitch prefix e.g. "D, A Timpani" – commas make this
        #    un-tokenisable in the normal way, so handle it as a pre-pass.
        pitch_spec, text = _strip_multi_pitch(text)
        if pitch_spec and not paren_notes:
            paren_notes = pitch_spec

        # 4. Bag-of-tokens: instrument span + key + index in any order
        tokens = _tokenise(text)
        inst_match, transposition, index = _parse_tokens(tokens)

        if inst_match:
            canonical, family, hs_code = inst_match
        else:
            canonical = text.title() or raw.strip().title()
            family = Family.UNKNOWN
            hs_code = "4"

        hs_class = HS_CLASSES.get(hs_code, HS_CLASSES["4"])

        # 7. Build display name
        parts = []
        if transposition:
            parts.append(transposition)
        parts.append(canonical)
        if paren_notes:
            parts.append(f"({paren_notes})")
        if index is not None:
            parts.append(str(index))
        if is_solo:
            parts.append("solo")
        display = " ".join(parts)

        return Instrument(
            raw=raw.strip(),
            canonical=canonical,
            display=display,
            transposition=transposition,
            index=index,
            family=family,
            hs_class=hs_class,
            is_solo=is_solo,
            notes=paren_notes,
        )

    def parse_roster(self, text: str) -> List[Instrument]:
        """
        Parse a comma-separated roster string.

        Handles CSV-style quoting: items enclosed in double-quotes that contain
        commas are treated as a single token, e.g. ``"D, A Timpani"``.

        Parameters
        ----------
        text : str
            e.g. ``"Flute 1,Flute 2,Oboe 1,Bb Clarinet 1,\\"D, A Timpani\\""``

        Returns
        -------
        List[Instrument]  (also stored as self._last_roster)

        >>> reg = InstrumentRegistry()
        >>> roster = reg.parse_roster('Flute 1,Bb Clarinet 2,Violin 1')
        >>> [i.canonical for i in roster]
        ['Flute', 'Clarinet', 'Violin']
        >>> reg.parse_roster('"D, A Timpani"')[0].notes
        'D, A'
        """
        import csv
        import io

        reader = csv.reader(io.StringIO(text))
        tokens = [t.strip() for row in reader for t in row if t.strip()]
        roster = [self.parse(t) for t in tokens]
        self._last_roster = roster
        return roster

    def group_by_family(
        self, roster: Optional[List[Instrument]] = None
    ) -> Dict[Family, List[Instrument]]:
        """Return a dict mapping Family → list of Instruments."""
        src = roster if roster is not None else self._last_roster
        result: Dict[Family, List[Instrument]] = {f: [] for f in Family}
        for inst in src:
            result[inst.family].append(inst)
        return {k: v for k, v in result.items() if v}

    def group_by_canonical(
        self, roster: Optional[List[Instrument]] = None
    ) -> Dict[str, InstrumentGroup]:
        """Return a dict mapping canonical name → InstrumentGroup."""
        src = roster if roster is not None else self._last_roster
        result: Dict[str, InstrumentGroup] = {}
        for inst in src:
            if inst.canonical not in result:
                result[inst.canonical] = InstrumentGroup(inst.canonical)
            result[inst.canonical].members.append(inst)
        return result

    def group_by_hs_top(
        self, roster: Optional[List[Instrument]] = None
    ) -> Dict[str, List[Instrument]]:
        """Group by top-level HS digit (1=Idio, 2=Membrano, 3=Chordo, 4=Aero, 6=Voice)."""
        _labels = {
            "1": "Idiophones",
            "2": "Membranophones",
            "3": "Chordophones",
            "4": "Aerophones",
            "5": "Electrophones",
            "6": "Voice",
        }
        src = roster if roster is not None else self._last_roster
        result: Dict[str, List[Instrument]] = {}
        for inst in src:
            top = inst.hs_class.top_level()
            label = _labels.get(top, f"HS-{top}")
            result.setdefault(label, []).append(inst)
        return result

    def summary(self, roster: Optional[List[Instrument]] = None) -> None:
        """Print a formatted summary of a roster grouped by family."""
        src = roster if roster is not None else self._last_roster
        if not src:
            print("(empty roster)")
            return

        by_family = self.group_by_family(src)
        family_order = [
            Family.WOODWIND,
            Family.BRASS,
            Family.PERCUSSION,
            Family.STRINGS,
            Family.VOICE,
            Family.KEYBOARD,
            Family.UNKNOWN,
        ]

        print(f"\n{'=' * 72}")
        print(f" ORCHESTRAL ROSTER  ({len(src)} parts)")
        print(f"{'=' * 72}")
        for fam in family_order:
            instruments = by_family.get(fam, [])
            if not instruments:
                continue
            print(f"\n  ── {fam.value.upper()} ──")
            for inst in instruments:
                solo_tag = " ★ SOLO" if inst.is_solo else ""
                trans = f"({inst.transposition}) " if inst.transposition else ""
                idx_tag = f"#{inst.index}" if inst.index else " "
                notes = f" [{inst.notes}]" if inst.notes else ""
                print(
                    f"{idx_tag:<3} {trans}{inst.canonical:<22}"
                    f" HS {inst.hs_class.code:<7}"
                    f" {inst.hs_class.name}{solo_tag}{notes}"
                )
        print(f"\n{'=' * 72}\n")

    def hs_tree(self, roster: Optional[List[Instrument]] = None) -> None:
        """Print a Hornbostel-Sachs tree view of the roster."""
        src = roster if roster is not None else self._last_roster
        by_hs = self.group_by_hs_top(src)
        print(f"\n{'=' * 72}")
        print(" HORNBOSTEL-SACHS CLASSIFICATION TREE")
        print(f"{'=' * 72}")
        for label, instruments in by_hs.items():
            print(f"\n  [{label}]")
            # sub-group by hs_code
            by_code: Dict[str, List[Instrument]] = {}
            for i in instruments:
                by_code.setdefault(i.hs_class.code, []).append(i)
            for code in sorted(by_code):
                hs = HS_CLASSES.get(code)
                hs_name = hs.name if hs else code
                parts = by_code[code]
                names = ", ".join(p.display for p in parts)
                print(f"{code:<7} {hs_name:<35} → {names}")
        print(f"\n{'=' * 72}\n")


# ---------------------------------------------------------------------------

# Module-level convenience


_default_registry = InstrumentRegistry()


def parse_roster(text: str) -> List[Instrument]:
    """
    Module-level shortcut: parse a comma-separated roster string.

    Parameters
    ----------
    text : str
        Comma-separated list of instrument names.

    Returns
    -------
    List[Instrument]
    """
    return _default_registry.parse_roster(text)
