from collections import Counter

import numpy as np


def yules_k(ngram_counts: dict[tuple, int]) -> float:
    """Calculates mean Yule's K statistic over m-type n-grams.
    Yule's K is a measure of the rate at which words are repeated in a given text.
    In the context of music, it measures the rate at which m-types are repeated in a given melody,
    according to the formula:

    :math:`K = 1000 * (sum(V(m,N) * m²) - N) / (N * N)`
    where:
    - :math:`V(m,N)` is the number of m-types with frequency :math:`m` in a melody with :math:`N` m-tokens
    - :math:`N` is the total number of m-tokens in the melody
    - :math:`m` is the index for the frequency class in the frequency distribution

    Parameters
    ----------
    ngram_counts : dict[tuple, int]
        Dictionary of n-gram counts

    Returns
    -------
    float
        Mean Yule's K statistic across all n-gram lengths.
        Returns 0 for empty input.
    Examples
    --------
    >>> from amads.algorithms.mtype_tokenizer import FantasticTokenizer
    >>> from amads.core.basics import Score
    >>> # Sample melody [60, 62, 64, 66, 64, 62, 60] with equal note durations
    >>> score = Score.from_melody([60, 62, 64, 66, 64, 62, 60], durations=1.0)
    >>> tokenizer = FantasticTokenizer()
    >>> high_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> yules_k(high_repetition_counts)  # High K indicates more repetition
    22.68...
    >>> # Sample melody with low repetition [60, 61, 62, 68, 59, 71] with different durations
    >>> score = Score.from_melody([60, 61, 62, 68, 59, 71], durations=[0.25, 0.5, 0.75, 0.35, 0.15, 0.25])
    >>> tokenizer = FantasticTokenizer()
    >>> low_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> yules_k(low_repetition_counts)  # Low K indicates less repetition
    8.88...
    >>> # Empty input
    >>> yules_k({})
    0.0
    """
    if not ngram_counts:
        return 0.0

    k_values = []

    # Get frequency of frequencies
    freq_spec = Counter(ngram_counts.values())

    # Calculate total_tokens (total tokens)
    total_tokens = sum(ngram_counts.values())
    if total_tokens == 0:
        return 0.0

    # Calculate sum(vm * m²) where vm is frequency of value m
    vm_m2_sum = sum(freq * (count * count) for count, freq in freq_spec.items())

    # Calculate K with scaling factor of 1000
    k = 1000 * (vm_m2_sum - total_tokens) / (total_tokens * total_tokens)
    k_values.append(k)

    return float(np.mean(k_values)) if k_values else 0.0


def simpsons_d(ngram_counts: dict[tuple, int]) -> float:
    """Compute mean Simpson's D diversity index over m-type n-grams.
    Simpson's D is also a measure of the diversity of m-types in a melody,
    and mathematically resembles the definition of Yule's K:
    :math:`D = 1 - sum(n_i * (n_i - 1)) / (N * (N - 1))`
    where:
    - :math:`n_i` is the frequency of the i-th m-type
    - :math:`N` is the total number of m-types in the melody
    - :math:`D` is the Simpson's D diversity index

    Parameters
    ----------
    ngram_counts : dict[tuple, int]
        Dictionary of n-gram counts

    Returns
    -------
    float
        Mean Simpson's D value across n-gram lengths.
        Returns 0.0 for empty input.

    Examples
    --------
    >>> from amads.algorithms.mtype_tokenizer import FantasticTokenizer
    >>> from amads.core.basics import Score
    >>> # Sample melody with high repetition
    >>> score = Score.from_melody([60, 62, 64, 62, 60], durations=1.0)
    >>> tokenizer = FantasticTokenizer()
    >>> high_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> simpsons_d(high_repetition_counts)  # Higher D indicates less diversity
    0.022...
    >>> # Sample melody with low repetition
    >>> score = Score.from_melody([60, 61, 62, 68, 59, 71], durations=[0.25, 0.5, 0.75, 0.35, 0.15, 0.25])
    >>> tokenizer = FantasticTokenizer()
    >>> low_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> simpsons_d(low_repetition_counts)  # Lower D indicates more diversity
    0.00952...
    >>> # Empty input
    >>> simpsons_d({})
    0.0
    """
    if not ngram_counts:
        return 0.0

    d_values = []

    # Get counts
    count_values = list(ngram_counts.values())
    total_tokens = sum(count_values)  # total_tokens holds total tokens

    if total_tokens <= 1:
        return 0.0

    # Calculate D using the formula: sum(n_i * (n_i - 1)) / (total_tokens * (total_tokens - 1))
    d = sum(n * (n - 1) for n in count_values) / (total_tokens * (total_tokens - 1))
    d_values.append(d)

    return float(np.mean(d_values)) if d_values else 0.0


