"""
test_instruments.py
===================
Pytest suite for instruments.py.

Structure
---------
Unit tests for private helpers  (_normalise_key, _strip_multi_pitch,
                                  _tokenise, _parse_tokens)
Integration tests via parse()   (ordering variants, flags, special cases,
                                  unknown instruments)
parse_roster tests              (CSV quoting, multi-pitch Timpani)
Grouping tests                  (group_by_family, group_by_canonical,
                                  group_by_hs_top)
Smoke tests                     (summary, hs_tree — don't crash, hit keys)
"""

import io
from contextlib import redirect_stdout

import pytest

from amads.instruments.instrument_classification import (  # Instrument,
    HS_CLASSES,
    Family,
    InstrumentGroup,
    InstrumentRegistry,
    _normalise_key,
    _parse_tokens,
    _strip_multi_pitch,
    _tokenise,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def reg() -> InstrumentRegistry:
    return InstrumentRegistry()


@pytest.fixture
def full_roster(reg):
    return reg.parse_roster(
        "Flute 1,Flute 2,Oboe 1,Bb Clarinet 1,Bb Clarinet 2,"
        "Bassoon 1,Horn in F 1,Horn in F 2,Trumpet in Bb 1,"
        "Trombone 1,Tuba,Timpani,Violin 1,Violin 2,"
        "Viola,Violoncello,Contrabass,Soprano solo"
    )


# ---------------------------------------------------------------------------
# _normalise_key
# ---------------------------------------------------------------------------


class TestNormaliseKey:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("bb", "Bb"),
            ("BB", "Bb"),
            ("Bb", "Bb"),
            ("b-flat", "Bb"),
            ("B-flat", "Bb"),
            ("bflat", "Bb"),
            ("eb", "Eb"),
            ("EB", "Eb"),
            ("Eb", "Eb"),
            ("e-flat", "Eb"),
            ("eflat", "Eb"),
            ("f", "F"),
            ("F", "F"),
            ("g", "G"),
            ("a", "A"),
            ("d", "D"),
            ("c", "C"),
        ],
    )
    def test_normalise(self, raw, expected):
        assert _normalise_key(raw) == expected


# ---------------------------------------------------------------------------
# _strip_multi_pitch
# ---------------------------------------------------------------------------


class TestStripMultiPitch:
    def test_two_pitches(self):
        spec, rest = _strip_multi_pitch("D, A Timpani")
        assert spec == "D, A"
        assert rest == "Timpani"

    def test_three_pitches(self):
        spec, rest = _strip_multi_pitch("C, G, D Timpani")
        assert spec == "C, G, D"
        assert rest == "Timpani"

    def test_no_match_returns_empty_spec(self):
        spec, rest = _strip_multi_pitch("Timpani")
        assert spec == ""
        assert rest == "Timpani"

    def test_single_letter_alone_not_matched(self):
        # A single pitch letter without a comma is not a multi-pitch spec
        spec, rest = _strip_multi_pitch("D Trumpet")
        assert spec == ""
        assert rest == "D Trumpet"

    def test_sharps_and_flats(self):
        spec, rest = _strip_multi_pitch("D#, Ab Timpani")
        assert spec == "D#, Ab"
        assert rest == "Timpani"


# ---------------------------------------------------------------------------
# _tokenise
# ---------------------------------------------------------------------------


class TestTokenise:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Bb Clarinet 1", ["Bb", "Clarinet", "1"]),
            ("1. Clarinet, Bb", ["1", "Clarinet", "Bb"]),
            ("Clarinet in Bb", ["Clarinet", "in", "Bb"]),
            ("Cor anglais", ["Cor", "anglais"]),
            # Ordinal suffixes survive intact for _NUMBER_TOKEN_RE to handle
            ("2nd Oboe", ["2nd", "Oboe"]),
            # Extra whitespace is collapsed
            ("  Flute  2  ", ["Flute", "2"]),
        ],
    )
    def test_tokenise(self, text, expected):
        assert _tokenise(text) == expected


