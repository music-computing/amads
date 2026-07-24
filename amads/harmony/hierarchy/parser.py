"""
This module
(amads.harmony.hierarchy.parser)
is part of
amads.harmony.hierarchy.
See top-level notes at
(amads.harmony.hierarchy.core)

Scope and rationale
-------------------
The generator (generator.py) samples top-down, so recursion and key-threading are trivial to control.
Parsing is the inverse problem: given a fixed sequence of chords,
find derivation tree(s) consistent with the rule table in rules.py.
Rohrmeier's grammar is not a plain CFG.
Notable divergences from CFG:
- rules carry a `key` feature (section 3) and
- one rule (15, modulation) can license a chord being derived twice from two disjoint branches (pivot chord, Figure 3).

While this implementation stays as close to the source as practical,
here we need to make a few deliberate (and explicit) simplifications as follows:

1. **Key is given, not searched.**
    In this parser mode, we build the tree from an harmoninc analysis.
    That analysis includes chord and key information for each item,
    and we deduce a single global key for the whole input (`key` argument to `parse`).
    This sidesteps the 24-key search a fully general parser would need.
2. **Input is Roman numerals, not raw audio/pitch chords.**
    Consistent with wider AMADS design,
    the functionality here focuses on symbolic data (where there's a distinction),
    and on the most specific representation within that.
    Each token is parsed with the same `Chord.from_roman` used by `amads.core.chord`,
    with the small extension to `/target` suffix for secondary dominants (rule 17/19, e.g. "V7/ii").
    This means the surface-to-scale-degree ambiguity is already resolved by the analyst;
    the parser's job is purely to find the tree from those chord identities.
3. **"Best" parse = fewest total tree nodes.**
    The paper does not specify a preference/scoring rule for genuinely ambiguous input
    (e.g. rule 7's free split point, or a VI chord in a minor key that could be read as `sp` or `tcp`).
    We break ties by minimising tree size.
    In practice, this means a preference for
    direct/base derivation (rules 8-10)
    over further prolongation (rule 7)
    when both are available.
    Again, this is a pragmatic design choice for the implementation here, not based on a claim from the paper.
4. **Rule 28 (surface repetition)** and **rule 21 (t -> I IV I, plagal).**
    These are seen as explicit surface patterns during a preprocessing pass
    (see `_build_constituents`),
    the same way rule 17 pairs a secondary dominant with its target.
5. **Modulation.**
    The `parse()` function takes one given key for the whole input (doesn't search for key changes).
    Modulation (rule 15/16) lives in a separate entry point, `parse_with_modulation().
    Here, the caller supplies one key per token (as in most annotation formats including DCML and RNTXT).
6. **Pivot chord.**
    We exclude (for now) pivot chords (see teh double derivation of Figure 3).
    This is the one item not modelled anywhere in this module.
    While some formats permit the encoding thereof, all have the option to reduce to a single default label
    and this simplifies the implementation and prospective use cases considerably.
7. **Rule 18 (diatonic fifth-sequences).**
    This is also not currently modelled here and would be needed for the "Autumn Leaves" example (Figure 4).
"""

from dataclasses import dataclass
from typing import Optional

from amads.core.chord import MAJOR_TRIADS, MINOR_TRIADS, ROMAN_TO_DEGREE, Chord
from amads.core.pitch import Pitch
from amads.harmony.hierarchy.core import FUNCTION_REALIZATION, Key, psi
from amads.harmony.hierarchy.tree import Node

RULE_TERMINAL = {
    "t": "20",
    "s": "22",
    "d": "23",
    "tp": "24",
    "dp": "25",
    "sp": "26",
    "tcp": "27",
}
SUBSTITUTION_RULE = {"tp": "11", "tcp": "12", "sp": "13", "dp": "14"}
BASE_OF = {
    "t": "t",
    "s": "s",
    "d": "d",
    "tp": "t",
    "tcp": "t",
    "sp": "s",
    "dp": "d",
}


# Map extended qualities to triad. TODO debatable choice e.g., wrt ii65
_TRIAD_COMPONENT = {
    "major": "major",
    "major6": "major",
    "major7": "major",
    "major9": "major",
    "minor": "minor",
    "minor6": "minor",
    "minor7": "minor",
    "minor9": "minor",
    "dominant7": "major",
    "dominant9": "major",
    "diminished": "diminished",
    "diminished7": "diminished",
    "half-dim7": "diminished",
    "augmented": "augmented",
}


