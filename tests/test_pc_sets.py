"""
Test PC Sets

Tests for pitch class set operations.

By Mark Gotham, 2021

License: Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/

Source: Gotham and Yust, Serial Analyser, DLfM 2021
https://github.com/MarkGotham/Serial_Analyser
"""

import pytest

from amads.pitch.pc_set_functions import pitches_to_prime, set_classes_from_cardinality


@pytest.mark.skip(
    reason="Currently failing, issue logged in https://github.com/music-computing/amads/issues/37"
)
def test_pitches_to_prime():
    """
    Tests one case through the interval vector, and another that requires transformation.
    """
    prime = pitches_to_prime((0, 2, 3))
    assert prime == (0, 1, 3)

    # Test one case of numbers beyond 0-11
    prime = pitches_to_prime((100, 102, 103))
    assert prime == (0, 1, 3)

    prime = pitches_to_prime(
        (8, 2, 4, 7)
    )  # via I [0,2,5,6], t2 [2,4,7,8], and shuffle.
    assert prime == (0, 1, 4, 6)


@pytest.mark.skip(
    reason="Currently failing, issue logged in https://github.com/music-computing/amads/issues/37"
)
def test_self_complement_hexachords():
    """
    Tests that all and only the hexachords without a Z-related pair are self-complementary.
    (In so doing, this also tests the pitches-to-prime routine.)
    """
    count_hexachords = 0
    count_total = 0
    for entry in set_classes_from_cardinality(6):
        hexachord = entry[1]
        complement = tuple([x for x in range(12) if x not in hexachord])
        complement_prime = pitches_to_prime(complement)
        if hexachord == complement_prime:
            assert "Z" not in entry[0]
            count_hexachords += 1
            count_total += entry[3]
        else:
            assert "Z" in entry[0]

    assert count_hexachords == 20  # 20/50, so 40%
    assert count_total == 372  # 372/924, so 35.4%