# ---------------------------------------------------------------------------
# _parse_tokens
# ---------------------------------------------------------------------------


class TestParseTokens:
    """Tests for the core bag-of-tokens classifier."""

    def _inst(self, tokens):
        """Helper: return (canonical, family, hs_code) or None from token list."""
        match, key, idx = _parse_tokens(tokens)
        return match, key, idx

    def test_simple_instrument(self):
        match, key, idx = _parse_tokens(["Clarinet"])
        assert match is not None
        assert match[0] == "Clarinet"
        assert key is None
        assert idx is None

    def test_key_before_instrument(self):
        match, key, idx = _parse_tokens(["Bb", "Clarinet"])
        assert match[0] == "Clarinet"
        assert key == "Bb"

    def test_key_after_instrument(self):
        match, key, idx = _parse_tokens(["Clarinet", "in", "Bb"])
        assert match[0] == "Clarinet"
        assert key == "Bb"

    def test_index_before_instrument(self):
        match, key, idx = _parse_tokens(["1", "Clarinet"])
        assert match[0] == "Clarinet"
        assert idx == 1

    def test_all_three_any_order(self):
        for tokens in [
            ["Bb", "Clarinet", "1"],
            ["Clarinet", "Bb", "1"],
            ["1", "Clarinet", "Bb"],
            ["Clarinet", "in", "Bb", "1"],
            ["1", "in", "Bb", "Clarinet"],
        ]:
            match, key, idx = _parse_tokens(tokens)
            assert match[0] == "Clarinet", f"failed for {tokens}"
            assert key == "Bb", f"failed for {tokens}"
            assert idx == 1, f"failed for {tokens}"

    def test_longest_span_wins_cor_anglais(self):
        # "cor anglais" (2 tokens) must beat "cor" → Horn (1 token)
        match, _, _ = _parse_tokens(["Cor", "anglais"])
        assert match[0] == "Cor anglais"
        assert match[1] == Family.WOODWIND

    def test_longest_span_wins_bass_clarinet(self):
        match, _, _ = _parse_tokens(["Bass", "Clarinet"])
        assert match[0] == "Bass Clarinet"

    def test_longest_span_wins_bass_trombone(self):
        match, _, _ = _parse_tokens(["Bass", "Trombone"])
        assert match[0] == "Bass Trombone"
        assert match[1] == Family.BRASS

    def test_ordinal_number(self):
        match, key, idx = _parse_tokens(["2nd", "Oboe"])
        assert match[0] == "Oboe"
        assert idx == 2

    def test_filler_words_ignored(self):
        for filler in ["in", "for", "di", "the", "a", "an"]:
            match, key, idx = _parse_tokens([filler, "Clarinet", "Bb"])
            assert match[0] == "Clarinet"
            assert key == "Bb"

    def test_unknown_returns_none(self):
        match, key, idx = _parse_tokens(["Theremin"])
        assert match is None

    def test_empty_returns_none(self):
        match, key, idx = _parse_tokens([])
        assert match is None


# ---------------------------------------------------------------------------
# InstrumentRegistry.parse — ordering variants
# ---------------------------------------------------------------------------

CLARINET_BB_1_EQUIVALENTS = [
    "Bb Clarinet 1",
    "Clarinet in Bb 1",
    "Clarinet 1 in Bb",
    "1. Clarinet, Bb",
    "1 Bb Clarinet",
    "Clarinet Bb 1",
]


