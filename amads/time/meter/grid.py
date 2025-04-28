"""
Settle on an appropriate granular grid of metrical tatums in response to a source and user settings.
"""

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------

import logging
from collections import Counter
from typing import Iterable, Union

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def starts_to_measure_relative_counter(starts: Iterable[float]):
    """
    Simple wrapper function to map an iterable (e.g., list or tuple) of floats to
    a measure-relative Counter, such that all the keys are geq 0, and less than 1.

    Examples
    --------
    >>> test_list = [0.0, 0.0, 0.5, 1.0, 1.5, 1.75, 2.0, 2.33, 2.667, 3]
    >>> starts_to_measure_relative_counter(test_list)
    Counter({0.0: 5, 0.5: 2, 0.75: 1, 0.33000000000000007: 1, 0.6669999999999998: 1})
    """
    for item in starts:
        if not isinstance(item, (int, float)):
            raise TypeError(
                f"All items in `starts` must be numeric (int or float). Found: {type(item)}"
            )

    return Counter([(x - int(x)) for x in starts])


def metrical_gcm(
    starts: Union[Iterable, Counter],
    bins: int = 12,
    distance_threshold: float = 1 / 24,
    proportion_threshold: float = 0.999,
):
    """
    To create a grid featuring every metrical position used in a source,
    we need to find the greatest common multiple (GCM).
    In metrically simple and regular cases like chorales, this value might be
    the eighth note, for instance.

    In other cases, it gets more complex.
    For example, Beethoven's Opus 10 Nr.2 Movement 1 is in 2/4 and from the start includes
    a triplet 16ths turn figure in measure 1
    (= 12x division, symbolic time = 1.75, 1.832, 1.916, 2.0)
    and also dotted rhythms pairing a dotted 16th with 32nd note from measure 5
    (= 32x division, symbolic time = 5.0, 5.188, 5.25).
    So to catch these cases in the first 5 measures, we need the
    lowest common multiple of 12 and 32, i.e., 96 bins.
    This is the default value of `bins`.

    In cases of extreme complexity, there may be a "need" for a
    considerably greater number of bins (shorter GCD).
    This is relevant for some modern music, as well as cases where
    grace notes are assigned a specific metrical position/duration
    (though in many encoded standards, grace notes are not assigned separate metrical positions).

    This function serves those common cases where
    there is a need to balance between capturing event positions as accurately as possible while not
    making excessive complexity to account for a few anomalous notes.

    This function serves that purpose.
    We seek the greatest common divider (GCD), while setting acceptable tolerance/threshold for
    the _distance_ of events from simple values (accounting a 3x divisions expressed as a float, for instance)
    and the _number_ of events to account for (not adding undue complexity for 1 note in a thousand).

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
    distance_threshold
        The rounding tolerance between a temporal position multiplied by the bin value and the nearest integer.
        This is essential when working with floats, but can be set to any value the user prefers.
    proportion_threshold
        The proportional number of notes to account for/ignore.
        The default of .999 means that once at least 99.9% of the source's notes are handled, we ignore the rest and bin them.
        This is achieved by iterating through a Counter object ordered from most to least used.

    Examples
    --------

    An example of values from the BPSD dataset (Zeilter et al.).

    >>> bpsd_Op027No1 = Counter({
    ... 0.0: 342, 0.5: 320, 0.25: 262, 0.75: 156, 0.375: 123, 0.125: 122, 0.875: 102, 0.625: 82, 0.833: 79,
    ... 0.333: 70, 0.167: 56, 0.417: 44, 0.917: 39, 0.583: 37, 0.667: 37, 0.083: 36, 0.938: 33, 0.688: 32, 0.812: 32,
    ... 0.562: 28, 0.188: 14, 0.312: 14, 0.438: 14, 0.062: 12
    ... })

    >>> metrical_gcm(bpsd_Op027No1, bins=12, distance_threshold=1/24, proportion_threshold=0.999)
    48

    Change the `distance_threshold`
    >>> metrical_gcm(bpsd_Op027No1, bins=12, distance_threshold=1/12, proportion_threshold=0.999)
    12

    Change the `proportion_threshold`
    >>> metrical_gcm(bpsd_Op027No1, bins=12, distance_threshold=1/24, proportion_threshold=0.80)
    12


    """
    if not 0.0 < distance_threshold < 1.0:
        raise ValueError("The `distance_threshold` must be between 0 and 1.")

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
                    "The `starts` Counter must measure relative, and so have keys of less than 1."
                )
        counter_starts = starts
    else:  # Convert to Counter (also includes type checks)
        counter_starts = starts_to_measure_relative_counter(starts)

    total = sum(counter_starts.values())
    cumulative_count = 0

    for x in counter_starts:
        test_case = x * bins
        diff = abs(round(test_case, 1) - test_case)

        logging.debug(f"Start position {x}. Testing against {bins} bins. Gap of {diff}")
        if diff > distance_threshold:
            logging.debug(f" ... is outside the threshold of {distance_threshold} ...")
            for multiplier in [2, 3, 4, 6, 8, 12, 32, 96]:
                bins *= multiplier
                test_case = x * bins
                diff = abs(round(test_case) - test_case)
                logging.debug(f"... trying `bins` value {bins} ... ")
                if diff < distance_threshold:
                    logging.debug(" ... works, move on.")
                    break
                else:
                    logging.debug(" ... doesn't work, ...")
                    bins /= multiplier
        else:
            logging.debug(
                f" ... is within the threshold of {distance_threshold}. Moving on."
            )

        logging.debug(f"Proportion covered = {cumulative_count}")
        if cumulative_count > proportion_threshold:
            break
        else:
            cumulative_count += counter_starts[x] / total

    return int(bins)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
