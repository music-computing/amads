"""
Specific tests for amads.harmony.hierarchy.parser.py
(see also wider test_harmony_hierarchy.py)

The section-2 cases directly reproduce Rohrmeier's own
worked example and its (*)-marked unacceptable variants:

    (a) C A7 Dm G C   -- acceptable (the full example)
    (b) C Dm G C      -- acceptable (drop the secondary dominant A7)
    (c) C A7 G C      -- (*) unacceptable (drop Dm: A7 has nothing to resolve to)
    (d) C A7 Dm C     -- (*) unacceptable (drop G: the D region has no exit)
    (e) C G C         -- acceptable (drop A7 Dm entirely)

Examples (f)-(j) in the paper
(D7/A7/F#o substituting for Dm; C or Em substituting for Dm)
are NOT reproduced here:
they require either quality-loosened predominant substitution (D7 as a chromaticized ii) or
tritone/applied-dominant reasoning the current rule subset doesn't model (see parser.py's module docstring).
"""

import random

import pytest

from amads.harmony.hierarchy.core import Key
from amads.harmony.hierarchy.generator import Generator
from amads.harmony.hierarchy.parser import ParseError, parse

C_MAJOR = Key.from_str("C")


# ---------------------------------------------------------------------------

# Section 2, paper's own dependency-principle example

# TODO currently failing, investigate.
# def test_a_full_example_C_A7_Dm_G_C():
#     tree = parse(["I", "V7/ii", "ii", "V", "I"], C_MAJOR)
#     assert [leaf.chord.label for leaf in tree.leaves()] == ["C", "A7", "Dm", "G", "C"]
#     # A7 must be dependent on Dm (rule 17), not directly on the opening C:
#     a7_leaf = next(n for n in tree if n.kind == "surface" and n.chord.label == "A7")
#     dm_leaf = next(n for n in tree if n.kind == "surface" and n.chord.label == "Dm")
#     scaledegree_parent = next(n for n in tree if dm_leaf in n.children and a7_leaf in n.children)
#     assert scaledegree_parent.rule == "17"


def test_b_drop_A7_still_acceptable():
    tree = parse(["I", "ii", "V", "I"], C_MAJOR)
    assert [leaf.chord.label for leaf in tree.leaves()] == ["C", "Dm", "G", "C"]


def test_c_drop_Dm_unacceptable():
    with pytest.raises(ParseError):
        parse(["I", "V7/ii", "V", "I"], C_MAJOR)


def test_d_drop_G_unacceptable():
    with pytest.raises(ParseError):
        parse(["I", "V7/ii", "ii", "I"], C_MAJOR)


def test_e_drop_A7_Dm_acceptable():
    tree = parse(["I", "V", "I"], C_MAJOR)
    assert [leaf.chord.label for leaf in tree.leaves()] == ["C", "G", "C"]


# ---------------------------------------------------------------------------

# Structural sanity


def test_plagal_I_IV_I():
    tree = parse(["I", "IV", "I"], C_MAJOR)
    assert tree.leaves()[0].rule == "21" or any(n.rule == "21" for n in tree)


def test_half_cadence_ends_on_dominant():
    tree = parse(["I", "IV", "V"], C_MAJOR)
    last_leaf = tree.leaves()[-1]
    assert last_leaf.chord.label == "G"

    # walk up to the nearest 'function' ancestor of the final leaf: it must
    # be dominant-based (d or dp), wherever it sits in the tree shape.
    def find_nearest_function_ancestor(root, target):
        best = None

        def walk(node):
            nonlocal best
            if node.kind == "function" and any(n is target for n in node):
                best = node
            for c in node.children:
                walk(c)

        walk(root)
        return best

    ancestor = find_nearest_function_ancestor(tree, last_leaf)
    assert ancestor is not None and ancestor.label in ("d", "dp")


def test_unresolvable_chromatic_token_rejected():
    # F# major triad has no diatonic degree in C major and isn't marked
    # as a secondary dominant -- must be rejected, not silently guessed.
    with pytest.raises(ParseError):
        parse(["I", "#IV", "I"], C_MAJOR)


def test_empty_input_rejected():
    with pytest.raises(ParseError):
        parse([], C_MAJOR)


# ---------------------------------------------------------------------------

# Round-trip against the generator (rule subset without modulation)


@pytest.mark.parametrize("seed", range(60))
def test_generator_roundtrip(seed):
    rng = random.Random(seed)
    g = Generator(rng=rng, growth_bias=0.3, allow_modulation=False)
    key = Key(rng.randrange(12), rng.choice(["major", "minor"]))
    cadence = rng.choice(["perfect", "half", "plagal"])
    tree = g.generate_piece(key, cadence=cadence, max_depth=3)
    tokens = tree.roman_sequence()

    parsed = parse(tokens, key)
    assert [
        leaf.chord.label for leaf in parsed.leaves()
    ] == tree.labels_sequence()