class TestParseOrderingVariants:

    @pytest.mark.parametrize("raw", CLARINET_BB_1_EQUIVALENTS)
    def test_clarinet_bb_1_canonical(self, reg, raw):
        assert reg.parse(raw).canonical == "Clarinet"

    @pytest.mark.parametrize("raw", CLARINET_BB_1_EQUIVALENTS)
    def test_clarinet_bb_1_transposition(self, reg, raw):
        assert reg.parse(raw).transposition == "Bb"

    @pytest.mark.parametrize("raw", CLARINET_BB_1_EQUIVALENTS)
    def test_clarinet_bb_1_index(self, reg, raw):
        assert reg.parse(raw).index == 1

    @pytest.mark.parametrize(
        "raw,expected_key",
        [
            ("Horn in F", "F"),
            ("F Horn", "F"),
            ("Trumpet in D", "D"),
            ("D Trumpet", "D"),
            ("Clarinet in A", "A"),
            ("Flute in G", "G"),
            # "Eb Clarinet" is a named table entry → canonical "Eb Clarinet",
            # no separate transposition field; use "Clarinet in Eb" for that.
            ("Clarinet in Eb", "Eb"),
        ],
    )
    def test_key_extraction(self, reg, raw, expected_key):
        assert reg.parse(raw).transposition == expected_key


# ---------------------------------------------------------------------------
# InstrumentRegistry.parse — field correctness
# ---------------------------------------------------------------------------


class TestParseFields:

    @pytest.mark.parametrize(
        "raw,canonical,family,hs_code",
        [
            # Woodwind
            ("Piccolo", "Piccolo", Family.WOODWIND, "421.1"),
            ("Flute", "Flute", Family.WOODWIND, "421.1"),
            ("Oboe", "Oboe", Family.WOODWIND, "4222"),
            ("Cor anglais", "Cor anglais", Family.WOODWIND, "4222"),
            ("English Horn", "English Horn", Family.WOODWIND, "4222"),
            ("Contrabassoon", "Contrabassoon", Family.WOODWIND, "4222"),
            ("Bassoon", "Bassoon", Family.WOODWIND, "4222"),
            ("Bass Clarinet", "Bass Clarinet", Family.WOODWIND, "4221"),
            ("Clarinet", "Clarinet", Family.WOODWIND, "4221"),
            ("Alto Saxophone", "Alto Sax", Family.WOODWIND, "4221"),
            ("Tenor Saxophone", "Tenor Sax", Family.WOODWIND, "4221"),
            ("Baritone Saxophone", "Baritone Sax", Family.WOODWIND, "4221"),
            # Brass
            ("Horn", "Horn", Family.BRASS, "423.1"),
            ("Trumpet", "Trumpet", Family.BRASS, "423.2"),
            ("Cornet", "Cornet", Family.BRASS, "423.2"),
            ("Flugelhorn", "Flugelhorn", Family.BRASS, "423.1"),
            ("Alto Trombone", "Alto Trombone", Family.BRASS, "423.3"),
            ("Bass Trombone", "Bass Trombone", Family.BRASS, "423.3"),
            ("Trombone", "Trombone", Family.BRASS, "423.3"),
            ("Tuba", "Tuba", Family.BRASS, "423.4"),
            ("Euphonium", "Euphonium", Family.BRASS, "423.4"),
            ("Baritone Horn", "Baritone Horn", Family.BRASS, "423.4"),
            # Percussion
            ("Timpani", "Timpani", Family.PERCUSSION, "211.1"),
            ("Bass Drum", "Bass Drum", Family.PERCUSSION, "211.2"),
            ("Snare Drum", "Snare Drum", Family.PERCUSSION, "21"),
            ("Xylophone", "Xylophone", Family.PERCUSSION, "1"),
            ("Vibraphone", "Vibraphone", Family.PERCUSSION, "1"),
            ("Glockenspiel", "Glockenspiel", Family.PERCUSSION, "1"),
            # Strings
            ("Violin", "Violin", Family.STRINGS, "321.3"),
            ("Viola", "Viola", Family.STRINGS, "321.3"),
            ("Violoncello", "Violoncello", Family.STRINGS, "321.3"),
            ("Cello", "Violoncello", Family.STRINGS, "321.3"),
            ("Contrabass", "Contrabass", Family.STRINGS, "321.3"),
            ("Double Bass", "Contrabass", Family.STRINGS, "321.3"),
            ("Harp", "Harp", Family.STRINGS, "322"),
            # Voice
            ("Soprano", "Soprano", Family.VOICE, "6.1"),
            ("Mezzo-soprano", "Mezzo-soprano", Family.VOICE, "6.1"),
            ("Alto", "Alto", Family.VOICE, "6.2"),
            ("Tenor", "Tenor", Family.VOICE, "6.3"),
            ("Baritone", "Baritone", Family.VOICE, "6.4"),
            ("Bass", "Bass", Family.VOICE, "6.4"),
            # Keyboard
            ("Piano", "Piano", Family.KEYBOARD, "314"),
            ("Harpsichord", "Harpsichord", Family.KEYBOARD, "314"),
            ("Celesta", "Celesta", Family.KEYBOARD, "314"),
            ("Organ", "Organ", Family.KEYBOARD, "4"),
        ],
    )
    def test_classification(self, reg, raw, canonical, family, hs_code):
        inst = reg.parse(raw)
        assert inst.canonical == canonical
        assert inst.family == family
        assert inst.hs_class == HS_CLASSES[hs_code]

    def test_index_extracted(self, reg):
        assert reg.parse("Violin 2").index == 2

    def test_ordinal_index(self, reg):
        assert reg.parse("2nd Oboe").index == 2

    def test_no_index(self, reg):
        assert reg.parse("Flute").index is None

    def test_solo_flag_set(self, reg):
        assert reg.parse("Soprano solo").is_solo is True

    def test_solo_flag_not_set(self, reg):
        assert reg.parse("Soprano").is_solo is False

    def test_solo_case_insensitive(self, reg):
        assert reg.parse("Soprano SOLO").is_solo is True

    def test_raw_preserved(self, reg):
        assert reg.parse("  Bb Clarinet 1  ").raw == "Bb Clarinet 1"

    def test_display_contains_canonical(self, reg):
        assert "Clarinet" in reg.parse("Bb Clarinet 1").display

    def test_display_contains_key(self, reg):
        assert "Bb" in reg.parse("Bb Clarinet 1").display

    def test_display_contains_index(self, reg):
        assert "1" in reg.parse("Bb Clarinet 1").display