def sichels_s(ngram_counts: dict[tuple, int]) -> float:
    """Compute Sichel's S statistic over m-type n-grams.
    Sichel's S is a measure of the proportion of m-types that occur exactly twice in a melody,
    based on alinguistic phenomenon: that words occuring twice with regards to vocabulary size
    appear to be constant for a given text.
    It is defined as:
    :math:`S = V(2,N)/(|n| * V(N))`
    where:
    - :math:`V(2,N)` is the number of m-types that occur exactly twice in the melody
    - :math:`V(N)` is the total number of m-types in the melody
    - :math:`|n|` is the number of n-gram lengths considered

    Parameters
    ----------
    ngram_counts : dict[tuple, int]
        Dictionary of n-gram counts

    Returns
    -------
    float
        Mean Sichel's S value across n-gram lengths.
        Returns 0.0 for empty input.

    Examples
    --------
    >>> from amads.algorithms.mtype_tokenizer import FantasticTokenizer
    >>> from amads.core.basics import Score
    >>> # Sample melody with high repetition
    >>> score = Score.from_melody([60, 62, 64, 62, 60], durations=1.0)
    >>> tokenizer = FantasticTokenizer()
    >>> high_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> sichels_s(high_repetition_counts)  # Higher S indicates more doubles
    0.111...
    >>> # Sample melody with low repetition
    >>> score = Score.from_melody([60, 61, 62, 68, 59, 71], durations=[0.25, 0.5, 0.75, 0.35, 0.15, 0.25])
    >>> tokenizer = FantasticTokenizer()
    >>> low_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> sichels_s(low_repetition_counts)  # Lower S indicates fewer doubles
    0.0714...
    >>> # Empty input
    >>> sichels_s({})
    0.0
    """
    if not ngram_counts:
        return 0.0

    s_values = []

    # Count how many n-grams occur exactly twice
    doubles = sum(1 for count in ngram_counts.values() if count == 2)

    # Get total_types (total number of unique n-grams)
    total_types = len(ngram_counts)

    if total_types == 0:
        return 0.0

    # Calculate S value
    s = float(doubles) / total_types
    s_values.append(s)

    return float(np.mean(s_values)) if s_values else 0.0


def honores_h(ngram_counts: dict[tuple, int]) -> float:
    """Compute Honore's H statistic over m-type n-grams.
    Honore's H is based on the assumption that the proportion of ngrams
    occuring exactly once is logarithmically related to the total number
    of ngrams in the melody.
    It is defined as:
    :math:`H = 100 * (log(N) / (1.01 - (V1/V)))`
    where:
    - :math:`N` is the total number of m-types in the melody
    - :math:`V1` is the number of m-types that occur exactly once
    - :math:`V` is the total number of m-types in the melody
    Parameters
    ----------
    ngram_counts : dict[tuple, int]
        Dictionary of n-gram counts

    Returns
    -------
    float
        Mean Honore's H value across n-gram lengths.
        Returns 0.0 for empty input.

    Examples
    --------
    >>> from amads.algorithms.mtype_tokenizer import FantasticTokenizer
    >>> from amads.core.basics import Score
    >>> # Sample melody with high repetition
    >>> score = Score.from_melody([60, 62, 64, 62, 60], durations=1.0)
    >>> tokenizer = FantasticTokenizer()
    >>> high_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> honores_h(high_repetition_counts)  # Lower H indicates fewer unique MTypes
    1901.217...
    >>> # Sample melody with low repetition
    >>> score = Score.from_melody([60, 61, 62, 68, 59, 71], durations=[0.25, 0.5, 0.75, 0.35, 0.15, 0.25])
    >>> tokenizer = FantasticTokenizer()
    >>> low_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> honores_h(low_repetition_counts)  # Higher H indicates more unique MTypes
    3325.68...
    >>> # Empty input
    >>> honores_h({})
    0.0
    """
    if not ngram_counts:
        return 0.0

    h_values = []

    # Get total_tokens (total tokens)
    total_tokens = sum(ngram_counts.values())

    # Get hapax_count (number of hapax legomena)
    hapax_count = sum(1 for count in ngram_counts.values() if count == 1)

    # Get total_types (total types)
    total_types = len(ngram_counts)

    # Handle edge cases
    if total_types == 0 or hapax_count == 0 or hapax_count == total_types:
        return 0.0

    # Calculate H value using total_tokens, hapax_count, and total_types
    h = 100.0 * (np.log(total_tokens) / (1.01 - (float(hapax_count) / total_types)))
    h_values.append(h)

    return float(np.mean(h_values)) if h_values else 0.0


