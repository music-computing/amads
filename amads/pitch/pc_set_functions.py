"""
Functions for retrieving one pitch class set property directly from another.

Most of the retrieval function names are in the form
`<call-on-type>_to_<return-type>`
e.g.
`prime_to_combinatoriality`
Some are simple mappings from one entry to another.
Anything starting with pitches involves more calculation.

Broadly as implemented by Mark Gotham
for [Serial_Analyser](https://github.com/MarkGotham/Serial_Analyser)
after Robert Morris,
but the functions are general
and not really named algorithms in sense used elsewhere on this code base.
"""

from typing import List, Tuple, Union

from . import pc_sets
from . import transformations as pitch_list_transformations


def set_classes_from_cardinality(cardinality: int):
    """
    In: a cardinality (2-10).
    Out: the pitch class set data for that cardinality.
    """
    if not (1 < cardinality < 11):
        raise ValueError("Invalid cardinality: must be 2-10 (inclusive).")
    else:
        return pc_sets.set_classes[cardinality]


def prime_to_combinatoriality(prime: Tuple[int]):
    """
    In: a prime form expressed as a Tuple of integers.
    Out: the combinatoriality status as a string.
    """
    data = set_classes_from_cardinality(len(prime))
    for x in data:
        if x[1] == prime:
            return x[3]
    raise ValueError(f"{prime} is not a valid prime form")


def interval_vector_to_combinatoriality(vector: Tuple[int]):
    """
    In: an interval vector for any set with 2-10 distinct pitches,
    expressed as a Tuple of 6 integers.
    Out: the combinatoriality status of any valid interval vector as a
    string (one of T, I, RI, A, or an empty string for non-combinatorial cases).
    """
    if len(vector) != 6:
        raise ValueError(f"{vector} is not a valid interval vector")
    total = sum(vector)
    total_to_cardinality = {1: 2, 3: 3, 6: 4, 15: 6}
    data = set_classes_from_cardinality(total_to_cardinality[total])
    for x in data:
        if x[2] == vector:
            return x[-1]
    raise ValueError(f"{vector} is not a valid interval vector")


def pitches_to_combinatoriality(pitches: Union[List[int], Tuple[int]]):
    """
    In: a list or tuple of pitches expressed as integers (0–11) for sets with 2-10 distinct pitches.
    Out: the combinatoriality status as a string.
    """
    icv = pitches_to_interval_vector(pitches)
    return interval_vector_to_combinatoriality(icv)


def distinct_PCs(pitches: Union[List, Tuple]) -> list:
    """
    In: a list or tuple of pitches (any integers).
    Out: a list of distinct PCs in the range 0-11.
    """
    pitches = list(set(pitches))  # remove any duplicates
    return [p % 12 for p in pitches]


def pitches_to_interval_vector(pitches: Union[List[int], Tuple[int]]):
    """
    In: a list or tuple of pitches.
    Out: the interval vector.
    """
    pitches = distinct_PCs(pitches)

    vector = [0, 0, 0, 0, 0, 0]
    from itertools import combinations

    for p in combinations(pitches, 2):
        ic = p[1] - p[0]
        if ic < 0:
            ic *= -1
        if ic > 6:
            ic = 12 - ic
        vector[ic - 1] += 1
    return tuple(vector)


def pitches_to_forte_class(pitches: Union[List[int], Tuple[int]]):
    """
    In: a list or tuple of pitches expressed as integers (0–11) for sets with 2-10 distinct pitches.
    Out: the Forte class.
    """
    data = set_classes_from_cardinality(len(pitches))
    prime = pitches_to_prime(pitches)
    for x in data:
        if x[1] == prime:
            return x[0]
    raise ValueError(f"{pitches} is not a valid entry.")


def pitches_to_prime(pitches: Union[List[int], Tuple[int]]):
    """
    In: a list or tuple of pitches expressed as integers (0–11) for sets with 2-10 distinct pitches.
    Out: the prime form.

    The function first converts the pitches to their interval vector (easy, fast).
    That vector unambiguously gives the prime form for cases except those with Z-related pairs.
    This affects one pair of tetrachords (so 2 prime forms) and 15 pairs of hexachords (30 primes).

    In those cases, the prime form is worked out by comparing the pitch list against the pair of
    options in both inversions until a match is found.
    """

    pitches = distinct_PCs(pitches)

    vector = pitches_to_interval_vector(pitches)
    primes = []
    data = set_classes_from_cardinality(len(set(pitches)))

    for x in data:
        if x[2] == vector:
            primes.append(x[1])

    if len(primes) == 1:
        return primes[0]
    elif len(primes) > 1:
        for prime in primes:  # each possible prime form
            inverted = pitch_list_transformations.invert(prime)
            for t in [prime, inverted]:
                if transposition_equivalent(t, pitches):
                    return prime


def transposition_equivalent(set1, set2):
    """
    Supporting function for determining whether two sets are transposition equivalent
    as part of determining prime forms with `pitches_to_prime`.
    """
    sorted_set2 = sorted(list(set2))
    for i in range(12):
        test_case = sorted(list(pitch_list_transformations.transpose_by(set1, i)))
        if test_case == sorted_set2:
            return True


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