# ---------------------------------------------------------------------------
# InstrumentRegistry.parse — special / edge cases
# ---------------------------------------------------------------------------


class TestParseSpecialCases:

    def test_eb_clarinet_named_entry(self, reg):
        # "Eb Clarinet" is in the table as a unit → canonical "Eb Clarinet",
        # no separate transposition.  Use "Clarinet in Eb" to get transposition="Eb".
        inst = reg.parse("Eb Clarinet")
        assert inst.canonical == "Eb Clarinet"
        assert inst.transposition is None
        inst2 = reg.parse("Clarinet in Eb")
        assert inst2.canonical == "Clarinet"
        assert inst2.transposition == "Eb"

    def test_cor_anglais_not_horn(self, reg):
        inst = reg.parse("Cor anglais")
        assert inst.family == Family.WOODWIND
        assert inst.canonical == "Cor anglais"
        assert inst.hs_class.code == "4222"

    def test_cor_anglais_case_insensitive(self, reg):
        assert reg.parse("COR ANGLAIS").canonical == "Cor anglais"

    def test_bass_alone_is_voice(self, reg):
        inst = reg.parse("Bass")
        assert inst.family == Family.VOICE

    def test_bass_clarinet_is_woodwind(self, reg):
        inst = reg.parse("Bass Clarinet")
        assert inst.family == Family.WOODWIND
        assert inst.canonical == "Bass Clarinet"

    def test_bass_drum_is_percussion(self, reg):
        inst = reg.parse("Bass Drum")
        assert inst.family == Family.PERCUSSION
        assert inst.canonical == "Bass Drum"

    def test_bass_trombone_is_brass(self, reg):
        inst = reg.parse("Bass Trombone")
        assert inst.family == Family.BRASS
        assert inst.canonical == "Bass Trombone"

    def test_alto_alone_is_voice(self, reg):
        assert reg.parse("Alto").family == Family.VOICE

    def test_alto_saxophone_is_woodwind(self, reg):
        assert reg.parse("Alto Saxophone").canonical == "Alto Sax"

    def test_tenor_alone_is_voice(self, reg):
        assert reg.parse("Tenor").family == Family.VOICE

    def test_tenor_saxophone_is_woodwind(self, reg):
        assert reg.parse("Tenor Saxophone").canonical == "Tenor Sax"

    def test_parenthetical_notes_extracted(self, reg):
        inst = reg.parse("Bb (basso) Horn 3")
        assert "basso" in inst.notes
        assert inst.canonical == "Horn"
        assert inst.transposition == "Bb"
        assert inst.index == 3

    def test_parenthetical_not_in_canonical(self, reg):
        inst = reg.parse("Horn (natural) 2")
        assert "natural" not in inst.canonical

    def test_cello_maps_to_violoncello(self, reg):
        assert reg.parse("Cello").canonical == "Violoncello"

    def test_double_bass_maps_to_contrabass(self, reg):
        assert reg.parse("Double Bass").canonical == "Contrabass"

    def test_case_insensitive(self, reg):
        assert reg.parse("bb clarinet").canonical == "Clarinet"
        assert reg.parse("VIOLIN").canonical == "Violin"

    def test_unknown_instrument_family(self, reg):
        inst = reg.parse("Theremin")
        assert inst.family == Family.UNKNOWN

    def test_unknown_instrument_raw_preserved(self, reg):
        inst = reg.parse("Theremin")
        assert inst.raw == "Theremin"

    def test_whitespace_only_raw(self, reg):
        # Should not raise; falls through to unknown
        inst = reg.parse("   ")
        assert inst.family == Family.UNKNOWN


