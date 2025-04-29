"""
Time variability.

This module provides various functions for calculating rhythmic variability in music,
including the normalized pairwise variability index (nPVI) and variations thereof.

References:
    - Daniele, J. R., & Patel, A. D. (2013). An Empirical Study of Historical Patterns
      in Musical Rhythm. Music Perception, 31(1), 10-18.
      https://doi.org/10.1525/mp.2013.31.1.10

    - Condit-Schultz, N. (2019). Deconstructing the nPVI: A Methodological Critique of
      the Normalized Pairwise Variability Index as Applied to Music. Music Perception,
      36(3), 300–313. https://doi.org/10.1525/mp.2019.36.3.300

    - VanHandel, L., & Song, T. (2010). The role of meter in compositional style in
      19th-century French and German art song. Journal of New Music Research, 39, 1–11.
      https://doi.org/10.1080/09298211003642498

Author:
    Huw Cheston (2025)
"""

import math
from typing import Iterable

__author__ = "Huw Cheston"


TINY = 1e-4


def _validate_inputs(
    durations: Iterable[float], _kind: str = "durations", _min: float = 2
) -> None:
    """Validates an input list (usually durations) and raises errors as required"""
    # Explicitly check to make sure we have enough elements
    if len(durations) < _min:
        raise ValueError(
            f"Must have at least {_min} {_kind}, but got {len(durations)} duration(s)"
        )
    # Also raise an error if any of the durations are zero or below
    if any(d <= 0.0 for d in durations):
        raise ValueError(f"All {_kind} must be positive, but got {durations}!")


def _normalized_pairwise_calculation(a_ioi: float, c_ioi: float) -> float:
    """Normalized pairwise calculation for an antecedent and consequent IOI, as in Condit-Schultz (2019)."""
    return 200 * abs((a_ioi - c_ioi) / (a_ioi + c_ioi))


# flake8: noqa: W605
def normalized_pairwise_variability_index(
    durations: Iterable[float],
) -> float:
    r"""
    Extracts the normalised pairwise variability index (nPVI).

    The nPVI is a measure of variability between successive elements in a sequence, commonly used
    in music analysis to quantify rhythmic variability. The equation is:

    .. math::

       \text{nPVI} = \frac{100}{m-1} \times \sum\limits_{k=1}^{m-1}
       \left| \frac{d_k - d_{k+1}}{\frac{d_k + d_{k+1}}{2}} \right|

    where :math:`m` is the number of intervals, and :math:`d_k` is the duration of the :math:`k^{th}` interval.

    Args:
        durations (Iterable[float]): the durations to analyse

    Returns:
        float: the extracted nPVI value.

    Examples:
        The first example is taken from Condit-Schultz (2019, Figure 1).

        >>> durs = [1., 1., 1., 1.]
        >>> normalized_pairwise_variability_index(durations=durs)
        0.

        The second example is Daniele & Patel (2013, Appendix).

        >>> durs = [1., 1/2, 1/2, 1., 1/2, 1/2, 1/3, 1/3, 1/3, 2., 1/3, 1/3, 1/3, 1/3, 1/3, 1/3, 3/2, 1., 1/2]
        >>> x = normalized_pairwise_variability_index(durations=durs)
        >>> round(x, 1)
        42.2
    """

    _validate_inputs(durations)
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


def normalized_pairwise_calculation(durations: Iterable[float]) -> Iterable[float]:
    r"""
    Extracts the normalized pairwise calculation (nPC) for a list of durations, as defined by Condit-Schultz (2019).

    The nPVI is equivalent to the arithmetic mean of a set of nPC values. The equation for nPC can be written as:

    .. math::
        \text{nPC} = 200 * \biggl{|} \frac{\text{antecedent IOI} - \text{consequent IOI}}
        {\text{antecedent IOI} + \text{consequent IOI}} \biggr{|}

    Args:
        durations (Iterable[float]): the durations to analyse

    Returns:
        Iterable[float]: the extracted nPC value(s) for every pair of antecedent-consequent durations

    """

    _validate_inputs(durations)
    return [
        _normalized_pairwise_calculation(a_ioi, c_ioi)
        for a_ioi, c_ioi in zip(durations, durations[1:])
    ]


def isochrony_proportion(
    durations: Iterable[float],
) -> float:
    r"""
    Calculates the isochrony proportion (IsoP) for a list of durations, as defined in Condit-Schultz (2019).

    The IsoP is calculated simply by iterating over every pair of duration values, counting the pairs that are
    identical, and dividing this count by the total number of pairs. In previous research (e.g., Condit-Schultz 2019),
    the IsoP has shown to account for a large degree of the variance contained in the nPVI.

    Args:
        durations (Iterable[float]): the durations to analyse

    Returns:
        float: the extracted IsoP value

    """

    _validate_inputs(durations)
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
    durations: Iterable[float],
) -> float:
    r"""
    Calculates the pairwise anisochronous contrast index (pACI) for a list of durations.

    Defined in Condit-Schultz(2019), the pACI is functionally equivalent to the nPVI, but ignores isochronous pairs of
    IOIs. This means that it is sensitive to changes in the frequencies of pairs of IOIs such as 2:1, 3:1, without
    being overwhelmbed by isochronous pairs (1:1).

    Args:
        durations (Iterable[float]): the durations to analyse

    Returns:
        float: the extracted pACI value

    """

    _validate_inputs(durations)
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
        raise ValueError("No non-isochronous pairs were found, cannot calculate pACI!")
    # Return the average
    return sum(all_npcs) / len(all_npcs)


def phrase_normalized_pairwise_variability_index(
    durations: Iterable[float],
    phrase_boundaries: Iterable[float],
) -> float:
    r"""
    Calculates the phrase-normalized pairwise variability index (pnPVI), as defined by VanHandel & Song (2010).

    The pnNPVI simply calculates the nPVI, but *ignores* cases where pairs of IOIs straddle phrase boundaries. To do
    so, we also need a list of phrase boundary times, which should increase linearly (i.e., they are not duration
    values, but closer to onsets).

    Args:
        durations (Iterable[float]): the durations to analyse
        phrase_boundaries (Iterable[float]): the phrase boundaries to analyse

    Returns:
        float: the extracted pnNPVI value

    """

    # Validate all inputs
    _validate_inputs(durations)
    _validate_inputs(
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
            "All pairs of IOIs cross phrase boundaries, cannot calculate pnNPVI!"
        )
    # Return the average of all nPC values
    return sum(all_npcs) / len(all_npcs)