class ParseError(Exception):
    pass


@dataclass
class Terminal:
    raw: str
    chord: Chord
    target_degree: Optional[
        int
    ]  # set only for secondary-dominant tokens ("V7/ii")


@dataclass
class Constituent:
    degree: int  # scale degree this constituent ultimately realises
    quality: str  # quality of the chord that determines function (the resolved chord)
    node: Node  # what to attach as the function-node's child (surface, or a scale degree wrapper)


# ---------------------------------------------------------------------------

# Tokenizing


def parse_token(token: str, key: Key) -> Terminal:
    token = token.strip()
    if "/" in token:
        main, target = token.split("/", 1)
        target_core = "".join(ch for ch in target if ch.isalpha()).upper()
        if target_core not in ROMAN_TO_DEGREE:
            raise ParseError(
                f"Unrecognised secondary-dominant target {target!r} in token {token!r}"
            )
        target_degree = ROMAN_TO_DEGREE[target_core]
        target_root_pc = key.degree_pc(target_degree)

        # Rule (19): D(X) in {V/X, VII/X}, i.e. a fifth above X's root.
        main_core = "".join(ch for ch in main if ch.isalpha()).upper()
        seventh = "7" in main or "ø" in main or "0" in main
        if main_core == "V":
            root_pc = (target_root_pc + 7) % 12
            quality = "dominant7" if seventh else "major"
        elif main_core in ("VII", "VIIO", "VII0"):
            root_pc = (target_root_pc + 11) % 12
            quality = "diminished7" if seventh else "diminished"
        else:
            raise ParseError(
                f"Secondary-dominant main part {main!r} in {token!r} must be one of V/V7/VII/VII7 "
                f"(rule 19: D(X) in {{V/X, VII/X}})."
            )
        chord = Chord(Pitch(root_pc), quality)
        return Terminal(raw=token, chord=chord, target_degree=target_degree)

    try:
        chord = Chord.from_roman(token, key.as_chord_key_str())
    except ValueError as e:
        raise ParseError(
            f"Could not parse token {token!r} as a Roman numeral in {key}: {e}"
        )
    assert (
        chord.key == key.as_chord_key_str()
    )  # from_roman tags the chord with the key it used

    # Rule (23): d is always V (major/dominant7) or VII (diminished/diminished7),
    if (
        key.mode == "minor"
        and chord.root.key_num % 12 == key.degree_pc(5)
        and chord.quality in ("minor", "minor7")
    ):
        chord = Chord(
            chord.root, "dominant7" if chord.quality == "minor7" else "major"
        )

    # Rule (23)/(19): d's VII-substitute is always built on the raised leading tone.
    if (
        key.mode == "minor"
        and chord.root.key_num % 12 == key.degree_pc(7)
        and chord.quality in ("diminished", "diminished7")
    ):
        raised_root = (key.tonic_pc + 11) % 12
        chord = Chord(Pitch(raised_root), chord.quality)

    return Terminal(raw=token, chord=chord, target_degree=None)


def _terminal_degree(chord: Chord, key: Key) -> Optional[int]:
    interval = (chord.root.key_num - key.tonic_pc) % 12
    scale = key.scale()
    if interval in scale:
        return scale.index(interval) + 1
    if key.mode == "minor" and interval == 11:
        # The raised leading tone in minor (again). See core.function_to_chord
        return 7
    return None


# ---------------------------------------------------------------------------

# Preprocessing: secondary dominants (17/19), repetition (28)


