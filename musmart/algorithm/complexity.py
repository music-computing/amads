#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Implements various functions related to complexity and information density."""

import numpy as np


__all__ = ["lz77"]


def lz77(sequence: np.array, window_size: int = 64) -> int:
    """Applies the LZ77 compression algorithm to a discrete `sequence` and returns length of the compressed string

    Here we calculate the complexity of a discrete `sequence` (could be pitch classes, binned inter-onset intervals)
    by converting it into a string representation, compressing using LZ77 [1], then calculating the length of the
    compressed string as in [2]. Higher values mean that more information is required to represent the sequence and
    thus greater complexity.

    Arguments:
        sequence (np.array): a discrete sequence, could be pitch classes, inter-onset intervals, etc...
        window_size (int, optional): the size of the sliding window to use in LZ77 calculation, defaults to 64

    Returns:
        int: the length of the compressed string

    Examples:
        NB. some examples are taken from https://timguite.github.io/jekyll/update/2020/03/15/lz77-in-python.html

        >>> lz77(np.array(["a"]))
        1

        >>> lz77(np.array(["a", "b", "a"]))
        3

        >>> testme = "word word"
        >>> lz77(np.array(list(testme)))    # i.e., np.array(["w", "o", "r", "d", " ", "w", "o", "r", "d"])
        6

        >>> lz77(np.array([0.1, 0.2, 0.1]))    # works with numeric values as well
        1

    References:
          [1]: Ziv, J., & Lempel, A. (1977). A universal algorithm for sequential data compression. IEEE Transactions
          on Information Theory. 23/3 (pp. 337–343).
          [2]: Cheston, H., Schlichting, J. L., Cross, I., & Harrison, P. M. C. (2024). Rhythmic qualities of jazz
          improvisation predict performer identity and style in source-separated audio recordings. Royal Society
          Open Science. 11/11.

    """

    def _lz77_compress(str_representation: str) -> list[tuple]:
        """Runs the LZ77 compression algorithm over the input `data`, with given `window_size`"""
        compress_list = []
        index = 0
        while index < len(str_representation):
            best_offset = -1
            best_length = -1
            best_match = ''
            # Search for the longest match in the sliding window
            for length in range(1, min(len(str_representation) - index, window_size)):
                substring = str_representation[index:index + length]
                offset = str_representation.rfind(substring, max(0, index - window_size), index)
                if offset != -1 and length > best_length:
                    best_offset = index - offset
                    best_length = length
                    best_match = substring
            if best_match:
                # Add the (offset, length, next_character) tuple to the compressed data
                compress_list.append((best_offset, best_length, str_representation[index + best_length]))
                index += best_length + 1
            else:
                # No match found, add a zero-offset tuple
                compress_list.append((0, 0, str_representation[index]))
                index += 1
        return compress_list

    assert len(sequence.shape) == 1, "Must provide a 1D array as input"
    # Convert the sequence to a string representation
    mapping = {v: i for i, v in enumerate(np.unique(sequence))}    # integer value for every unique element in sequence
    str_representation_of_sequence = "".join(str(mapping[v]) for v in sequence)    # map values using dict
    # Apply the LZ77 compression algorithm to the string representation, which gives us a list of tuples
    compressed = _lz77_compress(str_representation_of_sequence)
    # We take the length of the compressed string as the complexity of the input
    # TODO: alternatively, we can also express the compression score proportionally, with relation to the length
    #  of the initial input i.e., we'd do `score / len(sequence). Perhaps this could be an optional argument?
    return len(compressed)
