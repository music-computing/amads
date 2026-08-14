"""
Cross-check `parser._function_candidates`
(our reverse function-assignment table, rules 20-27)
against an independent implementation ... also by me ;) ... in
`music21.analysis.harmonicFunction`.

Scope of the comparison
------------------------
`music21.analysis.harmonicFunction` is a superset of Rohrmeier's function set:
it gives every one of T/S/D a Parallel and a Gegenklang variant
(18 labels total),
where Rohrmeier's rules (11)-(14) only define a Gegenklang for the tonic
(`tcp`; no `scp` or `dcp` in the paper).

As I note on music21, some of its 18 labels overlap
(e.g. `Tg` and `Dp` both resolve to scale degree iii in major).

This test compares at the level both systems agree is unambiguous:
the tonic/subdominant/dominant level
(music21's "HauptHarmonicFunction"; AMADS' `BASE_OF`)
that a given scale degree/quality combination realizes,
for every plain diatonic triad in major and minor.

Skipped automatically if music21 isn't installed.
"""

import pytest

music21 = pytest.importorskip("music21")

from music21 import key as m21key  # noqa: E402
from music21 import roman as m21roman  # noqa: E402
from music21.analysis import harmonicFunction as m21hf  # noqa: E402

from amads.harmony.hierarchy.core import Key  # noqa: E402
from amads.harmony.hierarchy.parser import (  # noqa: E402
    BASE_OF,
    _function_candidates,
)

_DEGREE_NUMERAL = ["I", "II", "III", "IV", "V", "VI", "VII"]

_M21_HAUPT_TO_BASE = {
    "T": "t",
    "t": "t",
    "S": "s",
    "s": "s",
    "D": "d",
    "d": "d",
}


def _numeral_for_quality(degree: int, quality: str) -> str:
    core = _DEGREE_NUMERAL[degree - 1]
    if quality == "major":
        return core
    if quality == "minor":
        return core.lower()
    if quality == "diminished":
        return core.lower() + "o"
    raise ValueError(quality)


_KNOWN_DIVERGENCES = {(3, "major")}


@pytest.mark.parametrize("mode", ["major", "minor"])
@pytest.mark.parametrize("degree", range(1, 8))
def test_base_function_agrees_with_music21(mode, degree):
    if (degree, mode) in _KNOWN_DIVERGENCES:
        pytest.skip("documented scope divergence, see _KNOWN_DIVERGENCES")

    key = Key(0, mode)  # C major / C minor
    quality = key.degree_triad_quality(degree)
    ours = set(BASE_OF[f] for f in _function_candidates(degree, quality, key))

    if not ours:
        pytest.skip(
            f"our table has no reading for degree {degree} ({mode}, {quality}) -- "
            f"nothing to compare (e.g. degree VII diminished isn't a plain-triad function)"
        )

    key_str = "C" if mode == "major" else "c"
    numeral = _numeral_for_quality(degree, quality)
    rn = m21roman.RomanNumeral(numeral, m21key.Key(key_str))
    fn = m21hf.romanToFunction(rn, onlyHauptHarmonicFunction=True)
    if fn is None:
        pytest.skip(
            f"music21 has no Haupt-function entry for {numeral!r} in {key_str!r}"
        )
    theirs = _M21_HAUPT_TO_BASE[str(fn)]

    assert (
        theirs in ours
    ), f"degree {degree} in C {mode} ({quality} triad): we say {ours}, music21 says {{{theirs!r}}}"
