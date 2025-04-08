"""
Parncutt's 1988 model for finding the root of a chord.

This module implements the root-finding model of Parncutt (1988).
"""

from typing import Dict, List, Optional, Union

import matplotlib.pyplot as plt

# Root support weights from Parncutt (1988) and Parncutt (2006)
ROOT_SUPPORT_WEIGHTS = {
    "v1": {0: 1.0, 7: 1 / 2, 4: 1 / 3, 10: 1 / 4, 2: 1 / 5, 3: 1 / 10},
    "v2": {0: 10, 7: 5, 4: 3, 10: 2, 2: 1},
}


def parn88(
    chord: List[int],
    root_support: Union[str, Dict[int, float]] = "v2",
    exponent: float = 0.5,
) -> Dict[str, Union[int, float, List[float]]]:
    """
    Analyze a pitch-class set using the root-finding model of Parncutt (1988).

    Parameters
    ----------
    chord : List[int]
        A list of MIDI pitches representing a chord.
    root_support : Union[str, Dict[int, float]], optional
        Identifies the root support weights to use. "v1" uses the original weights
        from Parncutt (1988), "v2" uses the updated weights from Parncutt (2006),
        by default "v2".
    exponent : float, optional
        Exponent to be used when computing root ambiguities, by default 0.5.

    Returns
    -------
    Dict[str, Union[int, float, List[float]]]
        A dictionary with three values:
        - root: the estimated chord root (integer)
        - root_ambiguity: the root ambiguity (float)
        - pc_weight: a 12-dimensional vector of weights by pitch class

    Examples
    --------
    >>> result = parn88([0, 4, 7])
    >>> result["root"]
    0
    >>> result["root_ambiguity"]
    1.871
    >>> result = parn88([0, 4, 7, 10], root_support="v1")
    >>> result["root"]
    0
    >>> result["root_ambiguity"]
    2.139
    """
    if len(chord) == 0:
        raise ValueError("Chord must contain at least one pitch")

    # Convert chord to pitch class set
    pc_set = set([pitch % 12 for pitch in chord])

    # Get root support weights
    if isinstance(root_support, str):
        if root_support not in ROOT_SUPPORT_WEIGHTS:
            raise ValueError(f"Unknown root support version: {root_support}")
        root_support = ROOT_SUPPORT_WEIGHTS[root_support]

    # Encode pitch class set
    encoded_pc_set = encode_pc_set(list(pc_set))

    # Calculate weights for each pitch class
    pc_weights = [pc_weight(pc, encoded_pc_set, root_support) for pc in range(12)]

    # Find the root
    root = pc_weights.index(max(pc_weights))

    # Calculate root ambiguity
    root_ambiguity = get_root_ambiguity(pc_weights, exponent)

    return {"root": root, "root_ambiguity": root_ambiguity, "pc_weight": pc_weights}


def root(
    chord: List[int],
    root_support: Union[str, Dict[int, float]] = "v2",
    exponent: float = 0.5,
) -> int:
    """
    Estimate the root of a chord using Parncutt's 1988 model.
    Calls parn88 under the hood.

    Parameters
    ----------
    chord : List[int]
        A list of MIDI pitches representing a chord.
    root_support : Union[str, Dict[int, float]], optional
        Identifies the root support weights to use, by default "v2".
    exponent : float, optional
        Exponent to be used when computing root ambiguities, by default 0.5.

    Returns
    -------
    int
        The pitch class of the estimated root.

    Examples
    --------
    >>> root([0, 4, 7])
    0
    >>> root([0, 4, 7, 10])
    0
    >>> root([2, 5, 9])
    2
    >>> root([1, 4, 9])
    9
    """
    return parn88(chord, root_support, exponent)["root"]


