#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Implements various functions related to complexity and information density."""

from typing import Iterable, Hashable, Union


__all__ = ["lz77_size", "lz77_compress"]
__author__ = "Huw Cheston"


def lz77_compress(str_representation: str, window_size) -> list[tuple]:
    """Runs the LZ77 compression algorithm over the input `data`, with given `window_size`"""
    # TODO: this should use a list, rather than a string representation
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


def lz77_size(sequence: Iterable[Hashable], window_size: int = 64, proportional: bool = False) -> Union[int, float]:
    """
    Applies the LZ77 compression algorithm to a discrete `sequence` and returns the length of the compressed string.

    Here we calculate the complexity of a discrete `sequence` (could be pitch classes, binned inter-onset intervals)
    by converting it into a string representation, compressing using LZ77 [1], then calculating the length of the
    compressed string as in [2]. Higher values mean that more information is required to represent the sequence,
    indicating greater complexity.

    Currently, only sequences with fewer than 96 unique elements are supported.

    Parameters
    ----------
    sequence : np.ndarray
        A discrete sequence, which could be pitch classes, inter-onset intervals, etc.

    window_size : int, optional
        The size of the sliding window to use in LZ77 calculation. Default is 64.

    proportional : bool, optional
        If True, the complexity is expressed with respect to the size of the input such that 1.0 means the input
        cannot be compressed (i.e., maximum possible complexity). Default is False.

    Returns
    -------
    int | float
        The length of the compressed string, either in `raw` form (int) or wrt. input sequence length (float)

    Raises
    ------
    NotImplementedError
        If the input contains more than 96 unique elements.

    Examples
    --------
    NB: Some examples are taken from https://timguite.github.io/jekyll/update/2020/03/15/lz77-in-python.html

    >>> lz77_size(["a"])
    1

    >>> lz77_size(["a", "b", "a"])
    3

    >>> testme = "word word"
    >>> lz77_size(list(testme))  # i.e., np.array(["w", "o", "r", "d", " ", "w", "o", "r", "d"]))
    6

    >>> lz77_size([0.1, 0.2, 0.1])  # Works with numeric values as well
    3

    >>> lz77_size([0, 1, 2, 3, 4, 0, 1, 2, 3])
    6

    >>> lz77_size(range(1000))  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    NotImplementedError: Currently only sequences with fewer than 95 unique elements are supported.

    References
    ----------
    [1] Ziv, J., & Lempel, A. (1977). A universal algorithm for sequential data compression. IEEE Transactions on
        Information Theory, 23/3, 337–343. https://doi.org/10.1109/TIT.1977.1055714

    [2] Cheston, H., Schlichting, J. L., Cross, I., & Harrison, P. M. C. (2024). Rhythmic qualities of jazz
        improvisation predict performer identity and style in source-separated audio recordings. Royal Society
        Open Science, 11/11. https://doi.org/10.1098/rsos.240920

    """

    # TODO: this is a band-aid fix. We should calculate LZ77 for a list, rather than a string representation, which
    #  would mean we wouldn't have a limit for the number of characters that can be used
    # Get list of printable characters with len == 1
    chrs = [chr(i) for i in range(32, 127)]
    # Raise an error if we have too many unique elements
    if len(set(sequence)) > len(chrs):
        raise NotImplementedError(f"Currently only sequences with fewer than {len(chrs)} unique elements are supported")
    # Convert sequence into a string representation, with the same character for each unique element
    mapping = {v: chrs[i] for i, v in enumerate(set(sequence))}    # integer value for every unique element in sequence
    str_representation_of_sequence = "".join(str(mapping[v]) for v in sequence)
    # Compress the string representation
    compressed = lz77_compress(str_representation_of_sequence, window_size)
    # We take the length of the compressed string as the complexity of the input
    score = len(compressed)
    # Express with relation to length of input string if required
    if proportional:
        score /= len(sequence)
    return score
