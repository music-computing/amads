"""
The module seeks to find the smallest metrical pulse level (broadly, "tatum")
in response to a source and user tolerance settings.

In the simplest case, a source records its metrical positions exactly,
including fractional values as needed.
We provide functionality for standard, general algorithms in these cases
(greatest common denominator and fraction estimation)
which are battle tested and computationally efficient.

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

In cases of extreme complexity, there may be a "need" for a
considerably shorter tatum pulse (and, equivalently, a greater number of bins).
This is relevant for some modern music, as well as cases where
grace notes are assigned a specific metrical position/duration
(though in many encoded standards, grace notes are not assigned separate metrical positions).

Moreover, there are musical sources that do not encode fractional time values, but rather approximation with floats.
These include any:
- frame-wise representations of time (including MIDI and any attempted transcription from audio),
- processing via code libraries that likewise convert fractions to floats,
- secondary representations like most CSVs.
As division by 3 leads to rounding, approximation, and floating point errors,
and as much music involves those divisions, this is widely relevant.

The standard algorithms often fail in these contexts, largely because symbolic music
tends to prioritise certain metrical divisions over others.
For example, 15/16 is a commonly used metrical position (largely because 16 is a power of 2), but 14/15 is not.
That being the case, while 14/15 might be a better mathematical fit for approximating a value,
it is typically incorrect as the musical solution.
We can use the term "incorrect" advisedly here because
the floats are secondary representations of a known fractional ground truth.
Doctests demonstrate some of these cases.
"""

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------

from collections import Counter
from fractions import Fraction
from math import floor, gcd
from typing import Iterable, Optional, Union


def starts_to_int_relative_counter(starts: Iterable[float]):
    """
    Simple wrapper function to map an iterable (e.g., list or tuple) of floats to
    integer-relative values (e.g., 1.5 -> 0.5) such that all the keys are geq 0, and less than 1,
    and to a Counter of those values (e.g., 1.5 and 2.5 -> 0.5: 2).

    Includes rounding to 5dp. This may change.

    Examples
    --------
    >>> test_list = [0.0, 0.0, 0.5, 1.0, 1.5, 1.75, 2.0, 2.3333333333, 2.666667, 3.00000000000000001]
    >>> starts_to_int_relative_counter(test_list)
    Counter({0.0: 5, 0.5: 2, 0.75: 1, 0.33333: 1, 0.66667: 1})
    """
    for item in starts:
        if not isinstance(item, (int, float, Fraction)):
            raise TypeError(
                f"All items in `starts` must be numeric (int or float). Found: {type(item)}"
            )

    return Counter([round(x - int(x), 5) for x in starts])


def float_gcd(a: float, b: float = 1.0, rtol=1e-05, atol=1e-08) -> float:
    """
    Calculate the greatest common divisor (GCD) for values a and b given the specified
    relative and absolute tolerance (rtol and atol).
    With thanks to Euclid,
    `fractions.gcd`, and
    [stackexchange](https://stackoverflow.com/questions/45323619/).

    Tolerance values should be set in relation to the granulaity (e.g., pre-rounding) of the input data.

    Parameters
    ----------
    a
        Any float value.
    b
        Any float value, though typically 1.0 for our use case of measure-relative positioning.
    rtol
        the relative tolerance
    atol
        the absolute tolerance


    Examples
    --------

    At risk of failure in both directions.
    Default tolerance values fail simple cases (2 / 3 to 4d.p.):
    >>> round(float_gcd(0.6667), 3) # failure
    0.0

    Leaving the value the same, but changing the tolerance to accomodate:
    >>> round(float_gcd(0.6667, atol=0.001, rtol=0.001), 3) # success
    0.333

    But this same kind of tolerance adjustment can make errors for other, common musical values.
    15/16 is a common musical value for which the finer tolerance is effective:

    >>> fifteen_sixteenths = 15/16
    >>> round(1 / float_gcd(fifteen_sixteenths)) # success
    16

    >>> round(1 / float_gcd(fifteen_sixteenths, atol=0.001, rtol=0.001)) # success
    16

    >>> fifteen_sixteenths_3dp = round(fifteen_sixteenths, 3)
    >>> round(1 / float_gcd(fifteen_sixteenths_3dp)) # failure
    500

    >>> round(1 / float_gcd(fifteen_sixteenths_3dp, atol=0.001, rtol=0.001)) # failure
    500

    """
    t = min(abs(a), abs(b))
    while abs(b) > rtol * t + atol:
        a, b = b, a % b
    return a