def _build_constituents(tokens: list[str], key: Key) -> list[Constituent]:
    terms = [parse_token(t, key) for t in tokens]
    n = len(terms)
    out: list[Constituent] = []
    i = 0
    while i < n:
        t = terms[i]

        if t.target_degree is not None:  # rule 17/19: D(X) X
            if i + 1 >= n:
                raise ParseError(
                    f"'{t.raw}' is a secondary dominant with nothing to resolve to."
                )
            nxt = terms[i + 1]
            nxt_degree = _terminal_degree(nxt.chord, key)
            if nxt.target_degree is not None or nxt_degree != t.target_degree:
                raise ParseError(
                    f"'{t.raw}' does not resolve to its stated target in the following token '{nxt.raw}'."
                )
            d_node = Node(t.raw, "surface", key, rule="19", chord=t.chord)
            x_node = Node(nxt.raw, "surface", key, rule="", chord=nxt.chord)
            wrapper = Node(
                nxt.raw,
                "scaledegree",
                key,
                rule="17",
                children=[d_node, x_node],
            )
            out.append(
                Constituent(
                    degree=nxt_degree, quality=nxt.chord.quality, node=wrapper
                )
            )
            i += 2
            continue

        # rule 28: contiguous run of identical chords -> right-branching repetition chain
        j = i + 1
        while (
            j < n
            and terms[j].target_degree is None
            and terms[j].chord == t.chord
        ):
            j += 1
        if j > i + 1:
            node = Node(t.raw, "surface", key, chord=t.chord)
            for _ in range(j - i - 1):
                node = Node(
                    t.raw,
                    "scaledegree",
                    key,
                    rule="28",
                    children=[node, Node(t.raw, "surface", key, chord=t.chord)],
                )
            degree = _terminal_degree(t.chord, key)
            if degree is None:
                raise ParseError(f"'{t.raw}' is not diatonic in {key}.")
            out.append(
                Constituent(degree=degree, quality=t.chord.quality, node=node)
            )
            i = j
            continue

        degree = _terminal_degree(t.chord, key)
        if degree is None:
            raise ParseError(
                f"'{t.raw}' is not diatonic in {key} and was not marked as a secondary dominant "
                f"(use e.g. 'V7/ii')."
            )
        out.append(
            Constituent(
                degree=degree,
                quality=t.chord.quality,
                node=Node(t.raw, "surface", key, chord=t.chord),
            )
        )
        i += 1
    return out


# ---------------------------------------------------------------------------

# Function assignment, rules (11)-(14) and (20)-(27) (inverse direction)


def _build_reverse_table() -> dict[tuple[str, int, str], list[str]]:
    table: dict[tuple[str, int, str], list[str]] = {}
    for func in ("t", "s", "tp", "sp", "dp", "tcp"):
        for mode, options in FUNCTION_REALIZATION.get(func, {}).items():
            for degree, override in options:
                if override is not None:
                    comp = _TRIAD_COMPONENT.get(override, override)
                else:
                    triads = MAJOR_TRIADS if mode == "major" else MINOR_TRIADS
                    comp = triads[degree - 1]
                table.setdefault((mode, degree, comp), []).append(func)
    return table


_REVERSE_TABLE = _build_reverse_table()


def _function_candidates(degree: int, quality: str, key: Key) -> list[str]:
    comp = _TRIAD_COMPONENT.get(quality, quality)
    candidates: list[str] = []
    # `d` (rule 23) is quality-forced (V/vii-dim), not diatonic-triad-driven. Handled separately.
    if degree == 5 and quality in ("major", "dominant7"):
        candidates.append("d")
    if degree == 7 and quality in ("diminished", "diminished7"):
        candidates.append("d")
    candidates += _REVERSE_TABLE.get((key.mode, degree, comp), [])
    return candidates


def _function_nodes(
    constituent: Constituent, key: Key
) -> list[tuple[str, Node]]:
    """
    Returns one [(base_function_label, fully-nested Node), ...]
    per grammatically valid reading of this constituent.
    """
    out = []
    for realized in _function_candidates(
        constituent.degree, constituent.quality, key
    ):
        base = BASE_OF[realized]
        inner = Node(
            realized,
            "function",
            key,
            rule=RULE_TERMINAL[realized],
            children=[constituent.node],
        )
        node = (
            inner
            if base == realized
            else Node(
                base,
                "function",
                key,
                rule=SUBSTITUTION_RULE[realized],
                children=[inner],
            )
        )
        out.append((base, node))
    return out


# ---------------------------------------------------------------------------

# CYK chart over regions (rules 4-10), plus phrase level (rules 1-3, 21)


def _count_nodes(node: Node) -> int:
    return 1 + sum(_count_nodes(c) for c in node.children)


# ---------------------------------------------------------------------------

# Modulation (rules 15/16), without pivot


NON_TONIC_FUNCTIONS = ("s", "d", "tp", "sp", "dp", "tcp")


