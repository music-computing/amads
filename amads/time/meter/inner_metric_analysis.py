"""
An Efficient Algorithm for Computing an Inner Metric Analysis (IMA) of Music
Created by Brian Bemman based on algorithms provided in two forthcoming papers, Bemman, B. et al. (forthcoming a,b)

Computes an Inner Metric Analysis of music (Volk, 2008), which consists of the following two steps:

1. enumerating all local meters in a strictly increasing sequence of integer onsets; and
2. computing the metric and spectral weight profiles from all enumerated local meters.

- A local meter is a maximal arithmetic progression of at least three onset pulses that is not contained in any other.

- A metric weight profile consists of a weight for each onset, l'^p, summed over all local meter pulses coinciding at
this onset, where l' is the length (minus 1) of a given local meter and p is a weighting parameter (default 2).

- A spectral weight profile consists of the same weight, l'^p, computed for each time point in an underlying metrical
grid and summed over all local meter pulses and extensions coinciding at this time point.

Example:

    onsets: [0, 1, 2, 3, 4, 5, 7]
    minimum local meter length: l = 2
    weighting parameter: p = 2

    local meters: [0, 1, 2, 3, 4, 5], [1, 3, 5, 7], [1, 4, 7]
    metric weights: [25, 38, 25, 34, 29, 34, 0, 13]
    spectral weights: [25, 38, 25, 34, 29, 34, 25, 38]

Usage:

    Compute an Inner Metric Analysis with a minimum local meter length, l = 2, and weighting parameter, p = 2, and
    return the metric and spectral weight profiles but not the local meters found (if any).

    analysis = compute_inner_metric_analysis(onsets, 2, 2, False)

    print(analysis.metric_weights)
    print(analysis.spectral_weights)
    print(analysis.local_meters)

    'analysis.local_meters' will be non-empty only if return_local_meters is True and local meters have been found. Each
    local meter is encoded as a tuple, (start_onset, period, length). For example, the local meter, [1, 3, 5, 7], above
    is (start_onset=1, period=2, length=3).

A note on performance:

For the vast majority of individual musical works (i.e., those having fewer than 5,000 onsets), one can expect a running
time not exceeding a few seconds. For significantly larger works, such as Richard Wagner's Das Rheingold, having roughly
32,000 onsets, one can expect a running time of a few minutes. Should these times prove inadequate for your application
or larger sequences need to be run, a considerably more performant C++ version is available at
https://github.com/brianm2b. In either case, depending on your machine, memory usage may become prohibitive for
sequences of any significantly greater length.

<small>**Author**: Brian Bemman</small>
"""

__author__ = "Brian Bemman"

from array import array
from typing import NamedTuple


class LM(NamedTuple):
    """Small, class for storing local meters (LM)"""

    start_onset: int
    period: int
    length: int  # number of pulses minus 1


class IMA(NamedTuple):
    """Small, class for storing an Inner Metric Analysis (IMA)"""

    metric_weights: array
    spectral_weights: array
    local_meters: list[LM]


def check_input_is_well_formed(
    onsets: list, l_param: int, p_weight_param: int
) -> list[int]:
    """Checks for well-formed input parameters and preprocesses the input sequence of onsets.

    Parameters:
    - onsets: strictly increasing sequence of non-negative integer onsets
    - l_param: minimum local meter length, l (default 2)
    - p_weight_param: weighting parameter, p, for controlling the influence of each local meter (default 2)

    Returns:
    - onsets: strictly increasing sequence of non-negative integer onsets
    """
    assert 3 <= len(
        onsets
    ), "Number of onsets is less than three, so no local meters possible"
    assert l_param < len(
        onsets
    ), "Number of onsets must be greater than the minimum requested local meter length, l"
    assert all(
        (
            isinstance(onset, int)
            or (isinstance(onset, float) and onset.is_integer())
        )
        for onset in onsets
    ), "Onsets must be whole numbers"
    assert 0 <= min(onsets), "Onsets must be non-negative"
    assert len(onsets) == len(set(onsets)), "Onsets must be distinct"
    assert all(
        onsets[i] < onsets[i + 1] for i in range(len(onsets) - 1)
    ), "Onsets must be strictly increasing"
    assert (
        2 <= l_param < len(onsets)
    ), "Minimum local meter length, l, must be 2 <= l < len(onsets). Default is l = 2"
    assert p_weight_param in (
        0,
        1,
        2,
    ), "Weighting parameter, p, must be equal to 0, 1, or 2. Default is p = 2"
    assert 0 == p_weight_param or 1 == p_weight_param or 2 == p_weight_param, (
        "Weighting parameter, p, must be equal "
        "to 0, 1, or 2. Default is p = 2"
    )
    return [
        int(onset) for onset in onsets
    ]  # ensure onsets are of type int for indexing