def local_lcm(a, b):
    """Local implementation of the Lowest Common Multiple (LCM)."""
    return a * b // gcd(a, b)


def fraction_gcd(x: Fraction, y: Fraction) -> Fraction:
    """
    Compute the GCD of two fractions using the
    equivalence between gcd(a/b, c/d) and gcd(a, c)/lcm(b, d)

    This function compares exactly two fractions (x and y).
    For a longer list, use `fraction_gcd_list`.

    Return
    ------
    Fraction (which is always simplified).

    >>> fraction_gcd(Fraction(1, 2), Fraction(2, 3))
    Fraction(1, 6)

    """
    return Fraction(
        gcd(x.numerator, y.numerator), local_lcm(x.denominator, y.denominator)
    )


def fraction_gcd_list(fraction_list: list[Fraction]):
    """
    Iterate GCD comparisons over a list of Fractions.
    See `fraction_gcd`

    >>> fraction_gcd_list([Fraction(1, 2), Fraction(2, 3), Fraction(5, 12)])
    Fraction(1, 12)

    """
    current_gcd = fraction_list[0]
    for i in range(1, len(fraction_list)):
        current_gcd = fraction_gcd(current_gcd, fraction_list[i])
    return current_gcd


def approximate_fraction(x, d: float = 0.001):
    """
    Takes a float and approximates the value as a fraction.

    Args:
    -------
    x: Input float to be approximated as a fraction.
    d: Tolerance ratio.

    Returns
    -------
    A tuple (numerator, denominator) representing the fraction.

    Based on [1] via an implementation in R by Peter Harrison.

    References
    [1] Frieder Stolzenburg. 2015. Harmony perception by periodicity detection. DOI: 10.1080/17459737.2015.1033024

    Examples
    --------
    Fine for simple cases:

    >>> approximate_fraction(0.833)
    (5, 6)

    >>> approximate_fraction(0.875)
    (7, 8)

    >>> approximate_fraction(0.916)
    (11, 12)

    >>> approximate_fraction(0.6666)
    (2, 3)

    Liable to fail in both directions.

    >>> one_third = 1 / 3
    >>> one_third
    0.3333333333333333

    >>> approximate_fraction(one_third)
    (1, 3)

    >>> one_third_3dp = round(one_third, 3)
    >>> one_third_3dp
    0.333

    >>> approximate_fraction(one_third_3dp) # fail
    (167, 502)

    >>> approximate_fraction(one_third_3dp, d = 0.01) # ... fixed by adapting tolerance
    (1, 3)

    But this same tolerance adjustment makes errors for other, common musical values.
    15/16 is a common musical value for which the finer tolerance is effective:

    >>> approximate_fraction(0.938) # effective at default tolerance value
    (15, 16)

    >>> approximate_fraction(0.938, d = 0.01) # ... made incorrect by the same tolerance adaptation above
    (14, 15)
    """

    x_min = (1 - d) * x
    x_max = (1 + d) * x
    a_l = floor(x)
    b_l = 1
    a_r = floor(x) + 1
    b_r = 1
    a = round(x)
    b = 1

    while a / b < x_min or x_max < a / b:
        x_0 = 2 * x - a / b
        if x < a / b:
            a_r = a
            b_r = b
            k = floor((x_0 * b_l - a_l) / (a_r - x_0 * b_r))
            a_l = a_l + k * a_r
            b_l = b_l + k * b_r
        else:
            a_l = a
            b_l = b
            k = floor((a_r - x_0 * b_r) / (x_0 * b_l - a_l))
            a_r = a_r + k * a_l
            b_r = b_r + k * b_l
        a = a_l + a_r
        b = b_l + b_r

    return a, b