@dataclass
class _Frame:
    key: Key
    items: list  # ('token', str) | ('resolved', base_function: str, Node)
    licensing_function: Optional[str] = (
        None  # the X (rule 15) that opened this frame; None for a root
    )


def _frame_to_slots(
    frame: "_Frame",
) -> tuple[list[list[tuple[str, Node]]], list[Optional[tuple[int, Node]]]]:
    """
    Turn a frame's mixed item list
    (raw tokens interleaved with already-resolved modulation slots)
    into the func_options/plain_positions shape `_cyk_region_chart` expects.
    Runs of raw tokens are grouped and passed through the normal `_build_constituents` pipeline together
    (so secondary-dominant pairing (17) and repetition (28) still work across them);
    a resolved slot is a ready-made singleton.
    """
    func_options: list[list[tuple[str, Node]]] = []
    plain_positions: list[Optional[tuple[int, Node]]] = []
    token_run: list[str] = []

    def flush():
        if not token_run:
            return
        for c in _build_constituents(list(token_run), frame.key):
            opts = _function_nodes(c, frame.key)
            if not opts:
                raise ParseError(
                    f"Degree {c.degree} (quality {c.quality}) cannot be assigned any tonal "
                    f"function in {frame.key}."
                )
            func_options.append(opts)
            plain_positions.append((c.degree, c.node))
        token_run.clear()

    for item in frame.items:
        if item[0] == "token":
            token_run.append(item[1])
        else:
            flush()
            _, base, node = item
            func_options.append([(base, node)])
            plain_positions.append(None)
    flush()
    return func_options, plain_positions


def _finalize_frame(frame: "_Frame") -> Node:
    """
    Parse one frame's material and return its region-level TR node
    (unwrapped: the caller decides whether it becomes a standalone 'piece' or an embedded rule-15 child).
    """
    func_options, plain_positions = _frame_to_slots(frame)
    if not func_options:
        raise ParseError(f"Empty key-phase in {frame.key}.")
    top_tr = _cyk_region_chart(
        func_options, frame.key, plain_positions=plain_positions
    )
    if top_tr is None:
        raise ParseError(
            f"No valid derivation found for the material in {frame.key}."
        )
    return top_tr


def _make_modulation_slot(
    child_top_tr: Node, licensing_function: str, parent_key: Key
) -> tuple[str, Node]:
    """
    Rule (15): X_key=y -> TR_key=psi(X,y).
    Wraps a finished child TR as the realisation of `licensing_function` in the parent's key,
    including the substitution nesting (11)-(14) if `licensing_function` isn't a base function
    (e.g., 'sp' nests inside 's').
    """
    inner = Node(
        licensing_function,
        "function",
        parent_key,
        rule="15",
        children=[child_top_tr],
    )
    base = BASE_OF[licensing_function]
    if base == licensing_function:
        return base, inner
    return base, Node(
        base,
        "function",
        parent_key,
        rule=SUBSTITUTION_RULE[licensing_function],
        children=[inner],
    )