def pairwise_arithmetic_progression_lengths(
    onsets: list[int],
) -> tuple[array, list[int], array, int, list[int]]:
    """Computes maximal lengths of all (i < j) arithmetic progressions using dynamic programming (Erickson 1999).

    Parameters:
    - onsets: strictly increasing sequence of non-negative integer onsets

    Returns:
    - ap_length_table: upper-right triangle of table containing lengths of all (i<j) arithmetic progressions in onsets
    - discovered_periods: all distinct periods belonging to all arithmetic progression triples found in onsets
    - max_period: largest discovered period from all arithmetic progression triples found in onsets

    Note that this is a modification of an algorithm by Erickson (1999) for computing the longest arithmetic progression
    """
    n = len(onsets)
    max_onset = onsets[-1]
    min_onset = onsets[0]
    discovered_periods: list[int] = []
    max_period = 0
    ap_length_table = array("i", [2]) * ((n * (n - 1)) // 2)
    period_indices = array("i", [-1]) * (((max_onset - min_onset) // 2) + 1)
    row_base = [0] * n
    for i in range(0, n):
        row_base[i] = i * (n - 1) - (i * (i - 1)) // 2

    for j in range(n - 2, 0, -1):  # j from n-2 down to 1 (inclusive)
        i = j - 1
        k = j + 1
        second_term_sum = 2 * onsets[j]
        row_base_j = row_base[j]
        while i >= 0 and k < n:
            first_third_term_sum = onsets[i] + onsets[k]
            if (
                first_third_term_sum < second_term_sum
            ):  # right-side term too small
                k += 1
                continue
            if (
                first_third_term_sum > second_term_sum
            ):  # left-side term too large
                i -= 1
                continue
            # arithmetic triple
            idx_ij = row_base[i] + (j - i - 1)  # linear index of i, j
            idx_jk = row_base_j + (k - j - 1)  # linear index of j, k
            prev_len = ap_length_table[idx_jk]
            updated_len = (prev_len + 1) if (prev_len > 2) else 3
            ap_length_table[idx_ij] = updated_len
            ap_period = onsets[j] - onsets[i]
            if period_indices[ap_period] < 0:  # new period discovered
                period_indices[ap_period] = len(discovered_periods)
                discovered_periods.append(ap_period)
                if ap_period > max_period:
                    max_period = ap_period
            i -= 1
            k += 1
    return (
        ap_length_table,
        discovered_periods,
        period_indices,
        max_period,
        row_base,
    )


def compute_period_cofactors(
    discovered_periods, period_indices, max_period
) -> tuple[list[int], list[int]]:
    """Computes for each discovered period all cofactors from division by its prime factors.

    Parameters:
    - discovered_periods: all distinct periods belonging to all arithmetic progression triples found in onsets
    - period_indices: index in discovered_periods associated to the value of its period
    - max_period: largest discovered period from all arithmetic progression triples found in onsets

    Returns:
    - period_factors: all cofactors from division by its prime factors ordered by discovered_periods
    - factor_indices: starting indices of cofactors in period_factors ordered by discovered_periods (i.e., prefix sum)

    Note that this procedure makes use of Euler's Linear Sieve algorithm.
    """
    smallest_prime_factors = array("i", [0]) * (max_period + 1)  # Euler sieve
    next_distinct = array("i", [0]) * (
        max_period + 1
    )  # index of next distinct prime factor
    primes = []
    for i in range(2, max_period + 1):  # Euler's Linear Sieve procedure
        if smallest_prime_factors[i] == 0:
            smallest_prime_factors[i] = i
            primes.append(i)
            next_distinct[i] = 1
        for p in primes:
            mul = i * p  # multiple of prime
            if mul > max_period:
                break
            smallest_prime_factors[mul] = p
            if p == smallest_prime_factors[i]:
                next_distinct[mul] = next_distinct[i]
                break
            else:
                next_distinct[mul] = i
    period_factors: list[int] = (
        []
    )  # cofactors for each period in discovered_periods (same order)
    factor_indices: list[int] = [
        0
    ]  # index of the first cofactor for each period in discovered_periods
    for (
        period
    ) in (
        discovered_periods
    ):  # compute period cofactors from each distinct prime factor
        idx = period
        while idx > 1:
            cofactor = (
                period // smallest_prime_factors[idx]
            )  # p-free part of period
            if period_indices[cofactor] > -1:
                period_factors.append(cofactor)
            idx = next_distinct[
                idx
            ]  # jump to index of next distinct prime factor
        factor_indices.append(len(period_factors))
    return period_factors, factor_indices


def is_local_meter(
    factor_start_idx: int,
    factor_end_idx: int,
    period_factors: list[int],
    row_periods: list[tuple[int, int]],
    current_row: int,
    ap_start_onset: int,
    ap_end_onset: int,
    period_indices: array,
) -> bool:
    """Determines if a maximal arithmetic progression is a local meter.

    Parameters
    ----------
    - factor_start_idx: index of first factor in period_factors for the period of a maximal arithmetic progressions
    - factor_end_idx: index of first factor in period_factors for the next (i.e., i + 1) period in period_factors
    - period_factors: for the period of a maximal arithmetic progression, all factors from division by its prime factors
    - row_periods: maximal length of each (i < j) arithmetic progression from a given i associated to its period
    - current_row: i-th row in ap_length_table
    - ap_start_onset: first onset of a maximal arithmetic progression
    - ap_end_onset: last onset of a maximal arithmetic progression
    - period_indices: index in discovered_periods associated to the value of its period

    Returns
    -------
    - boolean: indicating whether a maximal arithmetic progression is a local meter
    """
    for idx in range(
        factor_start_idx, factor_end_idx
    ):  # cofactors for ap_period
        cofactor = period_factors[idx]
        cofactor_length, cofactor_row = row_periods[period_indices[cofactor]]
        if (
            cofactor_row == current_row
            and ap_end_onset <= ap_start_onset + cofactor * cofactor_length
        ):
            return False  # existing ap with a cofactor of ap_period at least as long
    return True


def update_weights(
    metric_weights: array,
    spectral_weights: array,
    ap_start_onset: int,
    ap_end_onset: int,
    ap_period: int,
    ap_length: int,
    max_onset: int,
    p_weight_param: int,
):
    """Updates the metric and spectral weight profiles of a musical piece for a given local meter.

    Parameters
    ----------
    - metric_weights: sequence of metric weights, one for each onset of a local meter
    - spectral_weights: sequence of spectral weights, one for each time point of a local meter or extension
    - ap_start_onset: first onset of a local meter
    - ap_end_onset: last onset of a local meter
    - ap_period: period of a local meter
    - ap_length: length minus 1 of a local meter
    - max_onset: greatest onset in onsets
    - p_weight_param: weighting parameter, p, for controlling the influence of each local meter (default 2.0)

    Returns
    -------
    - metric_weights: sequence of metric weights, one for each onset of a local meter
    - spectral_weights: sequence of spectral weights, one for each time point of a local meter or extension
    """
    weight = ap_length**p_weight_param  # l^p weight for this local meter
    time_point = ap_start_onset  # time point in underlying grid
    while time_point <= ap_end_onset:  # local meter (pulses/onsets)
        metric_weights[time_point] += weight
        spectral_weights[time_point] += weight
        time_point += ap_period
    while time_point <= max_onset:  # right side of local meter
        spectral_weights[time_point] += weight
        time_point += ap_period
    time_point = ap_start_onset - ap_period
    while time_point >= max_onset:  # left side of local meter
        spectral_weights[time_point] += weight
        time_point -= ap_period
    return metric_weights, spectral_weights


def compute_inner_metric_analysis(
    onsets: list,
    l_param: int = 2,
    p_weight_param: int = 2,
    return_local_meters: bool = False,
) -> IMA:
    """Computes an Inner Metric Analysis (IMA) of music (Volk 2008).

    Parameters
    ----------
    - onsets: strictly increasing sequence of non-negative integer onsets
    - l_param: minimum local meter length, l (default 2)
    - p_weight_param: weighting parameter, p, for controlling the influence of each local meter (default 2)
    - return_local_meters: boolean indicating whether to store and return all discovered local meters (default False)

    Returns
    -------
    - An IMA object consisting of the following three attributes:
        - metric_weights: sequence of metric weights, one for each onset of a local meter
        - spectral_weights: sequence of spectral weights, one for each time point of a local meter or extension
        - local_meters: all local meters of the form LM(ap_start_onset, period, ap_length) discovered in onsets

    Note that local_meters will be non-empty if 'return_local_meters' is True and local meters have been found

    Example
    -------
    Volk (2008) provides an example with 19 local meters:
    >>> onsets = [0, 1, 2, 6, 8, 9, 10, 14, 16, 17, 18, 22, 24, 25, 26, 30]
    >>> analysis = compute_inner_metric_analysis(onsets, 2, 2, True)
    >>> analysis.metric_weights
    array('i', [17, 13, 65, 0, 0, 0, 57, 0, 25, 21, 65, 0, 0, 0, 57, 0, 33, 21, 65, 0, 0, 0, 57, 0, 25, 13, 65, 0, 0, 0, 57])

    >>> analysis.spectral_weights
    array('i', [17, 13, 65, 4, 4, 4, 61, 4, 29, 25, 69, 8, 12, 8, 69, 8, 45, 29, 77, 12, 24, 12, 77, 16, 45, 25, 89, 20, 32, 16, 89])

    >>> len(analysis.local_meters)
    19

    """
    # check whether onsets are properly formed
    onsets = check_input_is_well_formed(onsets, l_param, p_weight_param)

    # compute maximal lengths of all (i < j) arithmetic progressions
    (
        ap_length_table,
        discovered_periods,
        period_indices,
        max_period,
        row_base,
    ) = pairwise_arithmetic_progression_lengths(onsets)
    # compute (prime factor | period) cofactors for all discovered periods in onsets
    period_factors, factor_indices = compute_period_cofactors(
        discovered_periods, period_indices, max_period
    )

    n = len(onsets)
    max_onset = onsets[-1]
    metric_weights = array("i", [0]) * (max_onset + 1)
    spectral_weights = array("i", [0]) * (max_onset + 1)
    local_meters: list[LM] = []
    row_periods = [
        (0, -1) for _ in range(len(discovered_periods))
    ]  # (ap length, current row) for each period
    indicator_onsets = set(onsets)
    num_of_local_meters = 0

    for i in range(n - 2):  # each row in ap_length_table
        ap_start_onset = onsets[i]
        max_period_in_row = min(
            (max_onset - ap_start_onset) // l_param, max_period
        )  # maximum possible period
        row_start_idx = row_base[i]
        base_offset = row_start_idx - i - 1  # constant offset for row i
        for j in range(i + 1, n - 1):
            ap_period = onsets[j] - ap_start_onset
            if (
                ap_period > max_period_in_row
            ):  # remaining j for this i will be of length 2
                break
            current_idx = base_offset + j  # flat index for (i < j)
            ap_length = ap_length_table[current_idx] - 1  # length minus 1
            if ap_length >= l_param:  # at least length l_param
                period_idx = period_indices[
                    ap_period
                ]  # index in discovered_periods/factor_indices/period_factors
                row_periods[period_idx] = (ap_length, i)
                ap_prev_onset = (
                    ap_start_onset - ap_period
                )  # prior possible onset
                if (
                    ap_prev_onset < 0 or ap_prev_onset not in indicator_onsets
                ):  # new maximal arithmetic progression
                    ap_end_onset = ap_start_onset + ap_period * ap_length
                    factor_start_idx = factor_indices[
                        period_idx
                    ]  # index of first factor of ap_period
                    factor_end_idx = factor_indices[
                        period_idx + 1
                    ]  # index of first factor of next period
                    if is_local_meter(
                        factor_start_idx,
                        factor_end_idx,
                        period_factors,
                        row_periods,
                        i,
                        ap_start_onset,
                        ap_end_onset,
                        period_indices,
                    ):  # local meter found
                        # update metric and spectral weight profiles
                        metric_weights, spectral_weights = update_weights(
                            metric_weights,
                            spectral_weights,
                            ap_start_onset,
                            ap_end_onset,
                            ap_period,
                            ap_length,
                            max_onset,
                            p_weight_param,
                        )
                        num_of_local_meters += 1
                        if return_local_meters:
                            local_meters.append(
                                LM(ap_start_onset, ap_period, ap_length)
                            )
                        continue
                ap_length_table[current_idx] = 0  # not a local meter

    return IMA(metric_weights, spectral_weights, local_meters)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
