"""
This module
(amads.harmony.hierarchy.rules)
is part of
amads.harmony.hierarchy.
See top-level notes at
(amads.harmony.hierarchy.core)

Here is the rule table for rules (1)-(28) of Rohrmeier (2011).

Each rule is a small object exposing `expansions(label, key) -> list[RHS]`,
where an RHS is a list of `ChildSpec`s (kind, label, key, rule_note).
This is the generative direction (used by generator.py).
The same table serves re-use in a chart parser.
For all rules (except 6, 7, 28)
membership-checking a candidate span split amounts to
"does the split match one of `expansions`".
The variable-split rules (6 and 7) are where a CYK-style parser would try every split point of a span.

Note: some rules NOT implemented here (documented, not coded).
The paper's own admission (section 5/6) that pure sequential/schema patterns
(Monte sequences, Waldstein-style parallelism)
need extra machinery beyond the grammar;
Rule 28 (surface repetition) is implemented but trivial.
"""

from dataclasses import dataclass

from amads.harmony.hierarchy.core import Key, function_to_chord, psi


@dataclass(frozen=True)
class ChildSpec:
    kind: str  # 'region' | 'function' | 'scaledegree' | 'surface'
    label: str
    key: Key
    rule: str = (
        ""  # which rule licensed *this* child, if different from parent's rule id
    )
    degree_choice: int = 0


@dataclass(frozen=True)
class RHS:
    rule_id: str
    children: tuple[ChildSpec, ...]
    note: str = ""


# ---------------------------------------------------------------------------

# Phrase level: rules (1)-(3)


def phrase_expansions(key: Key) -> list[RHS]:
    """Rule 2: P -> TR. (Rule 3's single-key-seed variant is equivalent and
    not separately modeled.) A phrase ending on the dominant (a "half
    cadence") is NOT a distinct phrase-level rule -- it's an ordinary TR
    that happens to apply the functional rule (6) (TR -> TR DR) near its
    top; see generator.py's `force_half_cadence` for how the generator
    biases toward that shape, and parser.py's `parse`, which finds it
    automatically since rule 6 is tried at every span."""
    return [RHS("2", (ChildSpec("region", "TR", key, "2"),))]


# ---------------------------------------------------------------------------

# Functional level: expansion rules (4)-(10)


def region_expansions(region: str, key: Key) -> list[RHS]:
    """All rules whose LHS is `region` (a region symbol TR/DR/SR)."""
    out: list[RHS] = []
    if region == "TR":
        out.append(
            RHS(
                "4",
                (
                    ChildSpec("region", "DR", key),
                    ChildSpec("function", "t", key),
                ),
            )
        )
        out.append(
            RHS(
                "6",
                (
                    ChildSpec("region", "TR", key),
                    ChildSpec("region", "DR", key),
                ),
            )
        )
        out.append(RHS("8", (ChildSpec("function", "t", key),)))
    elif region == "DR":
        out.append(
            RHS(
                "5",
                (
                    ChildSpec("region", "SR", key),
                    ChildSpec("function", "d", key),
                ),
            )
        )
        out.append(RHS("9", (ChildSpec("function", "d", key),)))
    elif region == "SR":
        out.append(RHS("10", (ChildSpec("function", "s", key),)))
    else:
        raise ValueError(region)
    # rule 7: XR -> XR XR (functional prolongation), any region
    out.append(
        RHS(
            "7",
            (
                ChildSpec("region", region, key),
                ChildSpec("region", region, key),
            ),
        )
    )
    return out


# ---------------------------------------------------------------------------

# Functional level: substitution rules (11)-(14)


_SUBSTITUTIONS = {
    "t": [("tp", "11"), ("tcp", "12")],
    "s": [("sp", "13")],
    "d": [("dp", "14")],
}


def substitution_expansions(function: str, key: Key) -> list[RHS]:
    out = []
    for target, rule_id in _SUBSTITUTIONS.get(function, []):
        if key.mode in FUNCTION_REALIZATION_MODES(target):
            out.append(RHS(rule_id, (ChildSpec("function", target, key),)))
    return out


def FUNCTION_REALIZATION_MODES(function: str) -> set:
    from .core import FUNCTION_REALIZATION

    return set(FUNCTION_REALIZATION.get(function, {}).keys())


# ---------------------------------------------------------------------------

# Functional level: modulation rules (15)-(16)


def modulation_expansions(function: str, key: Key) -> list[RHS]:
    """Rule 15: X_key=y -> TR_key=psi(X,y), for X != t. Re-enters the
    recursive region domain at a new local key."""
    if function == "t":
        return []
    new_key = psi(function, key)
    if new_key is None:
        return []
    return [RHS("15", (ChildSpec("region", "TR", new_key),))]


def mode_change_expansions(function: str, key: Key) -> list[RHS]:
    """Rule 16: change of mode without change of function (modal borrowing)."""
    other_mode = "minor" if key.mode == "major" else "major"
    other_key = Key(key.tonic_pc, other_mode)
    if other_mode not in FUNCTION_REALIZATION_MODES(function):
        return []
    return [RHS("16", (ChildSpec("function", function, other_key),))]


# ---------------------------------------------------------------------------

# Function -> scale degree / surface chord, rules (20)-(27), plus rule 28


def scaledegree_terminal(
    function: str, key: Key, degree_choice: int = 0
) -> RHS:
    chord = function_to_chord(function, key, degree_choice=degree_choice)
    numeral = chord.roman_numeral(key.as_chord_key_str()) or "?"
    rule_by_function = {
        "t": "20",
        "s": "22",
        "d": "23",
        "tp": "24",
        "dp": "25",
        "sp": "26",
        "tcp": "27",
    }
    return RHS(
        rule_by_function[function],
        (ChildSpec("surface", numeral, key, degree_choice=degree_choice),),
        note=chord.label,
    )


def plagal_terminal(key: Key) -> RHS:
    """Rule 21: t -> I IV I (plagal elaboration of the tonic)."""
    return RHS(
        "21",
        (
            ChildSpec("surface", "I", key, degree_choice=0),
            ChildSpec("surface", "IV", key, degree_choice=0),
            ChildSpec("surface", "I", key, degree_choice=0),
        ),
    )


def repetition_expansion(surface_label: str, key: Key) -> RHS:
    """Rule 28: X -> X+ (surface repetition)."""
    return RHS("28", (ChildSpec("surface", surface_label, key),) * 2)
