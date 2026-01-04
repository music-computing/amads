"""
Approximating a fraction from a float
with a focus on the application to consonance.
"""

from math import floor


def approximate_fraction_consonance(x, d: float = 0.001) -> tuple:
    """
    Takes a float and approximates the value as a fraction.

    Based on [1] via an implementation in R by Peter Harrison.

    Parameters
    ----------
    x: float
        Input float to be approximated as a fraction.
    d: float
        Tolerance ratio.

    Returns
    -------
    tuple
        A tuple (numerator, denominator) representing the fraction.

    References
    ----------
    [1] Frieder Stolzenburg. 2015. Harmony perception by periodicity detection.
    DOI: 10.1080/17459737.2015.1033024

    Examples
    --------
    Fine for simple cases:

    >>> approximate_fraction_consonance(0.833)
    (5, 6)

    >>> approximate_fraction_consonance(0.875)
    (7, 8)

    >>> approximate_fraction_consonance(0.916)
    (11, 12)

    >>> approximate_fraction_consonance(0.6666)
    (2, 3)

    Liable to fail in both directions.

    >>> one_third = 1 / 3
    >>> one_third
    0.3333333333333333

    >>> approximate_fraction_consonance(one_third)
    (1, 3)

    >>> one_third_3dp = round(one_third, 3)
    >>> one_third_3dp
    0.333

    >>> approximate_fraction_consonance(one_third_3dp) # fail
    (167, 502)

    >>> approximate_fraction_consonance(one_third_3dp, d = 0.01) # ... fixed by adapting tolerance
    (1, 3)

    But this same tolerance adjustment makes errors for other, common musical values.
    15/16 is a common musical value for which the finer tolerance is effective:

    >>> approximate_fraction_consonance(0.938) # effective at default tolerance value
    (15, 16)

    >>> approximate_fraction_consonance(0.938, d = 0.01) # ... made incorrect by the same tolerance adaptation above
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


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
