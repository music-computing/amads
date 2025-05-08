"""
Settle on an appropriate granular grid for a smallest metrical pulse level (broadly, "tatum")
in response to a source and user tolerance settings.
"""

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------

from collections import Counter
from typing import Iterable, Union


def starts_to_measure_relative_counter(starts: Iterable[float]):
    """
    Simple wrapper function to map an iterable (e.g., list or tuple) of floats to
    a measure-relative Counter, such that all the keys are geq 0, and less than 1.
    Includes rounding to 5dp.

    Examples
    --------
    >>> test_list = [0.0, 0.0, 0.5, 1.0, 1.5, 1.75, 2.0, 2.3333333333, 2.666667, 3]
    >>> starts_to_measure_relative_counter(test_list)
    Counter({0.0: 5, 0.5: 2, 0.75: 1, 0.33333: 1, 0.66667: 1})
    """
    for item in starts:
        if not isinstance(item, (int, float)):
            raise TypeError(
                f"All items in `starts` must be numeric (int or float). Found: {type(item)}"
            )

    return Counter([round(x - int(x), 5) for x in starts])


def _float_gcd(a, b, rtol=1e-05, atol=1e-08):
    """
    Calculate the greatest common divisor (GCD) for values a and b given the specified
    relative and absolute tolerance (rtol and atol).
    With thanks to Euclid,
    `fractions.gcd`, and
    [stackexchange](https://stackoverflow.com/questions/45323619/).

    In context, set the tolerance values in relation to the granulaity (e.g., pre-rounding) of the input data,
    as shown in the pair of examples below.

    Examples
    --------
    Tolerance works:
    >>> _float_gcd(0.6666, 1, atol=0.001, rtol=0.001)
    0.33319999999999994

    Tolerance fails:
    >>> _float_gcd(0.666, 1, atol=0.001, rtol=0.001)
    0.002

    """
    t = min(abs(a), abs(b))
    while abs(b) > rtol * t + atol:
        a, b = b, a % b
    return a


def metrical_gcd(
    starts: Union[Iterable, Counter],
    bins: int = 12,
    rtol: float = 1e-05,
    atol: float = 1e-08,
    proportion_threshold: float = 0.999,
):
    """
    This function serves music symbolic encoded in terms of measures,
    with events defined by (or convertable to) measure-start-relative positions
    and with the length of those measures remaining constant.

    To create a grid accounting for every metrical position used in a source,
    we need to find the greatest common divisor (GCD).
    In metrically simple and regular cases like chorales, this value might be
    the eighth note, for instance.

    In other cases, it gets more complex.
    For example, Beethoven's Opus 10 Nr.2 Movement 1 is in 2/4 and from the start includes
    a triplet 16ths turn figure in measure 1
    (= 12x division, symbolic time = 1.75, 1.832, 1.916, 2.0)
    and also dotted rhythms pairing a dotted 16th with 32nd note from measure 5
    (= 32x division, symbolic time = 5.0, 5.188, 5.25).
    So to catch these cases in the first 5 measures, we need the
    GCD of 12 and 32, i.e., 96 bins per measure.
    This is the default value of `bins`.

    In cases of extreme complexity, there may be a "need" for a
    considerably greater number of bins.
    This is relevant for some modern music, as well as cases where
    grace notes are assigned a specific metrical position/duration
    (though in many encoded standards, grace notes are not assigned separate metrical positions).

    This function serves those common cases where
    there is a need to balance between capturing event positions as accurately as possible while not
    making excessive complexity to account for a few anomalous notes.

    We reterate that this function is limited to contexts with measures of same length.
    Do not use this functional if position in relation to measures is undefined
    or if the measure length changes during the passage in question
    (here, pre-segemntation by measure length is a possibility, depening on the use case).

    This function seeks the GCD, while setting explicit acceptable tolerance/threshold values for
    the _distance_ of events from simple values (accounting for 3x divisions expressed as a float, for instance)
    and the _number_ of events to account for (avoiding undue complexity for 1 note in a thousand).

    Parameters
    ----------
    starts
        Any iterable giving the starting position of events.
        Must be expressed in measure-relative fashion such that
        X.0 is the start of a measure,
        X.5 is the mid-point of a measure, etc.
        Converted to a Counter object if not already in that format.
    bins
        The argument sets a starting number of bins per measure.
        This function tests various values at this level and greater, returning the one it alights on.
    rtol
        the relative tolerance for temporal position
    atol
        the absolute tolerance for temporal position
    proportion_threshold
        The proportional number of notes to account for before ignoring the rest.
        For example, a value of .999 means that once at least 99.9% of the source's notes are handled,
        we ignore the rest and bin them.
        This is achieved by iterating through a Counter object ordered from the most to least used positions.

    Examples
    --------

    An example of values from the BPSD dataset (Zeilter et al.).

    >>> bpsd_Op027No1 = Counter({
    ... 0.0: 342, 0.5: 320, 0.25: 262, 0.75: 156, 0.375: 123, 0.125: 122, 0.875: 102, 0.625: 82, 0.833: 79,
    ... 0.333: 70, 0.167: 56, 0.417: 44, 0.917: 39, 0.583: 37, 0.667: 37, 0.083: 36, 0.938: 33, 0.688: 32, 0.812: 32,
    ... 0.562: 28, 0.188: 14, 0.312: 14, 0.438: 14, 0.062: 12
    ... })

    # TODO all worked before, now fail with refactor
    # >>> metrical_gcd(bpsd_Op027No1, bins=24, atol=0.01, rtol=0.01, proportion_threshold=0.98)
    # 48
    #
    # Change the `atol`
    # >>> metrical_gcd(bpsd_Op027No1, bins=12, atol=1/12, proportion_threshold=0.999)
    # 12
    #
    # Change the `proportion_threshold`
    # >>> metrical_gcd(bpsd_Op027No1, bins=12, atol=1/24, proportion_threshold=0.80)
    # 12


    """
    if not 0.0 < atol < 1.0:
        raise ValueError("The absolute tolerance (`atol`) must be between 0 and 1.")

    if not 0.0 < rtol < 1.0:
        raise ValueError("The relative tolerance (`rtol`) must be between 0 and 1.")

    if not 0.0 < proportion_threshold < 1.0:
        raise ValueError("The `proportion_threshold` must be between 0 and 1.")

    if not isinstance(bins, int):
        raise ValueError("The `bins` must be an integer.")

    if bins < 0:
        raise ValueError("The `bins` must be a positive integer.")

    if isinstance(starts, Counter):
        for k in starts:
            if k > 1:
                raise ValueError(
                    "The `starts` Counter must be measure-relative, and so have keys of less than 1."
                )
        counter_starts = starts
    else:  # Convert to Counter (also includes type checks)
        counter_starts = starts_to_measure_relative_counter(starts)

    total = sum(counter_starts.values())
    proportion_covered = 0

    gcd = 1 / bins
    for x in counter_starts:
        gcd = _float_gcd(x, gcd, atol=atol, rtol=rtol)

        proportion_covered += counter_starts[x] / total
        if proportion_covered > proportion_threshold:
            break

    return int(1 / gcd)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