def mean_entropy(ngram_counts: dict[tuple, int]) -> float:
    """Compute entropy of m-type n-gram distribution.
    Calulates the mean Shannon entropy of the m-type n-gram distribution.
    This is defined as:
    :math:`H = -sum(p(x) * log2(p(x)))`
    where:
    - :math:`p(x)` is the probability of the i-th m-type
    - :math:`N` is the total number of m-types in the melody
    - :math:`H` is the Shannon entropy


    Parameters
    ----------
    ngram_counts : dict[tuple, int]
        Dictionary of n-gram counts

    Returns
    -------
    float
        Mean normalized entropy value across n-gram lengths.
        Returns 0.0 for empty input.

    Examples
    --------
    >>> from amads.algorithms.mtype_tokenizer import FantasticTokenizer
    >>> from amads.core.basics import Score
    >>> # Sample melody with high repetition
    >>> score = Score.from_melody([60, 62, 64, 62, 60], durations=1.0)
    >>> tokenizer = FantasticTokenizer()
    >>> high_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> mean_entropy(high_repetition_counts)  # Lower entropy indicates less randomness
    0.939...
    >>> # Sample melody with low repetition
    >>> score = Score.from_melody([60, 61, 62, 68, 59, 71], durations=[0.25, 0.5, 0.75, 0.35, 0.15, 0.25])
    >>> tokenizer = FantasticTokenizer()
    >>> low_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> mean_entropy(low_repetition_counts)  # Higher entropy indicates more randomness
    0.966...
    >>> # Empty input
    >>> mean_entropy({})
    0.0
    """
    if not ngram_counts:
        return 0.0

    entropy_values = []

    # Get total_tokens
    total_tokens = sum(ngram_counts.values())

    if total_tokens <= 1:
        return 0.0

    # Calculate probabilities using total_tokens
    probabilities = [count / total_tokens for count in ngram_counts.values()]

    # Calculate entropy using probabilities
    entropy = -np.sum(probabilities * np.log2(probabilities))

    # Normalize entropy by log(total_tokens)
    entropy_norm = entropy / np.log2(total_tokens)
    entropy_values.append(entropy_norm)

    return float(np.mean(entropy_values)) if entropy_values else 0.0


def mean_productivity(ngram_counts: dict[tuple, int]) -> float:
    """Compute mean productivity of m-type n-gram distribution.

    Mean productivity is defined as the mean over all lengths of the number of m-types
    occurring only once divided by the total number of m-tokens. The m-types occurring
    only once in a text are known as hapax legomena.

    mean_productivity = sum(V1(N)/|n|) where V1(N) is the number of types occurring once

    Parameters
    ----------
    ngram_counts : dict[tuple, int]
        Dictionary mapping n-gram tuples to their counts

    Returns
    -------
    float
        Mean productivity value across n-gram lengths.
        Returns 0.0 for empty input.

    Examples
    --------
    >>> from amads.algorithms.mtype_tokenizer import FantasticTokenizer
    >>> from amads.core.basics import Score
    >>> # Sample melody with high repetition
    >>> score = Score.from_melody([60, 62, 64, 62, 60], durations=1.0)
    >>> tokenizer = FantasticTokenizer()
    >>> high_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> mean_productivity(high_repetition_counts)  # Lower productivity indicates less hapax legomena
    0.8
    >>> # Sample melody with low repetition
    >>> score = Score.from_melody([60, 61, 62, 68, 59, 71], durations=[0.25, 0.5, 0.75, 0.35, 0.15, 0.25])
    >>> tokenizer = FantasticTokenizer()
    >>> low_repetition_counts = tokenizer.get_mtype_counts(score, method="all")
    >>> mean_productivity(low_repetition_counts)  # Higher productivity indicates more hapax legomena
    0.9
    >>> # Empty input
    >>> mean_productivity({})
    0.0
    """
    if not ngram_counts:
        return 0.0

    productivity_values = []

    # Get total_tokens
    total_tokens = sum(ngram_counts.values())

    if total_tokens == 0:
        return 0.0

    # Count hapax_count (types occurring once)
    hapax_count = sum(1 for count in ngram_counts.values() if count == 1)

    # Calculate productivity using hapax_count and total_tokens
    productivity = hapax_count / total_tokens
    productivity_values.append(productivity)

    return float(np.mean(productivity_values)) if productivity_values else 0.0
