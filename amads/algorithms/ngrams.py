from collections import Counter
from typing import Dict, Optional, Union

import numpy as np


class NGramCounter:
    """A stateful n-gram counter that accumulates counts across multiple sequences."""

    def __init__(self):
        """Initialize an empty n-gram counter."""
        self.ngram_counts = {}  # Initialize with empty dictionary instead of None

    def count_ngrams(self, tokens: list, n: Union[int, list, None] = None) -> None:
        """Update n-gram counts from a sequence of tokens.

        Parameters
        ----------
            tokens : list
                List of tokens to process
            n : int, list, or None
            If int, count n-grams of that specific length.
                If list, count n-grams of the specified lengths.
                If None, count n-grams of all possible lengths.
        """
        # Determine n-gram lengths to count
        if n is None:
            n_values = range(1, len(tokens) + 1)
        elif isinstance(n, int):
            if n < 1:
                raise ValueError(f"n-gram length {n} is less than 1")
            if n > len(tokens):
                raise ValueError(
                    f"n-gram length {n} is larger than token sequence "
                    f"length {len(tokens)}"
                )
            n_values = [n]
        else:
            # n is a list
            for val in n:
                if not isinstance(val, int):
                    raise TypeError(f"n-gram lengths must be integers, got {type(val)}")
                if val < 1:
                    raise ValueError(f"n-gram length {val} is less than 1")
                if val > len(tokens):
                    raise ValueError(
                        f"n-gram length {val} is larger than token sequence "
                        f"length {len(tokens)}"
                    )
            n_values = n

        # Count n-grams and update the counter
        for n in n_values:
            for i in range(len(tokens) - n + 1):
                # Create hashable n-gram
                ngram = tuple(str(token) for token in tokens[i : i + n])
                # Update count in the dictionary
                self.ngram_counts[ngram] = self.ngram_counts.get(ngram, 0) + 1

    def reset(self) -> None:
        """Reset the n-gram counter to empty."""
        self.ngram_counts = {}

    def get_counts(self, n: Optional[int] = None) -> Dict:
        """Get the current n-gram counts.

        Parameters
        ----------
        n : int, optional
            If provided, only return counts for n-grams of this length.
            If None, return counts for all n-gram lengths.

        Returns
        -------
        dict
            Dictionary mapping each n-gram to its count
        """
        if n is None:
            return self.ngram_counts.copy()
        return {k: v for k, v in self.ngram_counts.items() if len(k) == n}

    @property
    def yules_k(self) -> float:
        """Calculate Yule's K statistic for the n-gram counts.

        Yule's K is a measure of the rate at which tokens are repeated in a sequence.
        It is calculated according to the formula:

        :math:`K = 1 / |n| * 1000 * (sum(V(m,N) * m^2) - N) / (N * N)`
        where:
        - :math:`|n|` is the number of different n-gram lengths
        - :math:`V(m,N)` is the number of types with frequency :math:`m` with :math:`N` tokens
        - :math:`N` is the total number of tokens in the sequence
        - :math:`m` is the index for the frequency class in the frequency distribution

        Interpretation:
        - Higher K values indicate more repetitive sequences
        - Lower K values indicate more diverse sequences with less repetition
        - K is scaled by 1000 to make values more readable

        Returns
        -------
        float
            Mean Yule's K statistic across all n-gram lengths.
            Raises ValueError for empty input.
        """
        if not self.ngram_counts:
            raise ValueError(
                "N-gram counts have not been calculated. Call count_ngrams() first."
            )

        n_lengths = len(self.ngram_counts)
        freq_spec = Counter(self.ngram_counts.values())
        n = sum(self.ngram_counts.values())
        if n == 0:
            raise ValueError("Cannot calculate Yule's K for empty sequence")

        # Calculate sum(vm * m²) where vm is frequency of value m
        vm_m2_sum = sum(freq * (count * count) for count, freq in freq_spec.items())

        # Calculate K with scaling factor of 1000
        k = (1 / n_lengths) * (1000 * (vm_m2_sum - n) / (n * n))

        return k

    @property
    def simpsons_d(self) -> float:
        """Compute mean Simpson's D diversity index over n-grams. This is closely
        mathematically related to the definition of Yule's K.
        Simpson's D is a measure of diversity in a sequence:
        :math:`D = 1 - sum(n_i * (n_i - 1)) / (N * (N - 1))`
        where:
        - :math:`n_i` is the frequency of the i-th type
        - :math:`N` is the total number of tokens in the sequence
        - :math:`D` is the Simpson's D diversity index

        Interpretation:
        - Higher D values indicate more repetitive sequences where tokens are often repeated
        - Lower D values indicate more diverse sequences with many different tokens

        Returns
        -------
        float
            Mean Simpson's D value across n-gram lengths.
            Raises ValueError for empty input.
        """
        if not self.ngram_counts:
            raise ValueError(
                "N-gram counts have not been calculated. Call count_ngrams() first."
            )

        n_lengths = len(self.ngram_counts)
        n = sum(self.ngram_counts.values())
        if n == 0:
            raise ValueError("Cannot calculate Simpson's D for empty sequence")

        # Get counts
        count_values = list(self.ngram_counts.values())
        total_tokens = sum(count_values)

        if total_tokens <= 1:
            raise ValueError("Cannot calculate Simpson's D for sequence of length <= 1")

        # Calculate D using the formula: 1 / |n| * sum(n_i * (n_i - 1)) / (total_tokens * (total_tokens - 1))
        d = (
            (1 / n_lengths)
            * sum(n * (n - 1) for n in count_values)
            / (total_tokens * (total_tokens - 1))
        )

        return float(d)

    @property
    def sichels_s(self) -> float:
        """Compute Sichel's S statistic over n-grams.
        Sichel's S is a measure of the proportion of token types that occur exactly twice in a sequence.
        It is defined as:
        :math:`S = V(2,N)/(|n| * V(N))`
        where:
        - :math:`V(2,N)` is the number of types that occur exactly twice in the sequence
        - :math:`V(N)` is the total number of types in the sequence
        - :math:`|n|` is the number of n-gram lengths considered

        Interpretation:
        - Higher S values indicate more types occurring exactly twice
        - Lower S values indicate fewer types occurring exactly twice

        Returns
        -------
        float
            Mean Sichel's S value across n-gram lengths.
            Raises ValueError for empty input.
        """
        if not self.ngram_counts:
            raise ValueError(
                "N-gram counts have not been calculated. Call count_ngrams() first."
            )

        n_lengths = len(self.ngram_counts)
        n = sum(self.ngram_counts.values())
        if n == 0:
            raise ValueError("Cannot calculate Sichel's S for empty sequence")

        # Count how many n-grams occur exactly twice
        doubles = sum(1 for count in self.ngram_counts.values() if count == 2)

        # Get total_types (total number of unique n-grams)
        total_types = len(self.ngram_counts)

        if total_types == 0:
            raise ValueError("Cannot calculate Sichel's S when no types exist")

        # Calculate S value using 1/|n| * V(2,N)/V(N)
        s = (1.0 / n_lengths) * (float(doubles) / total_types)

        return float(s)

    @property
    def honores_h(self) -> float:
        """Compute Honore's H statistic over n-grams.
        Honore's H is based on the assumption that the proportion of tokens
        occuring exactly once is logarithmically related to the total number
        of tokens in the sequence.
        It is defined as:
        :math:`H = 100 * (log(N) / (1.01 - (V1/V(N))))`
        where:
        - :math:`N` is the total number of tokens in the sequence
        - :math:`V1` is the number of types that occur exactly once
        - :math:`V(N)` : The number of different types in a sequence with N tokens.
            This can be interpreted as the size of the token vocabulary of the sequence.

        Interpretation:
        - Higher H values indicate more lexically rich sequences with many unique tokens
        - Lower H values indicate more repetitive sequences with fewer unique tokens

        Returns
        -------
        float
            Mean Honore's H value across n-gram lengths.
            Raises ValueError for empty input.
        """
        if not self.ngram_counts:
            raise ValueError(
                "N-gram counts have not been calculated. Call count_ngrams() first."
            )

        n = sum(self.ngram_counts.values())
        if n == 0:
            raise ValueError("Cannot calculate Honore's H for empty sequence")

        # Get hapax_count (number of hapax legomena)
        hapax_count = sum(1 for count in self.ngram_counts.values() if count == 1)

        # Get total_types
        total_types = len(self.ngram_counts)

        # Handle edge cases
        if total_types == 0 or hapax_count == 0 or hapax_count == total_types:
            import warnings

            warnings.warn(
                "Cannot calculate Honore's H for this sequence, insufficient variation in inputs"
            )
            return float("nan")

        # Calculate H value
        h = 100.0 * (np.log(n) / (1.01 - (float(hapax_count) / total_types)))

        return float(h)

    @property
    def mean_entropy(self) -> float:
        """Compute entropy of n-gram distribution.
        For each ngram length n, calculates the Shannon entropy of the ngram distribution
        and divides by the maximum entropy for that length (log2 N). The mean is then taken
        over these relative entropy values across all lengths.

        This is defined as:

        :math: `H = -sum_{i=1}^{N}(p(x_i) * log2(p(x_i)))`
        where:
        - :math:`H` is the Shannon entropy
        - :math:`N` is the total number of tokens in the sequence
        - :math:`p(x_i)` is the probability of the i-th type

        Interpretation:
        - Higher entropy indicates more random/unpredictable sequences
        - Lower entropy indicates more predictable/structured sequences

        Returns
        -------
        float
            Mean Shannon entropy value across n-gram lengths.
            Raises ValueError for empty input.
        """
        if not self.ngram_counts:
            raise ValueError(
                "N-gram counts have not been calculated. Call count_ngrams() first."
            )

        total_tokens = sum(self.ngram_counts.values())
        if total_tokens <= 1:
            raise ValueError("Cannot calculate entropy for sequence of length <= 1")

        # Calculate probabilities
        probabilities = [count / total_tokens for count in self.ngram_counts.values()]

        # Calculate entropy
        entropy = -np.sum(probabilities * np.log2(probabilities))

        # Normalize entropy by maximum possible entropy for sequence length
        entropy_norm = entropy / np.log2(total_tokens)

        return float(entropy_norm)

    @property
    def mean_productivity(self) -> float:
        """Compute mean productivity of n-gram distribution.

            Mean productivity is defined as the mean of the number of types
            occurring only once divided by the total number of tokens. The types occurring
            only once in a sequence are known as hapax legomena.

            mean_productivity = sum(V1(N)/|n|) where
            - :math: `V1(N)` is the number of types occurring once
            - :math: `|n|` is the number of n-gram lengths

            Interpretation:
            - Higher productivity indicates more diverse/generative sequences with many unique tokens
            - Lower productivity indicates more repetitive sequences with fewer unique tokens

        Returns
        -------
            float
                Mean productivity value across n-gram lengths.
                Raises ValueError for empty input.
        """
        if not self.ngram_counts:
            raise ValueError(
                "N-gram counts have not been calculated. Call count_ngrams() first."
            )

        total_tokens = sum(self.ngram_counts.values())
        if total_tokens == 0:
            raise ValueError("Cannot calculate productivity for empty sequence")

        # Count hapax_count (types occurring once)
        hapax_count = sum(1 for count in self.ngram_counts.values() if count == 1)

        # Calculate productivity
        productivity = hapax_count / total_tokens

        return float(productivity)