def approximate_pulse_match_with_priority_list(
    x: float,
    distance_threshold: float = 0.001,
    pulse_priority_list: Optional[list] = None,
) -> Optional[Fraction]:
    """
    Takes a float and an ordered list of possible pulses,
    returning the first pulse in the list to approximate the input float.

    Params:
    -------
    x:
        Input value (typically a float) to be approximated as a fraction.
    distance_threshold:
        The distance threshold.
    pulse_priority_list:
        Ordered list of pulse values to try.
        If unspecified, this defaults to 4, 3, 2, 1.5, 1, and the default output of `generate_n_smooth_numbers`.

    Returns
    -------
    None (no match) or a Fraction(numerator, denominator).

    This is a new function by MG as reported in [1].

    References
    [1] Gotham forthcoming. TODO

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
    Generates a list of "N-smooth" numbers up to a specified maximum value.

    An N-smooth number is a positive integer whose prime factors are all
    less than or equal to the largest number in the 'bases' list.

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


def get_tatum(
    starts: Union[Iterable, Counter],
    pulse_priority_list: Optional[list] = None,
    distance_threshold: float = 1 / 24,
    proportion_threshold: Optional[float] = 0.999,
):
    """
    This function serves cases where temporal position values are defined by reference to a constant value.
    Examples include the symbolic time to have elapsed since:
    - the start of a piece (or section) in quarter notes (or some other consistent symbolic value)
    - the start of a measure (or other container), assuming those measures are of a constant duration.

    It serves use cases including the attempted retrieval of true metrical positions (fractions)
    from rounded versions thereof (floats).
    See notes at the top of this module, as well as at
    `float_gcd` and `approximate_fraction` for why standard algorithms fail at this task in a musical setting.

    This function serves those common cases where
    there is a need to balance between capturing event positions as accurately as possible while not
    making excessive complexity to account for a few anomalous notes.
    Most importantly, it enables the explicit prioritisation of common pulse divisions.
    Defaults prioritse 16x divsion over 15x, for example.


    Parameters
    ----------
    starts
        Any iterable giving the starting position of events.
        Must be expressed relative to a reference value such that
        X.0 is the start of a unit,
        X.5 is the mid-point, etc.
    pulse_priority_list
        The point of this function is to encode musically common pulse values.
        This argument defaults to numbers under 100 with prime factors of only 2 and 3
        ("3-smooth"), in increasing order.
        The user can define any alternative list, optionally making use of `generate_n_smooth_numbers` for the purpose.
        See notes at `approximate_fraction_with_priorities`.
        Make sure this list is exhaustive: the function will raise an error if no match is found.
    distance_threshold
        The rounding tolerance between a temporal position multiplied by the bin value and the nearest integer.
        This is essential when working with floats, but can be set to any value the user prefers.
    proportion_threshold
        Optionally, set a proportional number of events notes to account for.
        The default of .999 means that once at least 99.9% of the source's notes are handled, we ignore the rest.
        This is achieved by iterating through a Counter object of values relative to the unit.
        E.g., 1.5 -> 0.5.
        This option should be chosen with care as, in this case,
        only the unit value and equal divisions thereof are considered.

    Examples
    --------

    A simple case, expressed in different ways.

    >>> tatum_1_6 = [0, 1/3, Fraction(1, 2), 1]
    >>> get_tatum(tatum_1_6)
    Fraction(1, 6)

    >>> tatum_1_6 = [0, 0.333, 0.5, 1]
    >>> get_tatum(tatum_1_6)
    Fraction(1, 6)

    An example of values from the BPSD dataset (Zeilter et al.).

    >>> from amads.time.meter import profiles
    >>> bpsd_Op027No1 = profiles.BPSD().op027No1_01 # /16 divisions of the measure and /12 too (from m.48). Tatum 1/48
    >>> get_tatum(bpsd_Op027No1, distance_threshold=1/24) # proportion_threshold=0.999
    Fraction(1, 48)

    Change the `distance_threshold`
    >>> get_tatum(bpsd_Op027No1, distance_threshold=1/6) # proportion_threshold=0.999
    Fraction(1, 12)

    Change the `proportion_threshold`
    >>> get_tatum(bpsd_Op027No1, distance_threshold=1/24, proportion_threshold=0.80)
    Fraction(1, 24)

    """

    if not 0.0 < distance_threshold < 1.0:
        raise ValueError("The `distance_threshold` tolerance must be between 0 and 1.")

    if proportion_threshold is not None:
        if not 0.0 < proportion_threshold < 1.0:
            raise ValueError(
                "When used (not `None`), the `proportion_threshold` must be between 0 and 1."
            )

    if pulse_priority_list is None:
        pulse_priority_list = generate_n_smooth_numbers(invert=True)  # 1, 1/2, 1/3, ...
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
        if (
            approximate_pulse_match_with_priority_list(
                x,
                pulse_priority_list=pulses_needed,
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
            cumulative_count += starts[x] / total
            if cumulative_count > proportion_threshold:
                break

    current_gcd = pulses_needed[0]
    for i in range(1, len(pulses_needed)):
        current_gcd = fraction_gcd(current_gcd, pulses_needed[i])

    return current_gcd


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
