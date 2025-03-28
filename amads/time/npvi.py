"""
Normalized Pairwise Variability Index (nPVI).

This module provides functions for calculating the normalized pairwise variability
index (nPVI), a measure used in the analysis of rhythmic variability in music.

References:
    - Daniele, J. R., & Patel, A. D. (2013). An Empirical Study of Historical Patterns
      in Musical Rhythm. Music Perception, 31(1), 10-18.
      https://doi.org/10.1525/mp.2013.31.1.10

    - Condit-Schultz, N. (2019). Deconstructing the nPVI: A Methodological Critique of
      the Normalized Pairwise Variability Index as Applied to Music. Music Perception,
      36(3), 300–313. https://doi.org/10.1525/mp.2019.36.3.300

Author:
    Huw Cheston (2025)
"""

from typing import Iterable

__author__ = "Huw Cheston"


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

    # Explicitly check to make sure we have enough elements to calculate nPVI
    if len(durations) < 2:
        raise ValueError(
            f"Must have at least 2 durations to calculate nPVI, but got {len(durations)} duration(s)"
        )
    # Also raise an error if any of the durations are zero or below
    if any(d <= 0.0 for d in durations):
        raise ValueError(f"All durations must be positive, but got {durations}!")

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
