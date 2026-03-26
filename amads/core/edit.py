"""
Edit distance functions for iterables.

Provides various distance metrics for transforming one sequence into another:
- neighbour_swap_distance: Adjacent swaps (bubble sort distance)
- transposition_distance: Arbitrary element swaps
- insertion_distance: Insertions only (no deletions)
- deletion_distance: Deletions only (no insertions)

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


from collections import Counter
from typing import Iterable

# ----------------------------------------------------------------------------


def neighbour_swap_distance(a: Iterable, b: Iterable) -> int | None:
    """
    Minimum number of adjacent swaps (bubble sort distance) to turn a into b.
    Returns None if the multisets differ (different elements present).

    Parameters
    ----------
    a: Iterable
        Any iterable, e.g., list, tuple, string.
    b: Iterable
        Any other iterable. We expect the same type, but do not enforce it.

    Return
    ------
    int or None
        The swap distance, or None if multisets differ.

    Examples
    --------
    >>> neighbour_swap_distance([1, 2, 3], [4, 5, 6]) is None
    True

    >>> neighbour_swap_distance([1, 2, 3], [2, 1, 3])
    1

    >>> neighbour_swap_distance("abc", "bac")
    1

    """
    a = list(a)
    b = list(b)

    if len(a) != len(b) or sorted(a) != sorted(b):
        return None

    # Build position index for b
    pos = {v: [] for v in set(b)}
    for i, v in enumerate(b):
        pos[v].append(i)

    # Build rank sequence by tracking which occurrence of each value maps where
    counts = {v: 0 for v in set(b)}
    rank = []
    for v in a:
        rank.append(pos[v][counts[v]])
        counts[v] += 1

    # Count inversions in rank (O(n log n) with merge sort could be used for large n)
    inversions = 0
    for i in range(len(rank)):
        for j in range(i + 1, len(rank)):
            if rank[i] > rank[j]:
                inversions += 1
    return inversions


def transposition_distance(a: Iterable, b: Iterable) -> int | None:
    """
    Minimum number of arbitrary swaps (any two positions) to turn a into b.
    Returns None if the multisets differ.

    A transposition swaps any two elements in a single operation.
    The distance equals n - c where c is the number of cycles in the
    permutation mapping a to b.

    Parameters
    ----------
    a: Iterable
        Any iterable, e.g., list, tuple, string.
    b: Iterable
        Any other iterable.

    Return
    ------
    int or None
        The transposition distance, or None if multisets differ.

    Examples
    --------
    >>> transposition_distance([1, 2, 3], [4, 5, 6]) is None
    True

    >>> transposition_distance([1, 2, 3], [3, 2, 1])
    1

    >>> transposition_distance([1, 2, 3, 4], [2, 1, 4, 3])
    2

    """
    a = list(a)
    b = list(b)

    if len(a) != len(b) or sorted(a) != sorted(b):
        return None

    # Build position index for b
    pos = {v: [] for v in set(b)}
    for i, v in enumerate(b):
        pos[v].append(i)

    # Build rank sequence (same as neighbour_swap_distance)
    counts = {v: 0 for v in set(b)}
    rank = []
    for v in a:
        rank.append(pos[v][counts[v]])
        counts[v] += 1

    # Build permutation and count cycles
    n = len(rank)
    visited = [False] * n
    cycles = 0

    for i in range(n):
        if not visited[i]:
            # Follow the cycle starting at i
            j = i
            while not visited[j]:
                visited[j] = True
                j = rank[j]
            cycles += 1

    # Distance = n - number of cycles
    return n - cycles


def insertion_distance(a: Iterable, b: Iterable) -> int | None:
    """
    Minimum number of insertions (no deletions) to transform a into b.
    Returns None if any element in a is not present in b.

    This is the edit distance with only insert operations allowed.
    Equivalent to: elements in b that are not accounted for by a's multiset.

    Parameters
    ----------
    a: Iterable
        Source sequence.
    b: Iterable
        Target sequence.

    Return
    ------
    int or None
        The insertion distance, or None if b's elements don't include all of a's.

    Examples
    --------
    >>> insertion_distance([1, 2, 3], [1, 2, 3, 4, 5])
    2

    >>> insertion_distance([1, 2, 3], [1, 2, 3])
    0

    >>> insertion_distance([1, 2, 3], [1, 2]) is None
    True

    """
    a = list(a)
    b = list(b)

    a_counts = Counter(a)
    b_counts = Counter(b)

    # Check if all elements in a exist in b (can only insert, not create)
    for elem in a_counts:
        if elem not in b_counts:
            return None

    # Insertions = surplus elements in b beyond what a provides
    insertions = 0
    for elem, count in b_counts.items():
        if count > a_counts.get(elem, 0):
            insertions += count - a_counts.get(elem, 0)

    return insertions


def deletion_distance(a: Iterable, b: Iterable) -> int | None:
    """
    Minimum number of deletions (no insertions) to transform a into b.
    Returns None if any element in b is not present in a.

    This is the edit distance with only delete operations allowed.
    Equivalent to: elements in a that are not accounted for by b's multiset.

    Parameters
    ----------
    a: Iterable
        Source sequence.
    b: Iterable
        Target sequence.

    Return
    ------
    int or None
        The deletion distance, or None if a's elements don't include all of b's.

    Examples
    --------
    >>> deletion_distance([1, 2, 3, 4, 5], [1, 2, 3])
    2

    >>> deletion_distance([1, 2, 3], [1, 2, 3])
    0

    >>> deletion_distance([1, 2], [1, 2, 3]) is None
    True

    """
    a = list(a)
    b = list(b)

    a_counts = Counter(a)
    b_counts = Counter(b)

    # Check if all elements in b exist in a (can only delete, not conjure)
    for elem in b_counts:
        if elem not in a_counts:
            return None

    # Deletions = surplus elements in a beyond what b provides
    deletions = 0
    for elem, count in a_counts.items():
        if count > b_counts.get(elem, 0):
            deletions += count - b_counts.get(elem, 0)

    return deletions


# ------------------------------------------------------------------------


if __name__ == "__main__":
    import doctest

    doctest.testmod()
