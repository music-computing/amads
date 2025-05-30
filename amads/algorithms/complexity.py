"""
This module provides functionality for measuring the complexity of discrete sequences
using the LZ77 compression algorithm.

References:
    - Ziv, J., & Lempel, A. (1977). A universal algorithm for sequential data compression.
      IEEE Transactions on Information Theory, 23(3), 337–343.
      https://doi.org/10.1109/TIT.1977.1055714

    - Cheston, H., Schlichting, J. L., Cross, I., & Harrison, P. M. C. (2024).
      Rhythmic qualities of jazz improvisation predict performer identity and style
      in source-separated audio recordings. Royal Society Open Science, 11(11).
      https://doi.org/10.1098/rsos.240920

Author:
    Huw Cheston (2025)
"""

from typing import Hashable, Iterable, Union

__author__ = "Huw Cheston"


def lz77_encode(input_list: list[Hashable]) -> list:
    """Runs the LZ77 compression algorithm over the input `data`, generating tuples of (distance, length, symbol)"""

    # Catch sequences that have a length of zero
    if len(input_list) == 0:
        raise ValueError("Cannot encode an empty sequence!")
    encoded = []
    i = 0
    while i < len(input_list):
        best_length = 0
        best_distance = 0
        # Search the entire processed portion (positions 0 to i-1)
        for j in range(0, i):
            length = 0
            # Allow overlapping matches: compare while within input bounds.
            while (
                (i + length < len(input_list))
                and (j + length < len(input_list))
                and (input_list[j + length] == input_list[i + length])
            ):
                length += 1
            if length > best_length:
                best_length = length
                best_distance = i - j
        # If a match was found, output a match token.
        if best_length > 0:
            encoded.append((best_distance, best_length, input_list[i]))
            i += best_length
        else:
            # No match: output a literal token with length 1.
            encoded.append((0, 1, input_list[i]))
            i += 1
    return encoded


def lz77_decode(encoded: list[int, int, Hashable]) -> list[Hashable]:
    """Decode a list of LZ77 tokens, each of which are 3-tuples with form (distance, length, symbol)"""

    # Catch sequences that have a length of zero
    if len(encoded) == 0:
        raise ValueError("Cannot decode an empty sequence!")
    decoded = []
    for token in encoded:
        distance, length, symbol = token
        # Literal token: simply append the symbol.
        if distance == 0:
            decoded.append(symbol)
        # Match token: copy 'length' characters from the already decoded list,
        # starting at position len(decoded) - distance.
        else:
            start = len(decoded) - distance
            for i in range(length):
                decoded.append(decoded[start + i])
    return decoded


def lz77_complexity(
    sequence: Iterable[Hashable], normalized: bool = False
) -> Union[int, float]:
    """
    Compresses a discrete sequence using the LZ77 algorithm and returns the length of the compressed output.

    This function applies LZ77 compression to a sequence of hashable elements (e.g., strings, floats, integers).
    Higher compression lengths indicate greater complexity in the sequence.

    Args:
        sequence (Iterable[Hashable]):
            A discrete sequence, such as pitch classes or inter-onset intervals.

        normalized (bool, optional):
            If True, the result is expressed relative to the input size, where 1.0 indicates
            maximum complexity (i.e., no compression is possible). Defaults to False.

    Returns:
        int | float:
            The length of the compressed sequence, either as a raw integer or a normalized float.

    """

    # Compress the sequence
    compressed = lz77_encode(sequence)
    # Express with relation to length of input string if required: returns a float
    if normalized:
        return len(compressed) / len(sequence)
    # Otherwise, take the length of the compressed string as the complexity of the input: returns an int
    else:
        return len(compressed)
