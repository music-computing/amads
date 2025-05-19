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
For example, Beethoven's Opus 10 Nr.2 Movement 1 is in 2/4 and from the start includes
a triplet 16ths turn figure in measure 1
(= 12x division, including float approximations of those position as 1.832, 1.916)
and also dotted rhythms pairing a dotted 16th with 32nd note from measure 5
(= 32x division, symbolic float approximation of 5.188).
So to catch these cases in the first 5 measures, we need the
lowest common multiple of 12 and 32, i.e., 96 bins.

In cases of extreme complexity, there may be a "need" for a
considerably greater number of bins per measure (shorter tatum).
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

import math
from collections import Counter
from typing import Iterable, Optional, Union


def starts_to_measure_relative_counter(starts: Iterable[float]):
    """
    Simple wrapper function to map an iterable (e.g., list or tuple) of floats to
    a measure-relative Counter, such that all the keys are geq 0, and less than 1.
    Includes rounding to 5dp.

    Examples
    --------
    >>> test_list = [0.0, 0.0, 0.5, 1.0, 1.5, 1.75, 2.0, 2.3333333333, 2.666667, 3.00000000000000001]
    >>> starts_to_measure_relative_counter(test_list)
    Counter({0.0: 5, 0.5: 2, 0.75: 1, 0.33333: 1, 0.66667: 1})
    """
    for item in starts:
        if not isinstance(item, (int, float)):
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

    Based on the R function by Peter Harrison at DOI: 10.1080/17459737.2015.1033024

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
    a_l = math.floor(x)
    b_l = 1
    a_r = math.floor(x) + 1
    b_r = 1
    a = round(x)
    b = 1

    while a / b < x_min or x_max < a / b:
        x_0 = 2 * x - a / b
        if x < a / b:
            a_r = a
            b_r = b
            k = math.floor((x_0 * b_l - a_l) / (a_r - x_0 * b_r))
            a_l = a_l + k * a_r
            b_l = b_l + k * b_r
        else:
            a_l = a
            b_l = b
            k = math.floor((a_r - x_0 * b_r) / (x_0 * b_l - a_l))
            a_r = a_r + k * a_l
            b_r = b_r + k * b_l
        a = a_l + a_r
        b = b_l + b_r

    return a, b


def generate_n_smooth_numbers(bases: list[int] = [2, 3], max_value: int = 100) -> list:
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

    Returns
    -------
    list
        A list of N-smooth numbers.

    Examples
    --------
    Our metrical default:
    >>> generate_n_smooth_numbers()  # all defaults `max_value=100`, `bases [2, 3]`
    [1, 2, 3, 4, 6, 8, 9, 12, 16, 18, 24, 27, 32, 36, 48, 54, 64, 72, 81, 96]

    Other cases:
    >>> generate_n_smooth_numbers(max_value=10, bases=[2])
    [1, 2, 4, 8]
    >>> generate_n_smooth_numbers(max_value=20, bases=[2, 3])
    [1, 2, 3, 4, 6, 8, 9, 12, 16, 18]
    >>> generate_n_smooth_numbers(max_value=50, bases=[2, 3, 5])
    [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 27, 30, 32, 36, 40, 45, 48, 50]

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
    return smooth_numbers