def root_ambiguity(
    chord: List[int],
    root_support: Union[str, Dict[int, float]] = "v2",
    exponent: float = 0.5,
) -> float:
    """
    Estimate the root ambiguity of a chord using Parncutt's 1988 model.
    Calls parn88 under the hood.

    Parameters
    ----------
    chord : List[int]
        A list of MIDI pitches representing a chord.
    root_support : Union[str, Dict[int, float]], optional
        Identifies the root support weights to use, by default "v2".
    exponent : float, optional
        Exponent to be used when computing root ambiguities, by default 0.5.

    Returns
    -------
    float
        The root ambiguity.

    Examples
    --------
    >>> root_ambiguity([0, 4, 7])
    1.871
    >>> root_ambiguity([0, 4, 7, 10], root_support="v1")
    2.139
    >>> root_ambiguity([0, 3, 6]) > root_ambiguity([0, 4, 7])
    True
    """
    return parn88(chord, root_support, exponent)["root_ambiguity"]


def visualize_root_weights(
    chord: List[int],
    root_support: Union[str, Dict[int, float]] = "v2",
    title: Optional[str] = None,
) -> None:
    """
    Visualize the root weights for a chord.

    Parameters
    ----------
    chord : List[int]
        A list of MIDI pitches representing a chord.
    root_support : Union[str, Dict[int, float]], optional
        Identifies the root support weights to use, by default "v2".
    title : Optional[str], optional
        Title for the plot, by default None.

    Examples
    --------
    >>> visualize_root_weights([0, 4, 7])
    """
    result = parn88(chord, root_support)
    weights = result["pc_weight"]
    root_pc = result["root"]

    # Create a bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(12), weights)

    # Highlight the root
    bars[root_pc].set_color("red")

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
        chord_str = ", ".join(str(pc) for pc in sorted(set(p % 12 for p in chord)))
        title = f"Root Weights for Chord [{chord_str}]"
    plt.title(title)

    # Add grid
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Show the plot
    plt.tight_layout()
    plt.show()


def encode_pc_set(pc_set: List[int]) -> List[int]:
    """
    Encode a pitch class set as a binary vector.

    Parameters
    ----------
    pc_set : List[int]
        A list of pitch classes (integers from 0 to 11).

    Returns
    -------
    List[int]
        A binary vector of length 12, where 1 indicates the presence of a pitch class.

    Examples
    --------
    >>> encode_pc_set([0, 4, 7])
    [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]
    >>> encode_pc_set([0])
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    >>> encode_pc_set([])
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    """
    result = [0] * 12
    for pc in pc_set:
        result[pc] = 1
    return result


def pc_weight(pc: int, pc_set: List[int], root_support: Dict[int, float]) -> float:
    """
    Calculate the weight for a given pitch class.

    Parameters
    ----------
    pc : int
        The pitch class to calculate the weight for.
    pc_set : List[int]
        A binary vector representing a pitch class set.
    root_support : Dict[int, float]
        A dictionary mapping intervals to root support weights.

    Returns
    -------
    float
        The weight for the given pitch class.

    Examples
    --------
    >>> v2_weights = {0: 10, 7: 5, 4: 3, 10: 2, 2: 1}
    >>> pc_set = encode_pc_set([0, 4, 7])
    >>> pc_weight(0, pc_set, v2_weights)
    18.0
    >>> pc_weight(1, pc_set, v2_weights)
    0.0
    """
    weight = 0.0
    for interval, support_weight in root_support.items():
        target_pc = (pc + interval) % 12
        if pc_set[target_pc] == 1:
            weight += support_weight
    return weight


def get_root_ambiguity(pc_weights: List[float], exponent: float = 0.5) -> float:
    """
    Calculate the root ambiguity of a pitch class set.

    Parameters
    ----------
    pc_weights : List[float]
        A list of weights for each pitch class.
    exponent : float, optional
        The exponent to use when computing root ambiguities, by default 0.5.

    Returns
    -------
    float
        The root ambiguity.
    """
    max_weight = max(pc_weights)
    if max_weight == 0:
        return 0.0
    return sum(w / max_weight for w in pc_weights) ** exponent
