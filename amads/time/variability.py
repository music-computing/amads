"""
Time variability.

This module provides various functions for calculating rhythmic variability in music,
including the normalized pairwise variability index (nPVI) and variations thereof.

<small>**Author**: Huw Cheston (2025), Mark Gotham (2026)</small>

References
----------

- Daniele, J. R., & Patel, A. D. (2013). An Empirical Study of
    Historical Patterns in Musical Rhythm. *Music Perception*, 31(1), 10-18.
      https://doi.org/10.1525/mp.2013.31.1.10

- Condit-Schultz, N. (2019). Deconstructing the nPVI: A Methodological
    Critique of the Normalized Pairwise Variability Index as Applied to
    Music. *Music Perception*,
    36(3), 300–313. https://doi.org/10.1525/mp.2019.36.3.300

- VanHandel, L., & Song, T. (2010). The role of meter in compositional style
    in 19th-century French and German art song. *Journal of New Music
    Research*, 39, 1–11. https://doi.org/10.1080/09298211003642498
"""

import math
from typing import Sequence

from amads.core.basics import Part, Score

__authors__ = ["Huw Cheston", "Mark Gotham"]


# Absolute tolerance used when comparing durations for isochrony.
# Assumes durations are expressed in seconds; adjust if using other units.
TINY = 1e-4


def _validate_inputs(
    durations: Sequence[float], _kind: str = "durations", _min: float = 2
) -> list[float]:
    """
    Validates an input sequence (usually durations) and raises errors if:
    - insufficient number of elements,
    - any element (duration) is zero or negative.

    Converts the input to a list and returns that list for validated processing.
    """
    durations = list(durations)

    if len(durations) < _min:
        raise ValueError(
            f"Must have at least {_min} {_kind}, but got {len(durations)} duration(s)"
        )

    if any(d <= 0.0 for d in durations):
        raise ValueError(f"All {_kind} must be positive, but got {durations}!")

    return durations


def _normalized_pairwise_calculation(a_ioi: float, c_ioi: float) -> float:
    """Normalized pairwise calculation for an antecedent and consequent IOI, as in Condit-Schultz (2019)."""
    return 200 * abs((a_ioi - c_ioi) / (a_ioi + c_ioi))


def normalized_pairwise_variability_index(
    durations: Sequence[float],
) -> float:
    r"""
    Calculates the normalised pairwise variability index (nPVI).

    The nPVI is a measure of variability between successive elements
    in a sequence. The equation is:

    $\text{nPVI} = \frac{100}{m-1} \times \sum\limits_{k=1}^{m-1}
    \left| \frac{d_k - d_{k+1}}{\frac{d_k + d_{k+1}}{2}} \right|$

    where $m$ is the number of intervals, and $d_k$ is the duration
    of the $k^{th}$ interval.

    A completely regular stream of equal durations returns 0 variability.
    High difference between successive items returns a high nPVI value
    irrespective of other (e.g., metrical) considerations.

    Note: this formula is equivalent to the mean of the nPC values
    (see :func:`normalized_pairwise_calculation`), since both
    `abs((k - k1) / ((k + k1) / 2)) * 100` and
    `200 * abs((k - k1) / (k + k1))` simplify to the same expression.

    Parameters
    ----------
    durations : Sequence[float]
        the durations to analyse

    Returns
    -------
    float
        the extracted nPVI value.

    Examples
    -------

    A completely regular stream of equal durations returns 0 variability.

    >>> normalized_pairwise_variability_index([1., 1., 1., 1.])
    0.0

    This example is from Daniele & Patel (2013, Appendix).

    >>> durs = [1., 1/2, 1/2, 1., 1/2, 1/2, 1/3, 1/3, 1/3, 2., 1/3, 1/3, 1/3, 1/3, 1/3, 1/3, 3/2, 1., 1/2]
    >>> x = normalized_pairwise_variability_index(durations=durs)
    >>> round(x, 1)
    42.2

    These next examples are from Condit-Schultz's 2019 critique (Figure 2).
    The only difference is the value of 62.9 (as distinct from the paper's 62.8).
    which is due to floating point rounding.

    >>> round(normalized_pairwise_variability_index([0.25, 0.25, 0.25, 0.25, 1., 0.25, 0.25, 0.25, 0.25, 1.]), 1)
    40.0

    >>> round(normalized_pairwise_variability_index([0.25, 0.25, 0.5, 1., 0.25, 0.25, 0.5, 1.]), 1)
    55.2

    >>> round(normalized_pairwise_variability_index([0.5, 0.25, 0.25, 1., 0.5, 0.25, 0.25, 1.]), 1)
    62.9

    >>> round(normalized_pairwise_variability_index([2, 1, 2, 1]), 2)
    66.67

    >>> round(normalized_pairwise_variability_index([0.5, 1, 2, 1, 0.5]), 2)
    66.67

    >>> round(normalized_pairwise_variability_index([2, 1, 0.5, 1, 0.5, 0.25]), 2)
    66.67
    """

    durations = _validate_inputs(durations)
    numerator = (
        sum(
            [
                abs((k - k1) / ((k + k1) / 2))
                for (k, k1) in zip(durations, durations[1:])
            ]
        )
        * 100
    )
    denominator = len(durations) - 1
    return numerator / denominator


