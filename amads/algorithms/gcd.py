"""
Basic, local calculations of the greatest common divisor (GCD)
at a central point in the code base for wide applicability.

Rhythm-specific modifications are stored there.
"""

__author__ = "Mark Gotham"


from fractions import Fraction


def gcd_pair(a, b):
    """
    Calculates the greatest common divisor (GCD) of two integers using the
    Euclidean algorithm.
    """
    while b:
        a, b = b, a % b
    return a


def float_gcd_pair(a: float, b: float = 1.0, rtol=1e-05, atol=1e-08) -> float:
    """
    Calculate the greatest common divisor (GCD) for values a and b given the specified
    relative and absolute tolerance (rtol and atol).
    With thanks to Euclid,
    `fractions.gcd`, and
    [stackexchange](https://stackoverflow.com/questions/45323619/).

    Tolerance values should be set in relation to the granularity (e.g., pre-rounding) of the input data.

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
    >>> round(float_gcd_pair(0.6667), 3) # failure
    0.0

    Leaving the value the same, but changing the tolerance to accomodate:
    >>> round(float_gcd_pair(0.6667, atol=0.001, rtol=0.001), 3) # success
    0.333

    But this same kind of tolerance adjustment can make errors for other, common musical values.
    15/16 is a common musical value for which the finer tolerance is effective:

    >>> fifteen_sixteenths = 15/16
    >>> round(1 / float_gcd_pair(fifteen_sixteenths)) # success
    16

    >>> round(1 / float_gcd_pair(fifteen_sixteenths, atol=0.001, rtol=0.001)) # success
    16

    >>> fifteen_sixteenths_3dp = round(fifteen_sixteenths, 3)
    >>> round(1 / float_gcd_pair(fifteen_sixteenths_3dp)) # failure
    500

    >>> round(1 / float_gcd_pair(fifteen_sixteenths_3dp, atol=0.001, rtol=0.001)) # failure
    500

    """
    t = min(abs(a), abs(b))
    while abs(b) > rtol * t + atol:
        a, b = b, a % b
    return a


def local_lcm_pair(a, b):
    """Local implementation of the Lowest Common Multiple (LCM)."""
    return a * b // gcd_pair(a, b)


def fraction_gcd_pair(x: Fraction, y: Fraction) -> Fraction:
    """
    Compute the GCD of two fractions using the
    equivalence between gcd(a/b, c/d) and gcd(a, c)/lcm(b, d)

    This function compares exactly two fractions (x and y).
    For a longer list, use `fraction_gcd_list`.

    Return
    ------
    Fraction (which is always simplified).

    >>> fraction_gcd_pair(Fraction(1, 2), Fraction(2, 3))
    Fraction(1, 6)

    """
    return Fraction(
        gcd_pair(x.numerator, y.numerator), local_lcm_pair(x.denominator, y.denominator)
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
        current_gcd = fraction_gcd_pair(current_gcd, fraction_list[i])
    return current_gcd
