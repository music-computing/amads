"""
The module seeks to find the smallest metrical pulse level (broadly, “tatum”)
in response to a source and user tolerance settings.

In the simplest case, a source records its metrical positions exactly,
including fractional values as needed.
We provide functionality for standard, general algorithms in these cases
(greatest common denominator and fraction estimation)
which are battle-tested and computationally efficient.

In metrically simple and regular cases like chorales, this value might be
the eighth note, for instance.
In other cases, it gets more complex.
For example, Beethoven's Opus 10 Nr.2 Movement 1 includes
a triplet 16th turn figure in measure 1
(tatum = 1/6 division of the quarter note)
and also dotted rhythms that pair a dotted 16th with a 32nd note from measure 5
(tatum = 1/8 division of the quarter).
So to catch these cases in the first 5 measures, we need the
lowest common multiple of 6 and 8, i.e., 24 per quarter (or 48 bins per 2/4 measure).

In cases of extreme complexity, there may be a “need” for a
considerably shorter tatum pulse (and, equivalently, a greater number of bins).
This is relevant for some modern music, as well as cases where
grace notes are assigned a specific metrical position/duration
(though in many encoded standards, grace notes are not assigned
separate metrical positions).

Moreover, there are musical sources that do not encode fractional time
values, but rather approximation with floats. These include any:

  - frame-wise representations of time (including MIDI and any attempted
    transcription from audio),
  - processing via code libraries that likewise convert fractions to floats,
  - secondary representations like most CSVs.

As division by 3 leads to rounding, approximation, and floating point errors,
and as much music involves those divisions, this is widely relevant.

The standard algorithms often fail in these contexts, largely because symbolic music
tends to prioritise certain metrical divisions over others.
For example, 15/16 is a commonly used metrical position (largely because 16 is a power of 2), but 14/15 is not.
That being the case, while 14/15 might be a better mathematical fit for approximating a value,
it is typically incorrect as the musical solution.
We can use the term “incorrect” advisedly here because
the floats are secondary representations of a known fractional ground truth.
Doctests demonstrate some of these cases.

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------

from collections import Counter
from fractions import Fraction
from numbers import Number
from typing import Iterable, Optional, Union

from amads.algorithms.gcd import fraction_gcd_pair


def starts_to_int_relative_counter(starts: Iterable[float]):
    """
    Find and count all fractional parts of an iterable.

    Simple wrapper function to create a Counter (dict) that
    maps the fractional parts of starts ($start - int(start)$, e.g.,
    1.5 becomes 0.5) to the number of occurrences of that fraction
    (e.g., starts 1.5 and 2.5 produce the mapping 0.5: 2 in the result).

    Fractional parts are rounded to 5 decimal points. This may change.

    Examples
    --------
    >>> test_list = [0.0, 0.0, 0.5, 1.0, 1.5, 1.75, 2.0, 2.3333333333, 2.666667, 3.00000000000000001]
    >>> starts_to_int_relative_counter(test_list)
    Counter({0.0: 5, 0.5: 2, 0.75: 1, 0.33333: 1, 0.66667: 1})
    """
    for item in starts:
        if not isinstance(
            item, Number
        ):  # int, float, Fraction, np.float32 etc.
            raise TypeError(
                f"All items in `starts` must be numeric (int or float). Found: {type(item)}"
            )

    return Counter([round(x - int(x), 5) for x in starts])


def approximate_pulse_match_with_priority_list(
    x: float,
    distance_threshold: float = 0.001,
    pulse_priority_list: Optional[list] = None,
) -> Optional[Fraction]:
    """
    Takes a float and an ordered list of possible pulses,
    returning the first pulse in the list to approximate the input float.

    This is a new function by MG as reported in [1].

    Parameters
    ----------
    x : float
        Input value to be approximated as a fraction.
    distance_threshold : float
        The distance threshold.
    pulse_priority_list : list[Fraction]
        Ordered list of pulse values to try.
        If unspecified, this defaults to 4, 3, 2, 1.5, 1, and the
        default output of [generate_n_smooth_numbers]
        [amads.time.meter.grid.generate_n_smooth_numbers].

    Returns
    -------
    Union(None, Fraction)
        None for no match, or a Fraction(numerator, denominator).

    References
    ----------
    [1] Gotham, Mark R. H. (2025). Keeping Score: Computational Methods for the
    Analysis of Encoded ("Symbolic") Musical Scores (v0.3)
     Zenodo. https://doi.org/10.5281/zenodo.14938027

    Examples
    --------
    >>> approximate_pulse_match_with_priority_list(5/6)
    Fraction(1, 6)

    >>> test_case = round(float(11/12), 5)
    >>> test_case
    0.91667

    >>> approximate_pulse_match_with_priority_list(test_case)
    Fraction(1, 12)

    Note that `Fraction(1, 12)` is included in the default list,
    while `Fraction(11, 12)` is not as that would be an extremely unusual tatum value.

    If the `distance_threshold` is very coarse, expect errors:
    >>> approximate_pulse_match_with_priority_list(29 + 1/12, distance_threshold=0.1)
    Fraction(1, 1)

    >>> approximate_pulse_match_with_priority_list(29 + 1/12, distance_threshold=0.01)
    Fraction(1, 12)

    """

    if pulse_priority_list is None:
        pulse_priority_list = [
            Fraction(4, 1),  # 4
            Fraction(3, 1),  # 3
            Fraction(2, 1),  # 2
            Fraction(3, 2),  # 1.5
        ]
        pulse_priority_list += generate_n_smooth_numbers(
            invert=True
        )  # 1, 1/2, 1/3, ...

    assert 0 not in pulse_priority_list
    assert None not in pulse_priority_list

    for p in pulse_priority_list:
        assert isinstance(p, Fraction)
        test_case = x / p
        diff = abs(round(test_case) - test_case)
        if diff < distance_threshold:
            return p

    return None


def generate_n_smooth_numbers(
    bases: list[int] = [2, 3], max_value: int = 100, invert: bool = True
) -> list:
    """
    Generates a list of “N-smooth” numbers up to a specified maximum value.

    An N-smooth number is a positive integer whose prime factors are all
    less than or equal to the largest number in the `bases` list.

    Parameters
    ----------
    max_value : int, optional
        The maximum value to generate numbers up to. Defaults to 100.
    bases : list, optional
        A list of base values (integers) representing the maximum allowed
        prime factor. Defaults to [2, 3].
    invert : bool = True
        If True, return not the n-smooth value x, but Fraction(1, x) instead.

    Returns
    -------
    list
        A list of N-smooth numbers.

    Examples
    --------
    Our metrical default:
    >>> generate_n_smooth_numbers(invert=False)  # all defaults `max_value=100`, `bases [2, 3]`
    [1, 2, 3, 4, 6, 8, 9, 12, 16, 18, 24, 27, 32, 36, 48, 54, 64, 72, 81, 96]

    Other cases:
    >>> generate_n_smooth_numbers(max_value=10, bases=[2], invert=False)
    [1, 2, 4, 8]
    >>> generate_n_smooth_numbers(max_value=20, bases=[2, 3], invert=False)
    [1, 2, 3, 4, 6, 8, 9, 12, 16, 18]
    >>> generate_n_smooth_numbers(max_value=50, bases=[2, 3, 5], invert=False)
    [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 27, 30, 32, 36, 40, 45, 48, 50]

    By default, invert is True
    >>> generate_n_smooth_numbers()[-1]
    Fraction(1, 96)

    """
    if not all(isinstance(b, int) and b > 1 for b in bases):
        raise ValueError("Bases must be a list of integers greater than 1.")

    if not isinstance(max_value, int) or max_value <= 0:
        raise ValueError("max_value must be a positive integer.")

    smooth_numbers = [1]
    queue = [1]

    while queue:
        current = queue.pop(0)
        for base in bases:
            next_num = current * base
            if next_num <= max_value:
                if next_num not in smooth_numbers:
                    smooth_numbers.append(next_num)
                    queue.append(next_num)
            else:
                break

    smooth_numbers.sort()

    if invert:
        return [Fraction(1, x) for x in smooth_numbers]
    else:
        return smooth_numbers


def get_tatum_from_floats_and_priorities(
    starts: Union[Iterable, Counter],
    pulse_priority_list: Optional[list] = None,
    distance_threshold: float = 1 / 24,
    proportion_threshold: Optional[float] = 0.999,
) -> Fraction:
    """
    Estimate metrical positions from floats.

    This function serves cases where temporal position values are defined
    relative to some origin, such as the time elapsed since:

    - the start of a piece (or section) in quarter notes (or some other
        consistent symbolic value)
    - the start of a measure (or other container), assuming those measures
        are of a constant duration.

    It serves use cases including the attempted retrieval of true metrical
    positions (fractions) from rounded versions thereof (floats).
    See notes at the top of this module, as well as
    for why standard algorithms fail at this task in a musical setting.

    This function serves those common cases where there is a need to balance
    between capturing event positions as accurately as possible while not
    making excessive complexity to account for a few anomalous notes.
    Most importantly, it enables the explicit prioritisation of common pulse
    divisions. Defaults prioritse 16x divsion over 15x, for example.


    Parameters
    ----------
    starts
        Any iterable giving the starting position of events.
        Each constituent start must be expressed relative to a reference value such that
        X.0 is the start of a unit,
        X.5 is the mid-point, etc.
        Floats are the main expected type here (as above); we seek to reverse engineer a plausible fraction from it.
        If any start is already an exact fraction, then it stays as it is, whatever the user setting:
        this functionality serves to improve the accuracy of timing data; there's no question of ever reducing it,
        even if user settings suggest that.
    pulse_priority_list
        The point of this function is to encode musically common pulse
        values. This argument defaults to numbers under 100 with prime
        factors of only 2 and 3 (“3-smooth”), in increasing order. The
        user can define any alternative list, optionally making use of
        `generate_n_smooth_numbers` for the purpose. See notes at
        `approximate_fraction_with_priorities`. Make sure this list is
        exhaustive: the function will raise an error if no match is found.
    distance_threshold
        The rounding tolerance between a temporal position multiplied by
        the bin value and the nearest integer.
        This is essential when working with floats, but can be set to any
        value the user prefers.
    proportion_threshold
        Optionally, set a proportional number of events notes to account for.
        This option requires that the `starts` be expressed as a Counter,
        ordered from most to least common.  The default of .999 means that
        once at least 99.9% of the source's notes are handled, we ignore the rest.
        This is achieved by iterating through the Counter object of values relative
        to the unit (e.g., 1.5 -> 0.5).
        This option should be chosen with care as, in this case,
        only the unit value and equal divisions thereof are considered.

    Examples
    --------

    A simple case, expressed in different ways.

    >>> tatum_1_6 = [0, 1/3, Fraction(1, 2), 1]
    >>> get_tatum_from_floats_and_priorities(tatum_1_6)
    Fraction(1, 6)

    >>> tatum_1_6 = [0, 0.333, 0.5, 1]
    >>> get_tatum_from_floats_and_priorities(tatum_1_6)
    Fraction(1, 6)

    An example of values from the BPSD dataset (Zeilter et al.).

    >>> from amads.time.meter import profiles
    >>> bpsd_Op027No1 = profiles.BPSD().op027No1_01 # /16 divisions of the measure and /12 too (from m.48). Tatum 1/48
    >>> get_tatum_from_floats_and_priorities(bpsd_Op027No1, distance_threshold=1/24) # proportion_threshold=0.999
    Fraction(1, 48)

    Change the `distance_threshold`
    >>> get_tatum_from_floats_and_priorities(bpsd_Op027No1, distance_threshold=1/6) # proportion_threshold=0.999
    Fraction(1, 12)

    Change the `proportion_threshold`
    >>> get_tatum_from_floats_and_priorities(bpsd_Op027No1, distance_threshold=1/24, proportion_threshold=0.80)
    Fraction(1, 24)

    """

    # Checks
    if not 0.0 < distance_threshold < 1.0:
        raise ValueError(
            "The `distance_threshold` tolerance must be between 0 and 1."
        )

    if pulse_priority_list is None:
        pulse_priority_list = generate_n_smooth_numbers(
            invert=True
        )  # 1, 1/2, 1/3, ...
    else:
        if not isinstance(pulse_priority_list, list):
            raise ValueError("The `pulse_priority_list` must be a list.")

        for i in pulse_priority_list:
            if not isinstance(i, Fraction):
                raise ValueError(
                    "The `pulse_priority_list` must consist entirely of Fraction objects "
                    "(which can include integers expressed as Fractions such as `Fraction(2, 1)`."
                )
            if i <= 0:
                raise ValueError(
                    "The `pulse_priority_list` items must be non-negative."
                )

    if proportion_threshold is not None:
        if not 0.0 < proportion_threshold < 1.0:
            raise ValueError(
                "When used (not `None`), the `proportion_threshold` must be between 0 and 1."
            )
        if isinstance(starts, Counter):
            for k in starts:
                if k > 1:
                    raise ValueError(
                        "The `starts` Counter must be measure-relative, and so have keys of less than 1."
                    )
        else:  # Convert to Counter (also includes type checks)
            starts = starts_to_int_relative_counter(starts)
        total = sum(starts.values())
        cumulative_count = 0

    pulses_needed = []

    for x in starts:
        if isinstance(
            x, Fraction
        ):  # Keep exact fraction as they are, whatever the user settings
            pulses_needed.append(x)
        elif (
            approximate_pulse_match_with_priority_list(
                x,
                pulse_priority_list=pulses_needed,  # Try those we're committed to first
                distance_threshold=distance_threshold,
            )
            is None
        ):  # No fit among those we have, try the rest of the user-permitted alternatives.
            new_pulse = approximate_pulse_match_with_priority_list(
                x,
                pulse_priority_list=pulse_priority_list,
                distance_threshold=distance_threshold,
            )
            if new_pulse is not None:
                pulses_needed.append(new_pulse)
            else:  # No fit among user-permitted alternatives.
                raise ValueError(
                    f"No match found for time point {x}, with the given arguments. "
                    "Try relaxing the `distance_threshold` or expanding the `pulse_priority_list`."
                )

        if proportion_threshold:
            # typing thinks cumulative_count, total could be undefined,
            # but they are defined if we reach here:
            cumulative_count += starts[x] / total  # type: ignore
            if cumulative_count > proportion_threshold:
                break

    current_gcd = pulses_needed[0]
    for i in range(1, len(pulses_needed)):
        current_gcd = fraction_gcd_pair(current_gcd, pulses_needed[i])

    return current_gcd


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
