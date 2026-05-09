"""
envelope.py

The `skyline.py` module demonstrates a strict case retrieving the
highest sounding notes at any given point (with caveats as noted there).

Here, we implement a variant that could be said to constitute a "smoothed" form of the same.

Consider a musical line in which only one note sounds at any time.
Musically, this may still outline more than one 'voice'.
Fugues for solo violin provide an example.
Notwithstanding some simultaneities, most of the 'different line' are interleaves sequentially.
The clue to these different lines is often in the relative separation of pitch-onset pairs in pitch-time space.
Highly relevant here is the field of auditory stream segregation.

Moreover, even in the absence of this implied polyphony,
a single monodic melody often outlines a simpler shape with elaborations.
Mozart's first piano sonata (K279) begins with the line
C B D C E D F E G F A
which clearly outlines (or is an elabroated form of)
C D E F G A.

Both of these scenarios are captures by the `envelope`.

In the language data science, we seek the "upper and lower envelope for sequential data".

Terminology
-----------
The `skyline` is used here to denote the upper envelope (aka the "ceiling", or "roofline").
The `valleyline` refers to the the lower envelope (aka the "valley floor").

The algorithm
-------------
A point belongs to the upper envelope if and only if it is NOT a strict local
minimum — i.e. it is not strictly below BOTH of its nearest retained neighbours.
Equivalently: we iteratively remove strict local minima until none remain.

This produces a piecewise-linear boundary that:
  - passes through actual data points (not a fitted curve)
  - retains an arbitrary number of direction changes
  - excludes only points that genuinely dip below (or rise above) their context
  - is parameter-free at tolerance=0 (a tolerance>0 also removes near-flat dips)

The valleyline is the symmetric pair: all of the above applies to the removal of strict local _maxima_.

Supported input forms
---------------------
1. String of digit characters  e.g. "313131" as a toy shorthand for test cases
2. Sequence of scalar values e.g. [3, 1, 3, 1, ...] which is more usable for MIDI pitch numbers for instance
    (in this case a fake onset sequence is synthesised with natural numbers 1, 2, 3, ...)
3. Sequence of (onset, pitch) pairs which data source gives us user- or score-specfied x-spacing.
4. A `Score` object or equivalent (internally using the `.find_all(Note)` functionality to get the above data.

<small>**Author**: Mark Gotham</small>
"""

from typing import Union

from amads.core.basics import Note, Part, Score

__author__ = "Mark Gotham"


# ---------------------------------------------------------------------------

# Type aliases (in-module only)

Point = tuple[float, float]  # (onset, pitch)
PointList = list[Point]


# ---------------------------------------------------------------------------

# Input wrangling ;)


def _to_points(source) -> PointList:
    """
    Normalise any supported input form into
    a list of (onset, pitch) float pairs,
    sorted by onset.

    >>> _to_points("312")
    [(1.0, 3.0), (2.0, 1.0), (3.0, 2.0)]

    >>> _to_points([5, 3, 7])
    [(1.0, 5.0), (2.0, 3.0), (3.0, 7.0)]

    >>> _to_points([(2.0, 4.0), (1.0, 9.0)])
    [(1.0, 9.0), (2.0, 4.0)]

    Empty example:
    >>> _to_points([])
    []

    Invalid type:
    >>> _to_points("abc")
    Traceback (most recent call last):
        ...
    ValueError: String input must contain only digit characters, e.g. '313131'.
    """
    if isinstance(source, str):
        if not all(c.isdigit() for c in source):
            raise ValueError(
                "String input must contain only digit characters, e.g. '313131'."
            )
        return [(float(i + 1), float(c)) for i, c in enumerate(source)]

    if hasattr(source, "find_all"):
        return _extract_from_score(source)

    seq = list(source)
    if not seq:
        return []

    first = seq[0]

    if isinstance(first, (tuple, list)) and len(first) == 2:
        pts = [(float(x), float(y)) for x, y in seq]
        return sorted(pts)

    return [(float(i + 1), float(v)) for i, v in enumerate(seq)]


