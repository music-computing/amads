"""
Basic, local calculations of the greatest common divisor (GCD)
at a central point in the code base for wide applicability.
Parameter-specific adaptations are in the relevant place (e.g., `amads.time.meter`).

The module is organised in a kind of logical quadrant for
data type (e.g., integer vs fraction)
and
number (a single pair vs many pairwise calculations).

<small>**Author**: Mark Gotham</small>
"""

__author__ = "Mark Gotham"


from fractions import Fraction

# -----------------------------------------------------------------------------

# Direct operations on pair of values, known to be integer, float, fraction.


def integer_gcd_pair(a: int, b: int) -> int:
    """
    Calculates the greatest common divisor (GCD) of two integers using the
    Euclidean algorithm.

    >>> integer_gcd_pair(0, 2)
    2

    >>> integer_gcd_pair(15, 16)
    1

    >>> integer_gcd_pair(8, 16)
    8

    """
    while b:
        a, b = b, a % b
    return a


def float_gcd_pair(a: float, b: float = 1.0, rtol=1e-05, atol=1e-08) -> float:
    """
    Calculate approximate greatest common divisor (GCD) for values a and b given the specified
    relative and absolute tolerance (`rtol` and `atol`).
    With thanks to Euclid,
    `fractions.gcd`, and
    [stackexchange](https://stackoverflow.com/questions/45323619/).

    Tolerance values should be set in relation to the granularity
    (e.g., pre-rounding) of the input data.

    Parameters
    ----------
    a: float
        Any float value.
    b: float
        Any float value, though typically 1.0 (default) for our use case
        of measure-relative positioning.
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

    Leaving the value the same, but changing the tolerance to accommodate:
    >>> round(float_gcd_pair(0.6667, atol=0.001, rtol=0.001), 3) # success
    0.333

    But this same kind of tolerance adjustment can make errors for other,
    common musical values.
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


def local_lcm_pair(a: int, b: int) -> int:
    """
    Local implementation of the Lowest Common Multiple (LCM).

    >>> local_lcm_pair(8, 16)
    16

    >>> local_lcm_pair(2, 3)
    6

    """
    return a * b // integer_gcd_pair(a, b)


def fraction_gcd_pair(x: Fraction, y: Fraction) -> Fraction:
    """
    Compute the GCD of two fractions using the
    equivalence between gcd(a/b, c/d) and gcd(a, c)/lcm(b, d)

    This function compares exactly two fractions (x and y).
    For a longer list, use `fraction_gcd_list`.

    Returns
    -------
    Fraction
        The GCD of `x` and `y`, which is always simplified.

    Examples
    --------
    >>> fraction_gcd_pair(Fraction(1, 2), Fraction(2, 3))
    Fraction(1, 6)

    """
    return Fraction(
        integer_gcd_pair(x.numerator, y.numerator),
        local_lcm_pair(x.denominator, y.denominator),
    )


# -----------------------------------------------------------------------------

# Combined operations on iterable (list, tuple, ... ) of values.


def calculate_gcd(numbers: list):
    """
    Compute GCD.
    Wrapper function when you don't know whether the type of the numeric data.
    If the value type is known (integer, fractions, float),
    use the more specific `{type}_gcd` function.

    Here, the logic is that integers and fractions are lossless, but floats are not
    so process the former first and fractions
    and then the latter as needed.

    >>> calculate_gcd([1, 2])
    Fraction(1, 1)

    >>> calculate_gcd([1, Fraction(1, 2), 2])
    Fraction(1, 2)

    >>> calculate_gcd([0, 1/2])
    0.5

    >>> calculate_gcd([0, Fraction(1, 2), 1/2])
    Fraction(1, 2)

    >>> gcd = calculate_gcd([0, Fraction(1, 2), 4/12])
    >>> round(gcd, 3)
    0.167

    """
    floats = [num for num in numbers if isinstance(num, float)]
    ints_fractions = [num for num in numbers if not isinstance(num, float)]

    if ints_fractions:
        gcd = Fraction(ints_fractions[0])
        for num in ints_fractions[1:]:
            gcd = fraction_gcd_pair(Fraction(num), gcd)
    else:
        gcd = floats.pop(0)  # seed with first float

    for f in floats:
        gcd = float_gcd_pair(f, gcd)

    return gcd


def integer_gcd(integers: list[int]) -> int:
    """
    Compute GCD where the elements are known/asserted to be integers.
    See `integer_gcd_pair`.

    Returns
    -------
    tuple
        The GCD of all elements in the list of integers.

    Examples
    --------
    >>> integer_gcd([0, 2, 4])
    2

    >>> integer_gcd([0, 15, 16])
    1

    >>> integer_gcd([0, 8, 16])
    8

    """
    gcd = integers[0]
    for i in range(1, len(integers)):
        gcd = integer_gcd_pair(gcd, integers[i])
    return gcd


def fraction_gcd(fractions: list[Fraction]) -> Fraction:
    """
    Compute GCD where all elements are known/asserted to be Fractions.
    See `fraction_gcd_pair`

    Returns
    -------
    Fraction
        The GCD of all Fractions in `fraction_list`.

    Examples
    --------
    >>> fraction_gcd([Fraction(1, 2), Fraction(2, 3), Fraction(5, 12)])
    Fraction(1, 12)

    """
    gcd = fractions[0]
    for i in range(1, len(fractions)):
        gcd = fraction_gcd_pair(gcd, fractions[i])
    return gcd


def float_gcd(floats: list[float], rtol=1e-05, atol=1e-08) -> float:
    """
    Calculate GCD for values given the specified
    relative and absolute tolerance (rtol and atol).

    If the values are known to be
    integers use `integer_gcd`,
    fractions
    and if the type is not known, use `calculate_gcd`.

    Parameters
    ----------
    floats: list[float]
        Any float value.
    rtol
        the relative tolerance
    atol
        the absolute tolerance

    """
    gcd = floats[0]
    for i in range(1, len(floats)):
        gcd = float_gcd_pair(gcd, floats[i], rtol=rtol, atol=atol)
    return gcd
