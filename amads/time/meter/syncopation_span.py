"""
This module sets out a new "IOI span" measure of syncopation.
(Note that some alternative, existing measures of syncopation from the literature are available in
`amads.time.meter.syncopation`.).

Syncopation is defined here by the interaction between
1) a pair of consecutive onsets and
2) the surrounding hierarchy, particularly wrt positions during the span between the two onsets.

Here, a note event is syncopated if
1) it starts at a lower-weight metrical position and
2) the next onset occurs only after positions of strictly higher weight.

That is, a potential syncopation is set up and opportunities for resolving are not taken (missed/avoided).

That much is relatively clear.
More complex and debatable is the scoring system to implement this.
In the absense of empirical testing, some plausible starting point preliminaries.
Currently, the score for a single onset pair (A, B) is calculated with two components:
- count: number of higher-weight positions traversed in the span (A, B)
- gap: difference between the maximum weight traversed and A's own weight

These two are combined and weighted by a decay factor to differentiate
resolution by a nearby onset counts vs a distant one.

The total syncopation score for an onset (here `A`)
is the sum of decayed pair scores for events that are
- during the span (ending with event `B`)
- also during `max_lookahead` onsets (if B is further off).

All positions are expressed as absolute quarter-lengths from the start of the
first metrical cycle.
The metrical cycle wraps automatically (position mod `cycle_length`).

Dependencies
------------
amads.time.meter.representations


<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


import math
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

from amads.time.meter.representations import StartTimeHierarchy

# ---------------------------------------------------------------------------

# Data classes


@dataclass
class PairSyncopation:
    """
    Syncopation contribution from a single onset pair (A, B).

    Attributes
    ----------
    onset_a : float
        Absolute position of the first onset.
    onset_b : float
        Absolute position of the second onset.
    weight_a : float
        Metrical weight at onset_a (coincident pulse count by default).
    max_weight_traversed : float
        Highest weight of any metrical position strictly inside (onset_a, onset_b).
    count : int
        Number of positions inside (onset_a, onset_b) with weight > weight_a.
    gap : float
        max_weight_traversed - weight_a  (0 if no higher position traversed).
    raw_score : float
        count * gap  (0 if not syncopated).
    decay : float
        Decay factor applied at this lookahead distance.
    score : float
        raw_score * decay.
    """

    onset_a: float
    onset_b: float
    weight_a: float
    max_weight_traversed: float
    count: int
    gap: float
    raw_score: float
    decay: float
    score: float


@dataclass
class OnsetSyncopation:
    """
    Aggregated syncopation score for a single onset, across all lookahead pairs.

    Attributes
    ----------
    onset : float
        Absolute position of this onset.
    weight : float
        Metrical weight at this position.
    pairs : list[PairSyncopation]
        One entry per lookahead onset considered.
    score : float
        Sum of pair scores.
    """

    onset: float
    weight: int
    pairs: list[PairSyncopation] = field(default_factory=list)
    score: float = 0.0


@dataclass
class SyncopationAnalysis:
    """
    Full syncopation analysis for a sequence of onsets.

    Attributes
    ----------
    onset_results : list[OnsetSyncopation]
        Per-onset breakdown.
    total_score : float
        Sum of all onset scores.
    hierarchy : StartTimeHierarchy
        The metrical hierarchy used.
    """

    onset_results: list[OnsetSyncopation]
    total_score: float
    hierarchy: StartTimeHierarchy


# ---------------------------------------------------------------------------

# Helpers


def _build_weight_map(
    hierarchy: StartTimeHierarchy,
    granular_pulse: float,
) -> dict[float, int]:
    """
    Build a mapping {position -> weight} for every grid point in the cycle.

    Weight is the coincident pulse count at that position,
    optionally scaled by level_weights (applied in `weight_at_position`).

    Parameters
    ----------
    hierarchy : StartTimeHierarchy
    granular_pulse : float
        Resolution of the finest grid to consider.

    Returns
    -------
    dict mapping rounded position -> raw coincident count.

    Examples
    --------
    >>> from amads.time.meter.representations import PulseLengths, StartTimeHierarchy
    >>> pl = PulseLengths([4, 2, 1], cycle_length=4)
    >>> sh = StartTimeHierarchy(pl.to_start_hierarchy())
    >>> wm = _build_weight_map(sh, granular_pulse=1.0)
    >>> wm[0.0]
    3
    >>> wm[1.0]
    1
    >>> wm[2.0]
    2
    """
    cycle_length = hierarchy.cycle_length
    counts = hierarchy.coincident_pulse_list(granular_pulse)
    steps = int(cycle_length / granular_pulse)
    return {round(granular_pulse * i, 4): counts[i] for i in range(steps)}


def weight_at_position(
    position: float,
    hierarchy: StartTimeHierarchy,
    weight_map: dict[float, int],
    level_weights: Optional[list[float]] = None,
) -> float:
    """
    Return the (optionally scaled) metrical weight at an absolute position.

    The position is reduced modulo the cycle length before lookup.
    If the position does not fall on a grid point, weight 0 is returned.

    Note that this may be merged/refactored with MetricalSplitter.

    Parameters
    ----------
    position : float
        Absolute quarter-length position.
    hierarchy : StartTimeHierarchy
    weight_map : dict
        Pre-built by `_build_weight_map`.
    level_weights : list[float], optional
        If provided, must have one entry per coincident-pulse-count level.
        The raw count is used as an index into this list (1-based).
        Defaults to the raw count (rank = 1 per level).

    Returns
    -------
    float
        Scaled weight (or raw int count if level_weights is None).

    Examples
    --------
    >>> from amads.time.meter.representations import PulseLengths, StartTimeHierarchy
    >>> pl = PulseLengths([4, 2, 1], cycle_length=4)
    >>> sh = StartTimeHierarchy(pl.to_start_hierarchy())
    >>> wm = _build_weight_map(sh, granular_pulse=1.0)
    >>> weight_at_position(0.0, sh, wm)
    3
    >>> weight_at_position(2.0, sh, wm)
    2
    >>> weight_at_position(1.0, sh, wm)
    1
    >>> weight_at_position(0.5, sh, wm)  # off-grid
    0
    """
    cycle_length = hierarchy.cycle_length
    pos = round(position % cycle_length, 4)
    raw = weight_map.get(pos, 0)
    if level_weights is None or raw == 0:
        return raw
    idx = min(raw - 1, len(level_weights) - 1)
    return level_weights[idx]


def _positions_in_span(
    onset_a: float,
    onset_b: float,
    weight_map: dict[float, int],
    cycle_length: float,
) -> list[tuple[float, int]]:
    """
    Return all (position, raw_weight) pairs strictly inside the open interval
    (onset_a, onset_b), with cycle wrapping.

    NOTE: this may merge / refactor with `MetricalSplitter`.

    Parameters
    ----------
    onset_a, onset_b : float
        Absolute positions; onset_b > onset_a.
    weight_map : dict
        Maps cycle-relative positions to raw weights.
    cycle_length : float

    Returns
    -------
    list of (position, weight) tuples, in order.

    Examples
    --------
    >>> from amads.time.meter.representations import PulseLengths, StartTimeHierarchy
    >>> pl = PulseLengths([4, 2, 1], cycle_length=4)
    >>> sh = StartTimeHierarchy(pl.to_start_hierarchy())
    >>> wm = _build_weight_map(sh, granular_pulse=1.0)
    >>> _positions_in_span(0.0, 3.0, wm, 4.0)
    [(1.0, 1), (2.0, 2)]
    >>> _positions_in_span(3.0, 5.0, wm, 4.0)
    [(4.0, 3)]
    """
    result = []
    seen: set[float] = set()
    span = onset_b - onset_a
    n_cycles = math.ceil(span / cycle_length) + 1
    base_cycle = int(onset_a // cycle_length)

    for c in range(n_cycles):
        for rel_pos, w in weight_map.items():
            p = round(rel_pos + (base_cycle + c) * cycle_length, 4)
            if onset_a < p < onset_b and p not in seen:
                seen.add(p)
                result.append((p, w))

    result.sort()
    return result


def syncopation_for_pair(
    onset_a: float,
    onset_b: float,
    hierarchy: StartTimeHierarchy,
    weight_map: dict[float, int],
    level_weights: Optional[list[float]] = None,
    decay: float = 1.0,
) -> PairSyncopation:
    """
    Compute the syncopation contribution for a single onset pair (A, B).

    A note starting at onset_a and sustained until onset_b is syncopated if
    the span (onset_a, onset_b) contains metrical positions of strictly higher
    weight than onset_a itself.

    Parameters
    ----------
    onset_a, onset_b : float
        Absolute quarter-length positions; onset_b > onset_a.
    hierarchy : StartTimeHierarchy
    weight_map : dict
        Pre-built by `_build_weight_map`.
    level_weights : list[float], optional
        Custom importance scaling per weight level.
    decay : float
        Decay factor for this lookahead distance. Defaults to 1.0.

    Returns
    -------
    PairSyncopation

    Examples
    --------
    >>> from amads.time.meter.representations import PulseLengths, StartTimeHierarchy
    >>> pl = PulseLengths([4, 2, 1], cycle_length=4)
    >>> sh = StartTimeHierarchy(pl.to_start_hierarchy())
    >>> wm = _build_weight_map(sh, granular_pulse=1.0)

    Not syncopated: starts on the downbeat (highest weight).
    >>> pair = syncopation_for_pair(0.0, 2.0, sh, wm)
    >>> pair.score
    0.0

    Syncopated: starts on weight-1 position, crosses weight-2 position.
    >>> pair = syncopation_for_pair(1.0, 3.0, sh, wm)
    >>> pair.gap
    1
    >>> pair.count
    1
    >>> pair.score
    1.0

    Strongly syncopated: starts on weight-1, crosses weight-3 (downbeat).
    >>> pair = syncopation_for_pair(3.0, 5.0, sh, wm)
    >>> pair.gap
    2
    >>> pair.count
    1
    >>> pair.score
    2.0
    """
    w_a = weight_at_position(onset_a, hierarchy, weight_map, level_weights)
    inner = _positions_in_span(
        onset_a, onset_b, weight_map, hierarchy.cycle_length
    )

    higher = [(p, w) for p, w in inner if w > w_a]
    count = len(higher)
    max_w = max((w for _, w in higher), default=w_a)
    gap = max_w - w_a
    raw_score = count * gap
    score = raw_score * decay

    return PairSyncopation(
        onset_a=onset_a,
        onset_b=onset_b,
        weight_a=w_a,
        max_weight_traversed=max_w,
        count=count,
        gap=gap,
        raw_score=raw_score,
        decay=decay,
        score=score,
    )


# ---------------------------------------------------------------------------

# Default decay function


def default_decay(n: int) -> float:
    """
    Default decay function: 1/n where n is the lookahead index (1-based).

    n=1 is the immediately following onset.
    This received the full (maximum) weight as the first opportunity to resolve.
    n=2 is the onset after that (half weight), etc.

    Examples
    --------
    >>> default_decay(1)
    1.0
    >>> default_decay(2)
    0.5
    >>> default_decay(4)
    0.25
    """
    return 1.0 / n


# ---------------------------------------------------------------------------

# Top-level analysis


def analyse(
    onsets: list[float],
    hierarchy: StartTimeHierarchy,
    granular_pulse: float,
    level_weights: Optional[list[float]] = None,
    decay_fn: Optional[Callable[[int], float]] = None,
    max_lookahead: int = 1,
) -> SyncopationAnalysis:
    """
    Analyse syncopation across a sequence of onsets against a metrical hierarchy.

    For each onset A, the function looks ahead at the next `max_lookahead` onsets
    (B, C, ...) and computes a decayed syncopation score for each pair (A, B),
    (A, C), etc.  The onset's total score is the sum of these pair scores.

    Parameters
    ----------
    onsets : list[float]
        Absolute quarter-length positions of note onsets, in order.
    hierarchy : StartTimeHierarchy
        The metrical hierarchy against which to analyse.
    granular_pulse : float
        Resolution of the metrical grid (e.g. 0.5 for eighth notes).
        Must divide the cycle length evenly.
    level_weights : list[float], optional
        Custom importance per weight level (index 0 = weight 1).
        Defaults to raw coincident pulse count (rank weighting).
    decay_fn : callable, optional
        Function mapping lookahead index n (1-based) to a decay scalar.
        Defaults to `default_decay` (1/n).
    max_lookahead : int
        Number of subsequent onsets to consider for each onset A.
        Defaults to 1 (immediate successor only).

    Returns
    -------
    SyncopationAnalysis

    Examples
    --------
    >>> from amads.time.meter.representations import PulseLengths, StartTimeHierarchy
    >>> pl = PulseLengths([4, 2, 1], cycle_length=4)
    >>> sh = StartTimeHierarchy(pl.to_start_hierarchy())

    Simple case: four quarter notes.  The onset at 1.0 (weight 1) resolves at
    2.0 with nothing between — not syncopated at max_lookahead=1.  With
    max_lookahead=2 it also considers pair (1.0, 3.0) which crosses weight-2
    at position 2.0, syncopated with decay 1/2.
    >>> result = analyse([0.0, 1.0, 2.0, 3.0], sh, granular_pulse=1.0, max_lookahead=2)
    >>> result.onset_results[1].score  # onset at 1.0: gap=1 * decay=0.5
    0.5
    >>> result.onset_results[0].score  # onset at 0.0, highest weight
    0.0
    """
    if decay_fn is None:
        decay_fn = default_decay

    weight_map = _build_weight_map(hierarchy, granular_pulse)

    onset_results: list[OnsetSyncopation] = []

    for i, onset_a in enumerate(onsets):
        w_a = weight_at_position(onset_a, hierarchy, weight_map, level_weights)
        os = OnsetSyncopation(onset=onset_a, weight=w_a)

        for n in range(1, max_lookahead + 1):
            j = i + n
            if j >= len(onsets):
                break
            onset_b = onsets[j]
            decay = decay_fn(n)
            pair = syncopation_for_pair(
                onset_a, onset_b, hierarchy, weight_map, level_weights, decay
            )
            os.pairs.append(pair)
            os.score += pair.score

        onset_results.append(os)

    total_score = sum(os.score for os in onset_results)
    return SyncopationAnalysis(
        onset_results=onset_results,
        total_score=total_score,
        hierarchy=hierarchy,
    )


# ---------------------------------------------------------------------------

# Heatmap: all pairwise transitions on the granular grid


def transition_heatmap(
    hierarchy: StartTimeHierarchy,
    granular_pulse: float,
    level_weights: Optional[list[float]] = None,
) -> tuple[list[float], list[list[float]]]:
    """
    Compute syncopation scores for all ordered pairs of grid positions (A, B).

    The upper triangle (j > i) scores pairs within one cycle, where B follows
    A directly.  The lower triangle (j < i) scores the wrap-around case: A is
    near the end of the cycle and B is the corresponding position in the next
    cycle, so the IOI is still at most one full cycle length.  The diagonal
    (j == i) is always 0.0 (zero IOI, undefined).

    Parameters
    ----------
    hierarchy : StartTimeHierarchy
    granular_pulse : float
        Grid resolution; determines the set of positions considered.
    level_weights : list[float], optional

    Returns
    -------
    positions : list[float]
        The grid positions (row/column labels).
    matrix : list[list[float]]
        matrix[i][j] is the syncopation score for onset at positions[i]
        resolving at positions[j].  Diagonal entries are 0.0.

    Examples
    --------
    >>> from amads.time.meter.representations import PulseLengths, StartTimeHierarchy
    >>> pl = PulseLengths([4, 2, 1], cycle_length=4)
    >>> sh = StartTimeHierarchy(pl.to_start_hierarchy())
    >>> positions, matrix = transition_heatmap(sh, granular_pulse=1.0)
    >>> positions
    [0.0, 1.0, 2.0, 3.0]
    >>> matrix[2][3]  # upper: pos 2 -> pos 3, nothing higher between: not syncopated
    0.0
    >>> matrix[1][3]  # upper: pos 1 -> pos 3, crosses weight-2 at pos 2
    1.0
    >>> matrix[3][1]  # lower/wrap: pos 3 -> pos 1 next cycle, crosses downbeat (weight 3)
    2.0
    """
    weight_map = _build_weight_map(hierarchy, granular_pulse)
    positions = sorted(weight_map.keys())
    cycle_length = hierarchy.cycle_length
    n = len(positions)
    matrix = [[0.0] * n for _ in range(n)]

    for i, pos_a in enumerate(positions):
        for j, pos_b in enumerate(positions):
            if j == i:
                continue
            if j > i:
                # within-cycle: B follows A directly
                onset_b = pos_b
            else:
                # wrap-around: B is in the next cycle
                onset_b = round(pos_b + cycle_length, 4)
            pair = syncopation_for_pair(
                pos_a, onset_b, hierarchy, weight_map, level_weights, decay=1.0
            )
            matrix[i][j] = pair.score

    return positions, matrix


try:
    from matplotlib.colors import LinearSegmentedColormap as _LSC

    SYNCMAP = _LSC.from_list(
        "sync", ["#fffae6", "#fac44b", "#ef6c00", "#b01e00", "#500000"]
    )
except ImportError:
    SYNCMAP = "YlOrRd"  # fallback if matplotlib is absent at import time


def plot_transition_heatmap(  # noqa: C901  (complexity acceptable here)
    hierarchy: StartTimeHierarchy,
    granular_pulse: float,
    level_weights: Optional[list[float]] = None,
    mask_lower: bool = False,
    vmax: Optional[float] = None,
    title: str = "Syncopation Transition Heatmap",
    write_not_show: bool = False,
) -> Tuple[plt.figure, plt.axes]:
    """
    Plot the syncopation transition heatmap using matplotlib.

    Each cell (i, j) shows the syncopation score for an onset pair
    starting at grid position i and ending at position j.

    The upper triangle (j > i) scores pairs within one cycle.

    The lower triangle (j < i) scores the wrap-around case:
    onset A is nearer-the end of the cycle than B so the span goes from
    A via cycle end to B within the next cycle
    (IOI still <= one full cycle).

    The diagonal (j == i) is always blank.

    Colour scheme made anew in this module.
    Similar to "YlOrRd" but with the zero-end not fully white (some distinction from BG).

    Parameters
    ----------
    hierarchy : StartTimeHierarchy
    granular_pulse : float
    level_weights : list[float], optional
    mask_lower : bool
        If True, mask the lower triangle instead of showing wrap-around scores.
        Defaults to False (show the lower triangle).
    vmax : float, optional
        Colour scale maximum. Defaults to the maximum score in the data,
        computed per plot. Pass an explicit value for cross-meter comparison.
    title : str
        Plot title.
    write_not_show : bool
        If True, write to local directory.
        If False, show (default for use in notebooks)

    Returns
    -------
    fig, ax : matplotlib figure, matplotlib axes
        Displays the plot via matplotlib.
    """
    positions, matrix = transition_heatmap(
        hierarchy, granular_pulse, level_weights
    )
    arr = np.array(matrix, dtype=float)

    # Diagonal is always masked (see docs)
    diag_mask = np.eye(len(positions), dtype=bool)
    if mask_lower:
        display = np.where(np.tril(np.ones_like(arr, dtype=bool)), np.nan, arr)
    else:
        display = np.where(diag_mask, np.nan, arr)

    vmax = vmax if vmax is not None else float(np.nanmax(display))
    vmax = vmax if vmax > 0 else 1.0  # guard against all-zero matrices

    # Weight labels for axis ticks
    weight_map = _build_weight_map(hierarchy, granular_pulse)
    labels = [f"{p}\n(w={weight_map.get(p, 0)})" for p in positions]

    fig, ax = plt.subplots(
        figsize=(max(6, len(positions) * 0.7), max(5, len(positions) * 0.6))
    )

    im = ax.imshow(
        display, cmap=SYNCMAP, aspect="auto", origin="upper", vmin=0, vmax=vmax
    )
    plt.colorbar(im, ax=ax, label="Syncopation score")

    ax.set_xticks(range(len(positions)))
    ax.set_yticks(range(len(positions)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel(
        "Ending onset B  [lower triangle = wrap-around to next cycle]"
        if not mask_lower
        else "Ending onset (B)"
    )
    ax.set_ylabel("Starting onset (A)")
    ax.set_title(title)

    # Annotate all non-masked, non-zero cells
    for i in range(len(positions)):
        for j in range(len(positions)):
            if i != j and arr[i][j] > 0:
                if mask_lower and j <= i:
                    continue
                ax.text(
                    j,
                    i,
                    f"{arr[i][j]:.1f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="black",
                )

    plt.tight_layout()
    if write_not_show:
        plt.savefig("./syncopation_span.pdf")
    else:
        plt.show()
    return fig, ax


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