def tatum_pulses_per_measure(
    starts: Union[Iterable, Counter],
    pulse_priority_list: Optional[list] = None,
    distance_threshold: float = 1 / 24,
    proportion_threshold: float = 0.999,
):
    """
    This function serves music that is symbolically encoded in terms of measures,
    with events defined by (or convertable to) measure-start-relative positions
    and with the length of those measures remaining constant.
    It serves use cases including the attempted retrieval of true metrical positions
    from rounded versions thereof (floats).
    See notes at the top of this module, as well as at
    `float_gcd` and `approximate_fraction` for why standard algorithms fail at this task.

    This function serves those common cases where
    there is a need to balance between capturing event positions as accurately as possible while not
    making excessive complexity to account for a few anomalous notes.
    Most importantly, it enables the explicit prioritisation of common pulse divisions.
    Defaults prioritse 16x divsion over 15x, for example.


    Parameters
    ----------
    starts
        Any iterable giving the starting position of events.
        Must be expressed in measure-relative fashion such that
        X.0 is the start of a measure,
        X.5 is the mid-point of a measure, etc.
        Converted to a Counter object if not already in that format.
    pulse_priority_list
        The point of this function is to encode musically common pulse values.
        This argument defaults to numbers under 100 with prime factors of only 2 and 3
        ("3-smooth"), in increasing order.
        The user can define any alternative list, optionally making use of `generate_n_smooth_numbers` for the purpose.
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

    >>> from amads.time.meter import profiles
    >>> bpsd_Op027No1 = profiles.BPSD().op027No1_01
    >>> tatum_pulses_per_measure(bpsd_Op027No1, distance_threshold=1/24) # proportion_threshold=0.999
    48

    Change the `distance_threshold`
    >>> tatum_pulses_per_measure(bpsd_Op027No1, distance_threshold=1/6) # proportion_threshold=0.999
    12

    Change the `proportion_threshold`
    >>> tatum_pulses_per_measure(bpsd_Op027No1, distance_threshold=1/24, proportion_threshold=0.80)
    24

    """

    if not 0.0 < distance_threshold < 1.0:
        raise ValueError("The `distance_threshold` tolerance must be between 0 and 1.")

    if not 0.0 < proportion_threshold < 1.0:
        raise ValueError("The `proportion_threshold` must be between 0 and 1.")

    if pulse_priority_list is None:
        pulse_priority_list = [
            1,  # 2^{0} x 3^{0}
            2,  # 2^{1} x 3^{0}
            3,  # 2^{0} x 3^{1}
            4,  # 2^{2} x 3^{0}
            6,  # 2^{1} x 3^{1}
            8,  # 2^{3} x 3^{0}
            9,  # 2^{0} x 3^{2}
            12,  # 2^{2} x 3^{1}
            16,  # 2^{4} x 3^{0}
            18,  # 2^{1} x 3^{2}
            24,  # 2^{3} x 3^{1}
            27,  # 2^{0} x 3^{3}
            32,  # 2^{5} x 3^{0}
            36,  # 2^{2} x 3^{2}
            48,  # 2^{4} x 3^{1}
            54,  # 2^{1} x 3^{3}
            64,  # 2^{6} x 3^{0}
            72,  # 2^{3} x 3^{2}
            81,  # 2^{0} x 3^{4}
            96,  # 2^{5} x 3^{1}
        ]

    else:
        if not isinstance(pulse_priority_list, list):
            raise ValueError(
                "The `pulse_priority_list` must consist entirely of integers."
            )

        for i in pulse_priority_list:
            if not isinstance(i, int):
                raise ValueError(
                    "The `pulse_priority_list` must consist entirely of integers."
                )
            if i <= 0:
                raise ValueError(
                    "The `pulse_priority_list` must consist entirely of non-negative integers."
                )

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
    cumulative_count = 0
    pulses_needed = [1]

    for x in counter_starts:
        for p in pulses_needed:  # Try those we have first
            test_case = x * p
            diff = abs(round(test_case) - test_case)
            if diff < distance_threshold:
                break
            # else try the rest of `pulses_needed` and then move on to the user alternatives.

        for p in pulse_priority_list:  # Then try those on the user list  # TODO DRY
            test_case = x * p
            diff = abs(round(test_case) - test_case)
            if diff < distance_threshold:
                pulses_needed.append(p)
                break

        cumulative_count += counter_starts[x] / total
        if cumulative_count > proportion_threshold:
            break

    current_lcm = pulses_needed[0]
    for i in range(1, len(pulses_needed)):
        current_lcm = math.lcm(current_lcm, pulses_needed[i])

    return current_lcm


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
