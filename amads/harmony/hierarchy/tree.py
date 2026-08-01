"""
This module
(amads.harmony.hierarchy.tree)
is part of
amads.harmony.hierarchy.
See top level notes at
(amads.harmony.hierarchy.core)

A single tree type shared by every level of the grammar
(phrase, functional, scale-degree, surface).

This is a data structure representation of the paper's dash-diagrams
(Figure 1) and hand-drawn trees (Figures 2-6).

Design notes
------------
- `kind` records which grammar level produced the node
    ('phrase', 'region', 'function', 'scaledegree', 'surface'),
    purely for rendering/inspection.
- `rule` records the paper's rule number (e.g. "4", "15") that licensed
    this expansion, so any tree can be checked back against the paper.
- `key` is carried on every node
    (the "key" feature threaded through the derivation, section 3).
- `pivot_id`:
    when the modulation rule generates a pivot chord twice
    (once from each adjacent branch, as in Figure 3),
    both nodes share a `pivot_id` so renderers can mark them as identical ('=' in the paper's Figure 3).
    TODO see notes elsewhere about the non-use of pivot chords so far.
"""

from dataclasses import dataclass, field
from typing import Optional

from amads.core.chord import Chord
from amads.harmony.hierarchy.core import Key


@dataclass
class Node:
    label: str  # e.g. "TR", "d", "V", "G7"
    kind: str  # 'phrase' | 'region' | 'function' | 'scaledegree' | 'surface'
    key: Key
    rule: str = ""  # paper rule number, e.g. "4"

    children: list["Node"] = field(default_factory=list)

    chord: Optional[Chord] = None  # populated at the surface level
    pivot_id: Optional[int] = (
        None  # shared id for pivot chords (see module docstring)
    )

    # ------------------------------------------------------------------

    # basic tree utilities

    def leaves(self) -> list["Node"]:
        if not self.children:
            return [self]
        return [leaf for child in self.children for leaf in child.leaves()]

    def chord_sequence(self) -> list[Chord]:
        return [leaf.chord for leaf in self.leaves() if leaf.chord is not None]

    def labels_sequence(self) -> list[str]:
        out = []
        for leaf in self.leaves():
            out.append(
                leaf.chord.label if leaf.chord is not None else leaf.label
            )
        return out

    def roman_sequence(self) -> list[str]:
        """Roman-numeral tokens for each surface leaf, in the format
        parser.parse() expects (generator.py sets `label` to the roman
        numeral already, for every surface leaf)."""
        return [leaf.label for leaf in self.leaves()]

    def __iter__(self):
        yield self
        for c in self.children:
            yield from c

    # ------------------------------------------------------------------

    # text rendering

    def _node_str(self) -> str:
        if self.kind == "surface" and self.chord is not None:
            tag = self.chord.label
        else:
            tag = self.label
        return f"{tag}[{self.key}]" if self.key is not None else tag

    def to_bracket(self) -> str:
        """Bracketed string, e.g. '(TR (DR d) t)': also valid input for
        nltk.Tree.fromstring() if you want to use nltk's tree utilities."""
        s = self._node_str()
        if not self.children:
            return s
        inner = " ".join(c.to_bracket() for c in self.children)
        return f"({s} {inner})"

    def pretty(self, indent: int = 0) -> str:
        """Readable indented tree for terminal/notebook output."""
        pad = "  " * indent
        line = f"{pad}{self._node_str()}"
        if self.rule:
            line += f"   (rule {self.rule})"
        if self.pivot_id is not None:
            line += f"   [pivot #{self.pivot_id}]"
        lines = [line]
        for c in self.children:
            lines.append(c.pretty(indent + 1))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.to_bracket()

    # ------------------------------------------------------------------

    # LaTeX rendering (forest package)

    def to_forest(self, show_key: bool = True, show_rule: bool = False) -> str:
        """
        LaTeX `forest` code
        (body only: wrap with `to_forest_document` for a standalone compilable file).
        Requires \\usepackage{forest} and the tree fits naturally with the `linguistics` forest library, e.g.:
            \\usepackage[linguistics]{forest}
        """

        def esc(s: str) -> str:
            return s.replace("#", "\\#")

        def node_tex(n: "Node") -> str:
            tag = (
                n.chord.label
                if (n.kind == "surface" and n.chord is not None)
                else n.label
            )
            tag = esc(tag)
            sub = (
                f"$_{{{esc(str(n.key))}}}$"
                if (show_key and n.key is not None)
                else ""
            )
            content = f"{tag}{sub}"
            if show_rule and n.rule:
                content += f", name={{r{n.rule}}}"
            if n.children:
                kids = " ".join(node_tex(c) for c in n.children)
                return f"[{{{content}}} {kids}]"
            return f"[{{{content}}}]"

        return f"\\begin{{forest}}\nfor tree={{align=center}}\n{node_tex(self)}\n\\end{{forest}}"

    def to_forest_document(self, **kwargs) -> str:
        body = self.to_forest(**kwargs)
        return (
            "\\documentclass[border=5pt]{standalone}\n"
            "\\usepackage[linguistics]{forest}\n"
            "\\begin{document}\n"
            f"{body}\n"
            "\\end{document}\n"
        )
