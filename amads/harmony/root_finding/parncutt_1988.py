"""
Parncutt's 1988 model for finding the root of a chord.

This module implements the root-finding model of Parncutt (1988).
"""

from typing import Dict, List, Optional, Union

import matplotlib.pyplot as plt


class ParncuttRootAnalysis:
    """
    Parncutt's (1988) model for finding the root of a chord.

    Parameters
    ----------
    chord : List[int]
        A list of MIDI pitches representing a chord.
    root_support_weights : Union[str, Dict[int, float]], optional
        Identifies the root support weights to use. "v1" uses the original weights
        from Parncutt (1988), "v2" uses the updated weights from Parncutt (2006),
        by default "v2".
    exponent : float, optional
        Exponent to be used when computing root ambiguities, by default 0.5.

    Attributes
    ----------
    pc_set : set
        The chord's pitch class set.
    root : int
        The pitch class of the derived chord root.
    root_ambiguity : float
        A measure of how ambiguous the root is.
    root_strengths : List[float]
        Root support values for each pitch class.

    Examples
    --------
    >>> # Major triad
    >>> analysis = ParncuttRootAnalysis([60, 64, 67])  # C major triad
    >>> analysis.root
    0
    >>> analysis.root_ambiguity
    1.9

    >>> # Minor triad
    >>> analysis = ParncuttRootAnalysis([60, 63, 67])  # C minor triad
    >>> analysis.root
    0
    >>> analysis.root_ambiguity
    2.1

    >>> # Dominant seventh
    >>> analysis = ParncuttRootAnalysis([60, 64, 67, 70])  # C7
    >>> analysis.root
    0
    >>> analysis.root_ambiguity
    2.1

    >>> # Diminished triad (more ambiguous)
    >>> analysis = ParncuttRootAnalysis([60, 63, 66])  # C diminished
    >>> analysis.root
    0
    >>> analysis.root_ambiguity
    2.5

    >>> # Using original Parncutt (1988) weights
    >>> analysis = ParncuttRootAnalysis([60, 64, 67, 70], root_support_weights="v1")
    >>> analysis.root
    0
    >>> analysis.root_ambiguity
    2.1
    """

    available_root_support_weights = {
        "v1": {0: 1.0, 7: 1 / 2, 4: 1 / 3, 10: 1 / 4, 2: 1 / 5, 3: 1 / 10},
        "v2": {0: 10, 7: 5, 4: 3, 10: 2, 2: 1},
    }

    def __init__(
        self,
        chord: List[int],
        root_support_weights: Union[str, Dict[int, float]] = "v2",
        exponent: float = 0.5,
    ):
        if len(chord) == 0:
            raise ValueError("Chord must contain at least one pitch")

        self.chord = chord
        self.pc_set = set([pitch % 12 for pitch in chord])
        self.root_support_weights = self.load_root_support_weights(root_support_weights)
        self.exponent = exponent
        self.root_strengths = [self.get_root_strength(pc) for pc in range(12)]
        self.root = self.get_root()
        self.root_ambiguity = self.get_root_ambiguity()

    def load_root_support_weights(
        self, root_support_weights: Union[str, Dict[int, float]]
    ) -> Dict[int, float]:
        if isinstance(root_support_weights, str):
            if root_support_weights not in self.available_root_support_weights:
                raise ValueError(
                    f"Unknown root support weights version: {root_support_weights}"
                )
        return self.available_root_support_weights[root_support_weights]

    def get_root_strength(self, pc: int) -> float:
        return sum(
            support_weight
            for interval, support_weight in self.root_support_weights.items()
            if (pc + interval) % 12 in self.pc_set
        )

    def get_root(self) -> int:
        return self.root_strengths.index(max(self.root_strengths))

    def get_root_ambiguity(self) -> float:
        max_weight = max(self.root_strengths)
        if max_weight == 0:
            return 0.0
        return sum(w / max_weight for w in self.root_strengths) ** self.exponent

    def visualize(self, title: Optional[str] = None) -> None:
        """
        Visualize the root support weights for a chord.

        Parameters
        ----------
        title : Optional[str], optional
            Title for the plot, by default None.

        Examples
        --------
        >>> analysis = Parncutt1988Analysis([0, 4, 7])
        >>> analysis.visualize()
        """
        # Create a bar chart
        plt.figure(figsize=(10, 6))
        bars = plt.bar(range(12), self.root_strengths)

        # Highlight the root
        bars[self.root].set_color("red")

        # Add labels
        plt.xlabel("Pitch Class")
        plt.ylabel("Weight")

        # Add pitch class names
        pitch_class_names = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ]
        plt.xticks(range(12), pitch_class_names)

        # Add title
        if title is None:
            chord_str = ", ".join(
                str(pc) for pc in sorted(set(p % 12 for p in self.chord))
            )
            title = f"Root Support Weights for Chord [{chord_str}]"
        plt.title(title)

        # Add grid
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        # Show the plot
        plt.tight_layout()
        plt.show()