def parse_with_modulation(
    items: list[tuple[str, Key]], max_depth: int = 4
) -> list[Node]:
    """
    Parse a sequence of (token, local_key) pairs.
    I.e. every token is individually tagged with the key it's relative to,
    as in both DCML and RomanText-style annotation.

    No pivot chords: each token belongs to exactly one key phase, period (see this module's docstring).

    Consecutive same-key tokens are grouped into phases automatically;
    no separate "phase" markup is required.

    For each new phase, in order:
    1. If its key is already open on the stack
        (the piece is returning to a key it was in before, e.g., C–G-C),
        reopen that frame and keep appending to it,
        rather than treating the return as a fresh modulation.
    2. Else, if the key equals psi(X, K) for some function X
        and some currently-open key K (innermost first),
        rule 15 allows nesting it as X's realisation inside K's derivation.
        This is the form of the Waldstein-sonata pattern (Figure 6):
        C tonicizes G, then F, each nested one level inside the surrounding C.
    3. Otherwise, (e.g., in a chromatic-mediant jump)
        rule 15 can't reach in a single step.
        We use Bb -> Gb as the standing example with a nod to Schubert.
        The relationship isn't expressible by this grammar in one step.
        In this case, close out everything currently open as a finished tree
        and start a fresh, sibling one.
        This is a kind of "at minimum, separate tree per phase" fallback.

    `max_depth` hard-caps how many frames may be open at once
    (a new nesting attempt is skipped, falling through to case 3,
    once the stack is already `max_depth` deep).
    This bounds how deep the resulting tree(s) can nest,
    which is useful for keeping analyses of unseen pieces manageable and comparable.

    Returns a list of trees (root 'piece' nodes)
    of length 1 unless case 3 is reached at least once.
    """
    if not items:
        raise ParseError("Empty input.")

    phases: list[tuple[Key, list[str]]] = []
    for token, k in items:
        if phases and phases[-1][0] == k:
            phases[-1][1].append(token)
        else:
            phases.append((k, [token]))

    def close_to(stack: list[_Frame], target_len: int) -> Optional[Node]:
        """
        Pop frames down to `target_len`, folding each into its new-top
        parent as a resolved modulation slot.
        If the stack empties entirely,
        returns that last (root) frame's finished TR.
        """
        result = None
        while len(stack) > target_len:
            child = stack.pop()
            top_tr = _finalize_frame(child)
            if stack:
                base, node = _make_modulation_slot(
                    top_tr, child.licensing_function, stack[-1].key
                )
                stack[-1].items.append(("resolved", base, node))
            else:
                result = top_tr
        return result

    results: list[Node] = []
    stack: list[_Frame] = [
        _Frame(key=phases[0][0], items=[("token", t) for t in phases[0][1]])
    ]

    for k, toks in phases[1:]:
        match_idx = next(
            (i for i in range(len(stack) - 1, -1, -1) if stack[i].key == k),
            None,
        )
        if match_idx is not None:  # case 1: return to an already-open key
            close_to(stack, match_idx + 1)
            stack[match_idx].items.extend(("token", t) for t in toks)
            continue

        nested = False
        if (
            len(stack) < max_depth
        ):  # case 2: try nesting under an open frame via psi
            for depth, frame in enumerate(reversed(stack)):
                for x in NON_TONIC_FUNCTIONS:
                    if psi(x, frame.key) == k:
                        target_idx = len(stack) - 1 - depth
                        close_to(stack, target_idx + 1)
                        stack.append(
                            _Frame(
                                key=k,
                                items=[("token", t) for t in toks],
                                licensing_function=x,
                            )
                        )
                        nested = True
                        break
                if nested:
                    break
        if nested:
            continue

        # case 3: unrelated key. Close everything open as one finished tree, start fresh
        completed = close_to(stack, 0)
        if completed is not None:
            results.append(
                Node(
                    "piece",
                    "phrase",
                    completed.key,
                    rule="2",
                    children=[completed],
                )
            )
        stack = [_Frame(key=k, items=[("token", t) for t in toks])]

    completed = close_to(stack, 0)
    if completed is not None:
        results.append(
            Node(
                "piece", "phrase", completed.key, rule="2", children=[completed]
            )
        )
    return results


def parse(tokens: list[str], key: Key) -> Node:
    """
    Parse `tokens` (Roman numerals relative to the fixed `key`) and
    return the single best-scoring derivation tree, rooted at 'piece'.
    Raises ParseError if no valid derivation exists under the rule subset
    documented in this module's docstring.
    """
    constituents = _build_constituents(tokens, key)
    m = len(constituents)
    if m == 0:
        raise ParseError("Empty input.")

    func_options = [_function_nodes(c, key) for c in constituents]
    for idx, opts in enumerate(func_options):
        if not opts:
            raise ParseError(
                f"Position {idx} ('{constituents[idx].node.label}', degree {constituents[idx].degree}, "
                f"quality {constituents[idx].quality}) cannot be assigned any tonal function in {key}."
            )

    top_tr = _cyk_region_chart(
        func_options,
        key,
        plain_positions=[(c.degree, c.node) for c in constituents],
    )
    if top_tr is None:
        raise ParseError(
            f"No valid derivation found for {tokens} in {key} under the rule subset this parser supports "
            f"(no modulation/rule 15-16, no rule 18 fifth-sequences)."
        )
    return Node("piece", "phrase", key, rule="2", children=[top_tr])


