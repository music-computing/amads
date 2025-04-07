def sign(x: float) -> [-1, 0, 1]:
    """
    Basic, static function for returning the sign of a numeric value.

    >>> sign(-15)
    -1

    >>> sign(-1)
    -1

    >>> sign(-0.5)
    -1

    >>> sign(-0)
    0

    >>> sign(+0)
    0

    >>> sign(+0.5)
    1

    >>> sign(15.2)
    1
    """
    if x is None:
        return None
    else:
        return bool(x > 0) - bool(x < 0)