# ---------------------------------------------------------------------------
# parse_roster
# ---------------------------------------------------------------------------


class TestParseRoster:

    def test_basic_csv(self, reg):
        roster = reg.parse_roster("Flute 1,Flute 2,Oboe 1")
        assert len(roster) == 3
        assert roster[0].canonical == "Flute"
        assert roster[0].index == 1
        assert roster[2].canonical == "Oboe"

    def test_stores_last_roster(self, reg):
        reg.parse_roster("Flute 1,Oboe 1")
        assert len(reg._last_roster) == 2

    def test_multi_pitch_timpani_via_quoting(self, reg):
        roster = reg.parse_roster('"D, A Timpani"')
        assert len(roster) == 1
        inst = roster[0]
        assert inst.canonical == "Timpani"
        assert inst.notes == "D, A"
        # The pitch letters must not be mistaken for a transposition key
        assert inst.transposition is None

    def test_multi_pitch_in_full_roster(self, reg):
        roster = reg.parse_roster('Flute 1,Oboe 1,"D, A Timpani",Violin 1')
        assert roster[2].canonical == "Timpani"
        assert roster[2].notes == "D, A"

    def test_whitespace_stripped_from_items(self, reg):
        roster = reg.parse_roster("  Flute 1  ,  Oboe 1  ")
        assert roster[0].canonical == "Flute"
        assert roster[1].canonical == "Oboe"

    def test_empty_items_skipped(self, reg):
        roster = reg.parse_roster("Flute 1,,Oboe 1,")
        assert len(roster) == 2

    def test_returns_list(self, reg):
        assert isinstance(reg.parse_roster("Flute"), list)


# ---------------------------------------------------------------------------
# Grouping helpers
# ---------------------------------------------------------------------------


