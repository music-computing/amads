"""Test suite for functions inside amads/algorithms/complexity.py"""

import pytest

from amads.algorithms.complexity import lz77_complexity, lz77_decode, lz77_encode

DECODED_SEQUENCES = [
    # The following four examples are from https://timguite.github.io/jekyll/update/2020/03/15/lz77-in-python.html
    ["a"],
    ["a", "b", "a"],
    ["w", "o", "r", "d", " ", "w", "o", "r", "d"],
    ["a", "b", "a", "b", "a", "b", "a", "b"],
    # This example is taken (with a bit of retooling to match our input structure, but the same results) from
    # https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-wusp/fb98aa28-5cd7-407f-8869-a6cef1ff1ccb
    ["A", "A", "B", "C", "B", "B", "A", "B", "C"],
]

ENCODED_SEQUENCES = [
    [(0, 1, "a")],
    [(0, 1, "a"), (0, 1, "b"), (2, 1, "a")],
    [(0, 1, "w"), (0, 1, "o"), (0, 1, "r"), (0, 1, "d"), (0, 1, " "), (5, 4, "w")],
    [(0, 1, "a"), (0, 1, "b"), (2, 6, "a")],
    [
        (0, 1, "A"),
        (1, 1, "A"),
        (0, 1, "B"),
        (0, 1, "C"),
        (2, 1, "B"),
        (3, 1, "B"),
        (5, 3, "A"),
    ],
]
ENCODED_SIZES = [1, 3, 6, 3, 7]
ENCODED_PROPORTIONAL_SIZES = [1, 1, 2 / 3, 3 / 8, 7 / 9]


@pytest.mark.parametrize(
    "to_encode,to_decode", zip(DECODED_SEQUENCES, ENCODED_SEQUENCES)
)
def test_lz77_encode_decode(to_encode, to_decode):
    # Encode and decode the sequence
    encoded = lz77_encode(to_encode)
    decoded = lz77_decode(encoded)
    # Encoded, the sequence should be as we expect
    assert encoded == to_decode
    # Decoding the sequence should give the original input
    assert decoded == to_encode


@pytest.mark.parametrize(
    "to_encode,size,size_proportional",
    zip(DECODED_SEQUENCES, ENCODED_SIZES, ENCODED_PROPORTIONAL_SIZES),
)
def test_lz77_complexity(to_encode, size, size_proportional):
    # Encode and get raw complexity
    actual = lz77_complexity(to_encode, normalized=False)
    assert actual == size
    # Encode and get normalized complexity
    actual_proportional = lz77_complexity(to_encode, normalized=True)
    assert actual_proportional == size_proportional


def test_bad_sequence():
    # Test some empty sequences
    for seq in [[], "", tuple()]:
        with pytest.raises(ValueError):
            lz77_decode(seq)
        with pytest.raises(ValueError):
            lz77_encode(seq)