def _extract_from_score(
    score: Union[Score, Part],
    upper_not_lower: bool = True,
) -> PointList:
    """
    Extract (onset, midi) pairs from a score object.

    Where multiple notes share an onset (chord), only the highest pitch is kept.
    Returns points sorted by onset.

    >>> test_pitches = [60, 62, 60, 64, 60, 65, 60, 67]
    >>> len(test_pitches)
    8

    >>> test_durations=[1.0, 0.5, 1.0, 0.5, 1.0, 0.5, 1.0]
    >>> len(test_durations)
    7

    >>> test_case = Score.from_melody(pitches=test_pitches, durations=test_durations)

    # >>> _extract_from_score(test_case, upper_not_lower=True)
    # [(0.0, 60.0), (1.0, 62.0), (1.5, 64.0), (2.5, 65.0), (3.0, 67.0)]

    # >>> _extract_from_score(test_case, upper_not_lower=False)
    # []
    """
    pairs: dict[float, float] = {}

    for note in score.find_all(Note):
        onset = float(note.onset)
        midi = float(note.key_num)
        if onset not in pairs:
            pairs[onset] = midi
        else:
            if upper_not_lower:
                pairs[onset] = max(pairs.get(onset, midi), midi)
            else:
                pairs[onset] = min(pairs.get(onset, midi), midi)
    return sorted(pairs.items())


# ---------------------------------------------------------------------------

# Core envelope algorithm


def _envelope(
    points: PointList, upper_not_lower: bool = True, tolerance: float = 0.0
) -> PointList:
    """
    Compute the upper or lower piecewise-linear envelope of a point sequence.

    Algorithm: iteratively remove strict local minima (upper) or maxima (lower)
    until the sequence is stable.  A point is a strict local minimum when its
    y-value is more than `tolerance` below both its nearest retained neighbours.

    Parameters
    ----------
    points : list of (x, y) pairs, will be sorted by x internally
    upper_not_lower : bool, True for 'upper', False for 'lower'
    tolerance : vertical slack -- points within this distance of their neighbours
                are also removed  (0.0 = exact envelope, the default)

    Returns
    -------
    Subset of the original points forming the envelope, sorted by x.

    >>> _envelope([(1,5),(2,1),(3,5)], upper_not_lower=True)
    [(1, 5), (3, 5)]

    >>> _envelope([(1,1),(2,5),(3,1)], upper_not_lower=False)
    [(1, 1), (3, 1)]

    >>> _envelope([(1,3),(2,3),(3,3)], upper_not_lower=True)
    [(1, 3), (2, 3), (3, 3)]

    >>> simultaneity = [(1,5),(1,2),(2,3)]
    >>> _envelope(simultaneity, upper_not_lower=True)
    [(1, 5), (2, 3)]

    >>> _envelope(simultaneity, upper_not_lower=False)
    [(1, 2), (2, 3)]

    One item
    >>> _envelope([(1,3)], upper_not_lower=True)
    [(1, 3)]

    No items
    >>> _envelope([], upper_not_lower=True)
    []

    Tolerance:
    >>> dip = [(1,5),(2,3),(3,5)]
    >>> tol_1  = _envelope(dip, upper_not_lower=True, tolerance=1.0)
    >>> tol_1
    [(1, 5), (3, 5)]

    >>> tol_2  = _envelope(dip, upper_not_lower=True, tolerance=2.0)
    >>> tol_2
    [(1, 5), (2, 3), (3, 5)]

    >>> tol_2 == dip
    True
    """

    pts = sorted(points)  # sort by x

    # Deduplicate by x: keep highest y for upper, lowest y for lower
    deduped: PointList = []
    for x, y in pts:
        if deduped and deduped[-1][0] == x:
            if (upper_not_lower and y > deduped[-1][1]) or (
                not upper_not_lower and y < deduped[-1][1]
            ):
                deduped[-1] = (x, y)
        else:
            deduped.append((x, y))
    pts = deduped

    if len(pts) <= 2:
        return pts

    def is_redundant(left_y: float, mid_y: float, right_y: float) -> bool:
        if upper_not_lower:
            return mid_y < left_y - tolerance and mid_y < right_y - tolerance
        else:
            return mid_y > left_y + tolerance and mid_y > right_y + tolerance

    changed = True
    while changed:
        changed = False
        new_pts: PointList = [pts[0]]
        for i in range(1, len(pts) - 1):
            if is_redundant(new_pts[-1][1], pts[i][1], pts[i + 1][1]):
                changed = True  # drop pts[i]
            else:
                new_pts.append(pts[i])
        new_pts.append(pts[-1])
        pts = new_pts

    return pts