class TestGrouping:

    def test_group_by_family_keys(self, reg, full_roster):
        groups = reg.group_by_family(full_roster)
        assert Family.WOODWIND in groups
        assert Family.BRASS in groups
        assert Family.STRINGS in groups
        assert Family.PERCUSSION in groups
        assert Family.VOICE in groups

    def test_group_by_family_empty_families_excluded(self, reg, full_roster):
        groups = reg.group_by_family(full_roster)
        # No keyboard instruments in full_roster
        assert Family.KEYBOARD not in groups

    def test_group_by_family_correct_assignment(self, reg, full_roster):
        groups = reg.group_by_family(full_roster)
        woodwinds = [i.canonical for i in groups[Family.WOODWIND]]
        assert "Flute" in woodwinds
        assert "Clarinet" in woodwinds
        assert "Bassoon" in woodwinds

    def test_group_by_canonical_keys(self, reg, full_roster):
        groups = reg.group_by_canonical(full_roster)
        assert "Flute" in groups
        assert "Clarinet" in groups
        assert "Violin" in groups

    def test_group_by_canonical_counts(self, reg, full_roster):
        groups = reg.group_by_canonical(full_roster)
        assert len(groups["Flute"]) == 2  # Flute 1 and 2
        assert len(groups["Clarinet"]) == 2
        assert len(groups["Violin"]) == 2
        assert len(groups["Viola"]) == 1

    def test_group_by_canonical_returns_instrument_group(
        self, reg, full_roster
    ):
        groups = reg.group_by_canonical(full_roster)
        assert isinstance(groups["Flute"], InstrumentGroup)

    def test_group_by_hs_top_keys(self, reg, full_roster):
        groups = reg.group_by_hs_top(full_roster)
        assert "Aerophones" in groups
        assert "Chordophones" in groups
        assert "Membranophones" in groups

    def test_group_by_hs_top_voice(self, reg, full_roster):
        groups = reg.group_by_hs_top(full_roster)
        assert "Voice" in groups
        assert groups["Voice"][0].canonical == "Soprano"

    def test_group_uses_last_roster_when_no_arg(self, reg, full_roster):
        # full_roster fixture already called parse_roster, so _last_roster is set
        groups = reg.group_by_family()
        assert Family.WOODWIND in groups


# ---------------------------------------------------------------------------
# Smoke tests — summary() and hs_tree() must not raise and hit key strings
# ---------------------------------------------------------------------------


class TestSmokeOutput:

    def _capture(self, fn, *args, **kwargs):
        buf = io.StringIO()
        with redirect_stdout(buf):
            fn(*args, **kwargs)
        return buf.getvalue()

    def test_summary_runs(self, reg, full_roster):
        out = self._capture(reg.summary, full_roster)
        assert "WOODWIND" in out
        assert "BRASS" in out
        assert "STRINGS" in out
        assert "Clarinet" in out

    def test_summary_empty(self, reg):
        out = self._capture(reg.summary, [])
        assert "empty" in out.lower()

    def test_summary_marks_solo(self, reg):
        roster = reg.parse_roster("Soprano solo")
        out = self._capture(reg.summary, roster)
        assert "SOLO" in out

    def test_hs_tree_runs(self, reg, full_roster):
        out = self._capture(reg.hs_tree, full_roster)
        assert "HORNBOSTEL" in out
        assert "421.1" in out  # flutes
        assert "423" in out  # brass

    def test_summary_uses_last_roster(self, reg, full_roster):
        out = self._capture(reg.summary)  # no argument
        assert "Clarinet" in out


# ---------------------------------------------------------------------------
# Instrument dataclass — equality and hashing
# ---------------------------------------------------------------------------


class TestInstrumentEquality:

    def test_equal_same_canonical_and_index(self, reg):
        a = reg.parse("Bb Clarinet 1")
        b = reg.parse("Clarinet in Bb 1")
        assert a == b

    def test_not_equal_different_index(self, reg):
        a = reg.parse("Violin 1")
        b = reg.parse("Violin 2")
        assert a != b

    def test_not_equal_different_canonical(self, reg):
        assert reg.parse("Flute") != reg.parse("Oboe")

    def test_hashable(self, reg):
        a = reg.parse("Clarinet 1")
        b = reg.parse("Clarinet 1")
        assert len({a, b}) == 1  # same hash, collapse in set

    def test_different_in_set(self, reg):
        a = reg.parse("Clarinet 1")
        b = reg.parse("Clarinet 2")
        assert len({a, b}) == 2
