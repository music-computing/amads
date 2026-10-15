import random

from amads.harmony.hierarchy.core import Key, psi
from amads.harmony.hierarchy.generator import Generator
from amads.harmony.hierarchy.parser import parse_with_modulation

# -----------------------------------------------------------------------------

# Core and generator


def test_psi_matches_paper_examples():
    """Paper section 3.2.3: psi(d, B maj) = F# maj; psi(tp, A maj) = F# min"""
    assert str(psi("d", Key.from_str("B"))) == "F#"
    assert str(psi("tp", Key.from_str("A"))) == "F#m"


def test_psi_rejects_diminished_realizations():
    """
    1. VII in major is diminished -> cannot license a modulation;
    2. tonic itself is excluded by definition
    """
    assert psi("d", Key.from_str("C"), degree_choice=1) is None
    assert psi("t", Key.from_str("C")) is None


def test_generator_produces_well_formed_tree():
    g = Generator(rng=random.Random(0), growth_bias=0.3)
    tree = g.generate_piece(Key.from_str("C"), cadence="perfect", max_depth=4)
    leaves = tree.leaves()
    assert all(
        leaf.kind == "surface" and leaf.chord is not None for leaf in leaves
    )
    assert len(leaves) >= 1


def test_plagal_cadence_is_I_IV_I():
    g = Generator(rng=random.Random(0))
    tree = g.generate_piece(Key.from_str("C"), cadence="plagal")
    assert tree.labels_sequence() == ["C", "F", "C"]


def test_half_cadence_ends_on_dominant_function():
    """
    piece -> TR (rule 6: TR -> TR DR).
    The phrase is a single TR whose rightmost functional child is a DR,
    not a separate phrase-level pairing.
    """

    g = Generator(rng=random.Random(1))
    tree = g.generate_piece(Key.from_str("C"), cadence="half", max_depth=3)
    assert tree.children[0].label == "TR"
    assert tree.children[0].rule == "6"
    assert tree.children[0].children[-1].label == "DR"


def test_to_bracket_and_forest_do_not_crash():
    g = Generator(rng=random.Random(2))
    tree = g.generate_piece(Key.from_str("G"), cadence="perfect", max_depth=3)
    assert tree.to_bracket().startswith("(piece")
    assert "\\begin{forest}" in tree.to_forest()


# -----------------------------------------------------------------------------

# Tests for parser.parse_with_modulation

C = Key.from_str("C")
G = Key.from_str("G")
F = Key.from_str("F")


def test_waldstein_style_nesting():
    """Paper's Figure 6 description: an overarching T-S-D-T in C, with the
    subdominant and dominant each briefly tonicized (nested one level in),
    not two independent phrases."""
    items = [("I", C), ("I", F), ("I", G), ("I", C)]
    trees = parse_with_modulation(items)
    assert len(trees) == 1
    tree = trees[0]
    assert [leaf.chord.label for leaf in tree.leaves()] == ["C", "F", "G", "C"]
    # both tonicizations must be rule-15 nodes, one level under the outer C
    mod_nodes = [n for n in tree if n.rule == "15"]
    assert len(mod_nodes) == 2
    assert {n.label for n in mod_nodes} == {"s", "d"}
    assert all(
        n.key == C for n in mod_nodes
    )  # rule 15 fires *in* the outer key
    assert {n.children[0].key for n in mod_nodes} == {F, G}


def test_return_to_key_reopens_frame_not_a_fresh_modulation():
    items = [("I", C), ("I", G), ("I", C)]
    trees = parse_with_modulation(items)
    assert len(trees) == 1
    assert [leaf.chord.label for leaf in trees[0].leaves()] == ["C", "G", "C"]


def test_chromatic_mediant_falls_back_to_separate_trees():
    Bb, Gb = Key.from_str("Bb"), Key.from_str("Gb")
    items = [("I", Bb), ("V", Bb), ("I", Gb), ("V", Gb)]
    trees = parse_with_modulation(items)
    assert len(trees) == 2
    assert trees[0].key == Bb
    assert (
        trees[1].key == Gb
    )  # (rendered as F# -- enharmonic, no spelling distinction; see core.Key)


def test_max_depth_caps_nesting():
    items = [("I", C), ("I", G)]
    # depth cap of 1: no room to open a second frame -> falls back to two trees
    shallow = parse_with_modulation(items, max_depth=1)
    assert len(shallow) == 2
    # default depth: nests normally -> one tree
    nested = parse_with_modulation(items, max_depth=4)
    assert len(nested) == 1


def test_single_phase_no_modulation_needed():
    items = [("I", C), ("IV", C), ("V", C), ("I", C)]
    trees = parse_with_modulation(items)
    assert len(trees) == 1
    assert [leaf.chord.label for leaf in trees[0].leaves()] == [
        "C",
        "F",
        "G",
        "C",
    ]


# -----------------------------------------------------------------------------