# ---------------------------------------------------------------------------

# Public API


def skyline_envelope(source, tolerance: float = 0.0) -> PointList:
    """
    Upper envelope of the data (not to be confused with polyphony.skyline).

    Returns the subset of input points that form the "roofline": no omitted
    point lies above the piecewise-linear boundary between its neighbours.

    Parameters
    ----------
    source : As described at the top of this module:
        str of digits,
        sequence of scalars,
        sequence of (onset, pitch) pairs,
        score object with .find_all(Note)
    tolerance: points that dip no more than this amount below their neighbours are also removed
        (default 0 = exact envelope)

    Returns
    -------
    list of (onset, pitch) float pairs on the upper envelope

    Examples
    --------

    Test some inpute types.

    >>> test_case = skyline_envelope("31513")
    >>> test_case
    [(1.0, 3.0), (3.0, 5.0), (5.0, 3.0)]

    >>> skyline_envelope([3, 1, 5, 1, 3]) == test_case
    True

    >>> skyline_envelope([(1.0, 3.0), (2.0, 1.0), (3.0, 5.0), (4.0, 1.0), (5.0, 3.0)]) == test_case
    True

    Test de-duplication of simultaneities

    >>> skyline_envelope([(1.0, 5.0), (1.0, 2.0), (2.0, 3.0)])
    [(1.0, 5.0), (2.0, 3.0)]
    """
    return _envelope(
        _to_points(source), upper_not_lower=True, tolerance=tolerance
    )


def valleyline_envelope(source, tolerance: float = 0.0) -> PointList:
    """
    Lower envelope of the data.

    Returns the subset of input points that form the "valley floor": no omitted
    point lies below the piecewise-linear boundary between its neighbours.

    Parameters
    ----------
    See skyline_envelope

    Returns
    -------
    list of (onset, pitch) float pairs on the lower envelope

    Examples
    --------

    Test some inpute types.

    >>> test_case = valleyline_envelope("31513")
    >>> test_case
    [(1.0, 3.0), (2.0, 1.0), (4.0, 1.0), (5.0, 3.0)]

    >>> valleyline_envelope([3, 1, 5, 1, 3]) == test_case
    True

    >>> valleyline_envelope([(1.0, 3.0), (2.0, 1.0), (3.0, 5.0), (4.0, 1.0), (5.0, 3.0)]) == test_case
    True

    Test de-duplication of simultaneities

    >>> valleyline_envelope([(1.0, 5.0), (1.0, 2.0), (2.0, 3.0)])
    [(1.0, 2.0), (2.0, 3.0)]
    """
    return _envelope(
        _to_points(source), upper_not_lower=False, tolerance=tolerance
    )


# ---------------------------------------------------------------------------

# Convenience: values only (x coordinates stripped from result)


def skyline_values(source, tolerance: float = 0.0) -> list[float]:
    """Upper envelope as a plain list of y-values (onset coordinates omitted).

    >>> skyline_values("31513")
    [3.0, 5.0, 3.0]

    >>> skyline_values([1, 3, 1])
    [1.0, 3.0, 1.0]
    """
    return [y for _, y in skyline_envelope(source, tolerance)]


def valleyline_values(source, tolerance: float = 0.0) -> list[float]:
    """Lower envelope as a plain list of y-values (onset coordinates omitted).

    >>> valleyline_values("31513")
    [3.0, 1.0, 1.0, 3.0]
    """
    return [y for _, y in valleyline_envelope(source, tolerance)]