def normalized_pairwise_calculation(durations: Sequence[float]) -> list[float]:
    r"""
    Calculates the normalized pairwise calculation (nPC) for a list of
    durations, as defined by Condit-Schultz (2019).

    The nPVI is equivalent to the arithmetic mean of a set of nPC values.
    The equation for nPC can be written as:

    $\text{nPC} = 200 * \biggl{|} \frac{\text{antecedent IOI} -
                                        \text{consequent IOI}}
        {\text{antecedent IOI} + \text{consequent IOI}} \biggr{|}$

    Parameters
    ----------
    durations : Sequence[float]
        the durations to analyse

    Returns
    -------
    Sequence[float]
        the extracted nPC value(s) for every pair of
        antecedent-consequent durations

    Examples
    --------

    From Condit-Schultz (2019) figure 3.

    >>> normalized_pairwise_calculation([1, 15])
    [175.0]

    >>> normalized_pairwise_calculation([1, 7])
    [150.0]

    >>> round(normalized_pairwise_calculation([1, 5])[0], 2)
    133.33

    >>> normalized_pairwise_calculation([1, 4])
    [120.0]

    >>> normalized_pairwise_calculation([1, 3])
    [100.0]

    >>> round(normalized_pairwise_calculation([1, 2])[0], 2)
    66.67

    >>> normalized_pairwise_calculation([2, 3])
    [40.0]

    >>> normalized_pairwise_calculation([1, 1])
    [0.0]

    """

    durations = _validate_inputs(durations)
    return [
        _normalized_pairwise_calculation(a_ioi, c_ioi)
        for a_ioi, c_ioi in zip(durations, durations[1:])
    ]


def isochrony_proportion(
    durations: Sequence[float],
) -> float:
    r"""
    Calculates the isochrony proportion (IsoP) for a list of durations, as defined in Condit-Schultz (2019):
    "by iterating over every pair of successive IOIs in a rhythm,
    counting the pairs that are identical,
    and dividing this count by the total number of pairs (one less than the total number of IOIs)."

    Condit-Schultz 2019 demonstrates that the IsoP accounts for a large degree of the variance in the nPVI.

    Parameters
    ----------
    durations (Sequence[float]): the durations to analyse

    Returns
    -------
    float: the extracted IsoP value

    Examples
    --------
    >>> isochrony_proportion([1, 1, 2, 2, 1, 0.5])
    0.4

    """

    durations = _validate_inputs(durations)
    isochronous = 0
    # Iterate over every pair of successive IOIs in a rhythm
    for a1, a2 in zip(durations, durations[1:]):
        # If both IOIs are the same
        if math.isclose(a1, a2, abs_tol=TINY):
            # Increase the counter by one
            isochronous += 1
    # Divide the counter by the total number of pairs (one less than the total number of IOIs)
    denominator = len(durations) - 1
    return isochronous / denominator


def pairwise_anisochronous_contrast_index(
    durations: Sequence[float],
) -> float:
    r"""
    Calculates the pairwise anisochronous contrast index (pACI) for a list of durations.

    Defined in Condit-Schultz (2019), the pACI is equivalent to the nPVI,
    except that it "factors out" isochronous pairs of IOIs.
    This means that it is sensitive to changes in the frequencies of IOIs pairs such as 2:1, 3:1, without
    being "overwhelmed by isochronous pairs" (1:1).

    Parameters
    ----------
    durations (Sequence[float]): the durations to analyse

    Returns
    -------
    float: the extracted pACI value

    """

    durations = _validate_inputs(durations)
    all_npcs = []
    # Iterate over successive IOIs
    for a1, a2 in zip(durations, durations[1:]):
        # If the two IOIs are NOT isochronous
        if not math.isclose(a1, a2, abs_tol=TINY):
            # Calculate the nPC for this pair of durations
            npc = _normalized_pairwise_calculation(a1, a2)
            all_npcs.append(npc)
    # Raise errors as required
    if len(all_npcs) == 0:
        raise ValueError(
            "No non-isochronous pairs were found, cannot calculate pACI."
        )
    # Return the average
    return sum(all_npcs) / len(all_npcs)


