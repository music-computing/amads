# fmt: off
"""
This module
(amads.harmony.hierarchy.generator)
is part of
amads.harmony.hierarchy.
See top level notes at
(amads.harmony.hierarchy.core)

This module implements the top-down sampler for the grammar (generation direction), notably:
- Rule 6) TR->TR DR,
- Rule 7) XR->XR XR, and
- Rules 11-16) the substitution/modulation/mode-change rules.

Note that these are recursive with no built-in stopping condition,
(intentionally in the paper's grammar so prolongation can nest arbitrarily),
but practically this sampler needs a stopping policy.

We use a simple depth budget: growth rules become impossible
once the budget hits zero (forcing a terminal rule),
and are otherwise sampled with a bias toward terminating,
so that trees can generally be limited to a readable and reasonable size.

Related, we have in mind use cases based on subtler evaluation metrics for machine learning,
in which context some hierarchically reduction may be useful, but extreme depth is probably counter-productive.
"""

import random
from typing import Optional

from amads.core.chord import Chord
from amads.harmony.hierarchy.core import (
    FUNCTION_REALIZATION,
    Key,
    function_to_chord,
)
from amads.harmony.hierarchy.rules import (
    RHS,
    ChildSpec,
    mode_change_expansions,
    modulation_expansions,
    phrase_expansions,
    region_expansions,
    scaledegree_terminal,
    substitution_expansions,
)
from amads.harmony.hierarchy.tree import Node


class Generator:
    def __init__(
            self,
            rng: Optional[random.Random] = None,
            growth_bias: float = 0.35,
            allow_modulation: bool = True):
        """
        Parameters
        ----------
        `growth_bias` in (0, 1):
            probability weight given to growing the tree further at each step (vs. terminating),
            before the depth budget forces termination anyway.
        `allow_modulation`: bool
            Default is True.
            Set False to restrict generation to the rule subset parser.py currently supports (no rules 15/16),
            which is useful for round-trip testing generator output through the parser.
        """
        self.rng = rng or random.Random()
        self.growth_bias = growth_bias
        self.allow_modulation = allow_modulation

    # ------------------------------------------------------------------

    def generate_piece(self, key: Key, cadence: str = "perfect", max_depth: int = 4) -> Node:
        """cadence in {'perfect', 'half', 'plagal'}. Returns the phrase-level root."""
        root = Node("piece", "phrase", key, rule="1")
        if cadence == "plagal":
            tr = Node("TR", "region", key, rule="2")
            root.children.append(tr)
            tr.children.append(self._plagal_tonic(key))
            return root

        rhs = phrase_expansions(key)[0]
        root.rule = rhs.rule_id
        force_half = cadence == "half"
        for cs in rhs.children:
            root.children.append(self._expand_region(cs.label, cs.key, max_depth, force_half_cadence=force_half))
        return root

    def _plagal_tonic(self, key: Key) -> Node:
        """Rule 21: t -> I IV I."""
        t_node = Node("t", "function", key, rule="21")
        for degree, roman in ((1, "I"), (4, "IV"), (1, "I")):
            chord = Chord.from_scale_degree(degree, key.as_chord_key_str())
            t_node.children.append(Node(roman, "surface", key, rule="21", chord=chord))
        return t_node

    # ------------------------------------------------------------------

    def _expand(self, spec: ChildSpec, depth_budget: int) -> Node:
        if spec.kind == "region":
            return self._expand_region(spec.label, spec.key, depth_budget)
        if spec.kind == "function":
            return self._expand_function(spec.label, spec.key, depth_budget)
        raise ValueError(f"Unexpected top-level kind in generator: {spec.kind}")

    def _expand_region(self, region: str, key: Key, depth_budget: int, force_half_cadence: bool = False) -> Node:
        options = region_expansions(region, key)
        terminal = [o for o in options if len(o.children) == 1]
        growth = [o for o in options if len(o.children) > 1]

        if force_half_cadence and region == "TR":
            rule6 = next(o for o in options if o.rule_id == "6")
            node = Node(region, "region", key, rule="6")
            left, right = rule6.children
            node.children = [
                self._expand_region(left.label, left.key, depth_budget - 1),
                self._expand_region(right.label, right.key, depth_budget - 1),
            ]
            return node

        if depth_budget <= 0 or not growth:
            chosen = self.rng.choice(terminal)
        elif self.rng.random() < self.growth_bias:
            chosen = self.rng.choice(growth)
        else:
            chosen = self.rng.choice(terminal)

        node = Node(region, "region", key, rule=chosen.rule_id)
        next_budget = depth_budget - 1
        node.children = [self._expand(cs, next_budget) for cs in chosen.children]
        return node

    def _expand_function(self, function: str, key: Key, depth_budget: int) -> Node:
        n_realizations = len(FUNCTION_REALIZATION.get(function, {}).get(key.mode, []))
        terminal_options: list[RHS] = [
            scaledegree_terminal(function, key, degree_choice=i) for i in range(n_realizations)
        ]
        growth_options: list[RHS] = list(substitution_expansions(function, key))
        if self.allow_modulation:
            growth_options += modulation_expansions(function, key) + mode_change_expansions(function, key)

        if depth_budget <= 0 or not growth_options:
            chosen = self.rng.choice(terminal_options)
            is_terminal = True
        elif self.rng.random() < self.growth_bias:
            chosen = self.rng.choice(growth_options)
            is_terminal = False
        else:
            chosen = self.rng.choice(terminal_options)
            is_terminal = True

        node = Node(function, "function", key, rule=chosen.rule_id)
        if is_terminal:
            cs = chosen.children[0]
            chord = function_to_chord(function, key, degree_choice=cs.degree_choice)
            numeral = chord.roman_numeral(key.as_chord_key_str())
            if numeral is None:
                # Again, special (only) case this currently happens:
                # `d`'s raised-leading-tone VII-substitute (rule 19/23).
                # Spell it directly.
                if function == "d" and chord.quality in ("diminished", "diminished7"):
                    numeral = "vii\u00b07" if chord.quality == "diminished7" else "vii\u00b0"
                else:
                    numeral = chord.label  # last-resort fallback; shouldn't normally happen
            node.children.append(Node(numeral, "surface", key, rule=chosen.rule_id, chord=chord))
        else:
            next_budget = depth_budget - 1
            node.children = [self._expand(cs, next_budget) for cs in chosen.children]
        return node