def _cyk_region_chart(
    func_options: list[list[tuple[str, Node]]],
    key: Key,
    plain_positions: Optional[list[Optional[tuple[int, Node]]]] = None,
) -> Optional[Node]:
    """
    Core chart parser:
    given, for each of `m` atomic positions,
    the list of (base_function, Node) readings available there
    (any from plain scale degrees, secondary dominants, repetition chains, or a pre-resolved modulation subtree),
    find the single best-scoring TR spanning all `m` positions (or None).

    `plain_positions`, if given, is (plain scale degree, surface Node) for
    positions that are an ordinary single-token diatonic constituent
    (None elsewhere, e.g. secondary dominants, repetition chains, or modulation slots).

    This is used only for the rule-21 (t -> I IV I) pattern.
    """
    m = len(func_options)
    chart: list[list[dict[str, Node]]] = [
        [{} for _ in range(m + 1)] for _ in range(m + 1)
    ]

    def set_best(i: int, j: int, label: str, candidate: Node) -> None:
        current = chart[i][j].get(label)
        if current is None or _count_nodes(candidate) < _count_nodes(current):
            chart[i][j][label] = candidate

    # base cases: rules 8, 9, 10 (region <- single atomic function) ---
    for i in range(m):
        for base, fnode in func_options[i]:
            region = {"t": "TR", "d": "DR", "s": "SR"}[base]
            rule = {"t": "8", "d": "9", "s": "10"}[base]
            set_best(
                i,
                i + 1,
                region,
                Node(region, "region", key, rule=rule, children=[fnode]),
            )

    # rule 21: t -> I IV I (plagal), recognized as a 3-position pattern ---
    if plain_positions is not None:
        for i in range(m - 2):
            trio = plain_positions[i : i + 3]
            if all(p is not None for p in trio) and tuple(
                p[0] for p in trio
            ) == (1, 4, 1):
                t_node = Node(
                    "t",
                    "function",
                    key,
                    rule="21",
                    children=[p[1] for p in trio],
                )
                set_best(
                    i,
                    i + 3,
                    "TR",
                    Node("TR", "region", key, rule="8", children=[t_node]),
                )

    # spans of increasing length: rules 4, 5, 6, 7 ---
    for length in range(2, m + 1):
        for i in range(0, m - length + 1):
            j = i + length
            for k in range(i + 1, j):
                for label in ("TR", "DR", "SR"):  # rule 7: XR -> XR XR
                    left, right = chart[i][k].get(label), chart[k][j].get(label)
                    if left is not None and right is not None:
                        set_best(
                            i,
                            j,
                            label,
                            Node(
                                label,
                                "region",
                                key,
                                rule="7",
                                children=[left, right],
                            ),
                        )
                left_tr, right_dr = chart[i][k].get("TR"), chart[k][j].get(
                    "DR"
                )  # rule 6: TR -> TR DR
                if left_tr is not None and right_dr is not None:
                    set_best(
                        i,
                        j,
                        "TR",
                        Node(
                            "TR",
                            "region",
                            key,
                            rule="6",
                            children=[left_tr, right_dr],
                        ),
                    )

            # rules 4 & 5 always end on a single atomic function (the last position, j-1)
            k = j - 1
            left_dr = chart[i][k].get("DR")
            if left_dr is not None:
                for base, fnode in func_options[k]:
                    if base == "t":
                        set_best(
                            i,
                            j,
                            "TR",
                            Node(
                                "TR",
                                "region",
                                key,
                                rule="4",
                                children=[left_dr, fnode],
                            ),
                        )
            left_sr = chart[i][k].get("SR")
            if left_sr is not None:
                for base, fnode in func_options[k]:
                    if base == "d":
                        set_best(
                            i,
                            j,
                            "DR",
                            Node(
                                "DR",
                                "region",
                                key,
                                rule="5",
                                children=[left_sr, fnode],
                            ),
                        )

    return chart[0][m].get("TR")


# TODO (phase 3): rule 15/16 modulation support. Sketch: allow a function
# node to *also* be built via `psi()` re-entering `_expand_region`-style
# recursion at a new local key over a sub-span, i.e. add a chart dimension
# for "local key at this span" and, for pivot chords, allow one chart
# position to be consumed by two different parent derivations rather than
# exactly one (breaking the CYK invariant that spans partition the input) --
# this is exactly the non-planarity the paper flags in Figure 3, and is why
# it's being deferred rather than bolted on here.
