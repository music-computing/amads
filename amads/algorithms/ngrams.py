from collections import Counter
from typing import Dict, Union

import numpy as np


class NGramCounter:

    def __init__(self):
        self.ngram_counts = None  # Initialize ngram_counts as None

    def count_ngrams(self, tokens: list, method: Union[str, int]) -> Dict:
        """Count all n-grams from a list of tokens.

        Parameters
        ----------
        tokens : list
            List of tokens to process (will be flattened if nested)
        method : str or int
            If "all", count n-grams of all lengths.
            If int, count n-grams of that specific length.

        Returns
        -------
        dict
            Counts of each n-gram
        """
        # Flatten nested list structure
        flat_tokens = (
            [token for sublist in tokens for token in sublist]
            if tokens and isinstance(tokens[0], list)
            else tokens
        )

        if not flat_tokens:
            return {}

        if method == "all":
            n_values = range(1, len(flat_tokens) + 1)
        else:
            if not isinstance(method, int):
                raise TypeError(f"method must be 'all' or int, got {type(method)}")
            if method < 1:
                raise ValueError(f"n-gram length {method} is less than 1")
            if method > len(flat_tokens):
                raise ValueError(
                    f"n-gram length {method} is larger than token sequence "
                    f"length {len(flat_tokens)}"
                )

            n_values = [method]

        counts = {}
        for n in n_values:
            for i in range(len(flat_tokens) - n + 1):
                # Create hashable n-gram
                ngram = tuple(str(token) for token in flat_tokens[i : i + n])
                counts[ngram] = counts.get(ngram, 0) + 1
        self.ngram_counts = counts
        return self.ngram_counts

    @property
    def yules_k(self) -> float:
        """Calculate Yule's K statistic for a given n-gram count dictionary.

        Yule's K is a measure of the rate at which words are repeated in a given text.
        In the context of music, it measures the rate at which m-types are repeated in a given
        melody or corpus, according to the formula:

        :math:`K = 1 / |n| * 1000 * (sum(V(m,N) * m^2) - N) / (N * N)`
        where:
        - :math:`|n|` is the number of different n-gram lengths
        - :math:`V(m,N)` is the number of m-types with frequency :math:`m` with :math:`N` m-tokens
        - :math:`N` is the total number of m-tokens in the melody
        - :math:`m` is the index for the frequency class in the frequency distribution

        Returns
        -------
        float
            Mean Yule's K statistic across all n-gram lengths.
            Returns 0 for empty input.
        """
        if self.ngram_counts is None:
            raise ValueError(
                "N-gram counts have not been calculated. Call get_mtype_counts() first."
            )

        n_lengths = len(self.ngram_counts)
        freq_spec = Counter(self.ngram_counts.values())
        n = sum(self.ngram_counts.values())
        if n == 0:
            return 0.0

        # Calculate sum(vm * m²) where vm is frequency of value m
        vm_m2_sum = sum(freq * (count * count) for count, freq in freq_spec.items())

        # Calculate K with scaling factor of 1000
        k = (1 / n_lengths) * (1000 * (vm_m2_sum - n) / (n * n))

        return k

    @property
    def simpsons_d(self) -> float:
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
        """
        if self.ngram_counts is None:
            raise ValueError(
                "N-gram counts have not been calculated. Call get_mtype_counts() first."
            )

        n_lengths = len(self.ngram_counts)
        n = sum(self.ngram_counts.values())
        if n == 0:
            return 0.0

        # Get counts
        count_values = list(self.ngram_counts.values())
        total_tokens = sum(count_values)

        if total_tokens <= 1:
            return 0.0

        # Calculate D using the formula: 1 / |n| * sum(n_i * (n_i - 1)) / (total_tokens * (total_tokens - 1))
        d = (
            (1 / n_lengths)
            * sum(n * (n - 1) for n in count_values)
            / (total_tokens * (total_tokens - 1))
        )

        return float(d)

    @property
    def sichels_s(self) -> float:
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
        """
        if self.ngram_counts is None:
            raise ValueError(
                "N-gram counts have not been calculated. Call get_mtype_counts() first."
            )

        n_lengths = len(self.ngram_counts)
        n = sum(self.ngram_counts.values())
        if n == 0:
            return 0.0

        # Count how many n-grams occur exactly twice
        doubles = sum(1 for count in self.ngram_counts.values() if count == 2)

        # Get total_types (total number of unique n-grams)
        total_types = len(self.ngram_counts)

        if total_types == 0:
            return 0.0

        # Calculate S value using 1/|n| * V(2,N)/V(N)
        s = (1.0 / n_lengths) * (float(doubles) / total_types)

        return float(s)

    @property
    def honores_h(self) -> float:
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

        Returns
        -------
        float
            Mean Honore's H value across n-gram lengths.
            Returns 0.0 for empty input.
        """
        if self.ngram_counts is None:
            raise ValueError(
                "N-gram counts have not been calculated. Call get_mtype_counts() first."
            )

        n = sum(self.ngram_counts.values())
        if n == 0:
            return 0.0

        # Get hapax_count (number of hapax legomena)
        hapax_count = sum(1 for count in self.ngram_counts.values() if count == 1)

        # Get total_types
        total_types = len(self.ngram_counts)

        # Handle edge cases
        if total_types == 0 or hapax_count == 0 or hapax_count == total_types:
            return 0.0

        # Calculate H value
        h = 100.0 * (np.log(n) / (1.01 - (float(hapax_count) / total_types)))

        return float(h)

    @property
    def mean_entropy(self) -> float:
        """Compute entropy of m-type n-gram distribution.
        Calulates the mean Shannon entropy of the m-type n-gram distribution.
        This is defined as:
        :math:`H = -sum(p(x) * log2(p(x)))`
        where:
        - :math:`p(x)` is the probability of the i-th m-type
        - :math:`N` is the total number of m-types in the melody
        - :math:`H` is the Shannon entropy

        Returns
        -------
        float
            Mean normalized entropy value across n-gram lengths.
            Returns 0.0 for empty input.
        """
        if self.ngram_counts is None:
            raise ValueError(
                "N-gram counts have not been calculated. Call get_mtype_counts() first."
            )

        total_tokens = sum(self.ngram_counts.values())
        if total_tokens <= 1:
            return 0.0

        # Calculate probabilities
        probabilities = [count / total_tokens for count in self.ngram_counts.values()]

        # Calculate entropy
        entropy = -np.sum(probabilities * np.log2(probabilities))

        # Normalize entropy
        entropy_norm = entropy / np.log2(total_tokens)

        return float(entropy_norm)

    @property
    def mean_productivity(self) -> float:
        """Compute mean productivity of m-type n-gram distribution.

        Mean productivity is defined as the mean over all lengths of the number of m-types
        occurring only once divided by the total number of m-tokens. The m-types occurring
        only once in a text are known as hapax legomena.

        mean_productivity = sum(V1(N)/|n|) where V1(N) is the number of types occurring once

        Returns
        -------
        float
            Mean productivity value across n-gram lengths.
            Returns 0.0 for empty input.
        """
        if self.ngram_counts is None:
            raise ValueError(
                "N-gram counts have not been calculated. Call get_mtype_counts() first."
            )

        total_tokens = sum(self.ngram_counts.values())
        if total_tokens == 0:
            return 0.0

        # Count hapax_count (types occurring once)
        hapax_count = sum(1 for count in self.ngram_counts.values() if count == 1)

        # Calculate productivity
        productivity = hapax_count / total_tokens

        return float(productivity)