def phrase_normalized_pairwise_variability_index(
    durations: Sequence[float],
    phrase_boundaries: Sequence[float],
) -> float:
    r"""
    Calculates the phrase-normalized pairwise variability index (pnPVI), as defined by VanHandel & Song (2010).

    The pnNPVI calculates the nPVI, ignoring cases where pairs of IOIs straddle a phrase boundary.
    To do so, we also need a list of times for where those phrase boundaries fall.

    Phrase boundaries are compared against the onset of each pair's first IOI and the
    onset of the note following the pair (i.e., `counter` to `counter + a1 + a2`).

    Parameters
    ----------
    durations (Sequence[float]): the durations to analyse
        phrase_boundaries (Sequence[float]): the phrase boundaries to analyse

    Returns
    -------
    float: the extracted pnNPVI value

    """

    # Validate all inputs
    durations = _validate_inputs(durations)
    phrase_boundaries = _validate_inputs(
        phrase_boundaries, _kind="phrase boundaries", _min=1
    )  # need at least one phrase boundary
    # We use the "counter" to keep track of where we are in the phrase
    counter = 0
    all_npcs = []
    # Iterate over pairs of IOIs
    for a1, a2 in zip(durations, durations[1:]):
        # This is where we "end" the current boundary: add both IOIs to the counter
        end_pos = counter + a1 + a2
        # If we're not straddling any of the phrase boundaries
        if not any([counter <= pb <= end_pos for pb in phrase_boundaries]):
            # Calculate the nPC
            npc = _normalized_pairwise_calculation(a1, a2)
            all_npcs.append(npc)
        # Add the first IOI to the counter to move forwards in time for the next pair
        counter += a1
    # Raise errors as required
    if len(all_npcs) == 0:
        raise ValueError(
            "All pairs of IOIs cross phrase boundaries, cannot calculate pnNPVI."
        )
    # Return the average of all nPC values
    return sum(all_npcs) / len(all_npcs)


def _iois_from_notes(notes: list) -> list[float]:
    """
    Return inter-onset intervals (IOIs) from a sorted list of Notes, dropping zeros.
    NOte that use of this function may change with possible changes to on-score storage of IOI values.
    """
    diffs = [notes[i].onset - notes[i - 1].onset for i in range(1, len(notes))]
    return [d for d in diffs if d > 0]


def score_npvi(score: Score) -> float:
    """
    Calculate the nPVI for a score using the resultant rhythm
    produced by the combination of all parts (i.e., a `flattened' score).

    Notes from all parts are merged into a single onset-sorted sequence.
    and duplicate onsets (e.g., simultaneous notes in a chord) are removed before
    computing inter-onset intervals.

    Parameters
    ----------
    score : Score
        The AMADS score to analyse.

    Returns
    -------
    float
        The nPVI of the resultant IOI sequence.

    See Also
    --------
    score_npvi_by_part : Per-part nPVI for polyphonic scores.
    normalized_pairwise_variability_index : The underlying nPVI calculation.
    """
    notes = score.get_sorted_notes()
    iois = _iois_from_notes(notes)
    return normalized_pairwise_variability_index(iois)


def score_npvi_by_part(score: Score) -> dict[str, float]:
    """
    Calculate the nPVI separately for each part in a score.

    Requires every part to be monophonic (no overlapping notes / chords).
    Raises `ValueError` if `score.parts_are_monophonic()` is `False`
    because the correct way to handle those cases is unclear here
    (as opposed to in `score_npvi` which is perfectly clear).

    Each part's IOI sequence is computed independently.
    The returned dict is keyed by each
    `Part` object's `name` attribute (or `"Part <count>"` if unnamed),
    and the values are the per-part nPVI floats.

    .. note::
        If you want a single combined value, consider :func:`score_npvi`
        (resultant rhythm) or take a weighted mean of the returned values,
        weighting by the `"n_ioi_pairs"` entry for each part.

    Parameters
    ----------
    score : Score
        The AMADS score to analyse.

    Returns
    -------
    dict[str, float]
        Mapping of part name → nPVI value.

    Raises
    ------
    ValueError
        If any part of the score contains chords (overlapping notes).

    See Also
    --------
    score_npvi : Resultant-rhythm nPVI for any score.
    normalized_pairwise_variability_index : The underlying nPVI calculation.
    """
    if not score.parts_are_monophonic():
        raise ValueError(
            "score_npvi_by_part requires all parts to be monophonic, "
            "but this score contains chords or overlapping notes. "
            "Use score_npvi() for polyphonic scores."
        )
    results = {}
    for n, part in enumerate(score.find_all(Part)):
        name = getattr(part, "name", None) or f"Part {n + 1}"
        notes = part.get_sorted_notes()
        iois = _iois_from_notes(notes)
        results[name] = normalized_pairwise_variability_index(iois)
    return results
