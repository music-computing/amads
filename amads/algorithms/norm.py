"""
Local implementation of standard normalization routines centrally for use in various functions.
The local implementation serves to obviate the need for external libraries (e.g., scipy) in basic cases.

Comparisons on this module support any pair of profiles.
Example use cased include pitch class profile matching for 'best key' measurement,
and the metrical equivalent.
"""

import numpy as np

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------

l1_names = ["sum", "manhattan", "city", "cityblock", "city block", "taxicab", "l1"]
l2_names = ["euclidean", "l2"]
max_names = ["max", "maximum", "inf", "infinity"]


def normalize(
    profile: list,
    method: str = "Euclidean",
    round_output: bool = False,
    round_places: int = 3,
) -> np.array:
    """
    Normalize usage profiles in standard ways.

    Parameters
    -------
    profile: list
        Any 1-D list of numeric data.

    method: str
        The desired normalization routine. Chose from any of
        'Euclidean' or 'l2' (scale so that the vector length is 1);
        'Sum', 'Manhattan', or 'l1' (divide each value by the total across the profile);
        'max', 'maximum', 'inf' or 'infinity' (divide each value by the largest value).
        These strings are not case-sensitive.

    round_output: bool
        Optionally, round the output values (default False).

    round_places: int
        If rounding, how many decimal places to use (default=3). Moot if `round_output` if False (default).

    Returns
    -------
    np.array

    Examples
    --------
    >>> toy_example = [0, 1, 2, 3, 4]
    >>> normalize(toy_example, method="l1")
    array([0. , 0.1, 0.2, 0.3, 0.4])

    >>> normalize(toy_example, method="l2")
    array([0.        , 0.18257419, 0.36514837, 0.54772256, 0.73029674])

    >>> normalize(toy_example, method="l2", round_output=True, round_places=3)
    array([0.   , 0.183, 0.365, 0.548, 0.73 ])

    >>> normalize(toy_example, method="max")
    array([0.  , 0.25, 0.5 , 0.75, 1.  ])

    """

    if np.max(profile) == 0:
        return profile  # All 0s: don't divide by 0 (or indeed do anything!)

    method = method.lower()
    if method in l1_names:
        norm_ord = 1
    elif method in l2_names:
        norm_ord = 2
    elif method in max_names:
        norm_ord = np.inf
    else:
        raise ValueError(
            f"Invalid method. Must be one of {l1_names + l2_names + max_names}"
        )
    norm_dist = profile / np.linalg.norm(profile, ord=norm_ord)

    if round_output:
        return np.round(norm_dist, round_places)
    else:
        return norm_dist


def shared_length(profile_1: list, profile_2: list) -> int:
    """
    Simple checks that two lists are of the same length.
    If so, returns the length of the list; if not, raises an error.

    >>> shared_length([1, 2], [2, 1])
    2
    """
    ln1 = len(profile_1)
    ln2 = len(profile_2)
    if ln2 != ln1:
        raise ValueError(f"Lengths (currently {ln1} and {ln2}) must match")
    else:
        return ln1


def manhattan_distance(profile_1: list, profile_2: list, norm_: bool = False) -> float:
    """
    The 'l1' aka 'Manhattan' distance between two points in N dimensional space.
    List length checks are included.
    Normalization is optional (defaults to False).

    Examples
    --------

    >>> profile_1 = [0, 1, 2, 3, 4]
    >>> profile_2 = [1, 2, 3, 4, 5]
    >>> manhattan_distance(profile_1, profile_2)
    5.0

    >>> manhattan_distance(profile_1, profile_2, norm_=True)
    0.2

    """
    shared_length(profile_1, profile_2)
    if norm_:
        profile_1 = normalize(profile_1, "l1")
        profile_2 = normalize(profile_2, "l1")
    return float(sum([abs(profile_1[n] - profile_2[n]) for n in range(len(profile_1))]))


def euclidean_distance(profile_1: list, profile_2: list, norm_: bool = False) -> float:
    """
    The Euclidean distance between two points
    is the length of the line segment connecting them in N dimensional space and
    is given by the Pythagorean formula.
    List length checks are included.
    Normalization is optional (defaults to False).

    Examples
    --------
    >>> profile_1 = [0, 1, 2, 3, 4]
    >>> profile_2 = [1, 2, 3, 4, 5]
    >>> euclidean_distance(profile_1, profile_2)
    2.23606797749979

    >>> euclidean_distance(profile_1, profile_2, norm_=True)
    0.17474594224380802

    """
    shared_length(profile_1, profile_2)

    if norm_:
        profile_1 = normalize(profile_1, "l2")
        profile_2 = normalize(profile_2, "l2")
    return float(
        np.sqrt(
            sum([(profile_1[n] - profile_2[n]) ** 2 for n in range(len(profile_1))])
        )
    )


def pnorm_distance(profile_1: np.array, profile_2: np.array, p: int = 2):
    """
    Calculate the p-norm distance between two vectors.

    Parameters
    ----------
    profile_1: list
        A 1-D numpy array of numeric data.
    profile_2: list
        Another 1-D numpy array of numeric data.
    p: int
        The order of the normalisation.
        The default is 2 (for Euclidean distance), alternatives include 1 for Manhattan.

    Returns
    -------
    float: The p-norm distance.

    Example
    -------
    >>> profile_1 = [0, 1, 2, 3, 4]
    >>> profile_2 = [1, 2, 3, 4, 5]
    >>> pnorm_distance(profile_1, profile_2)
    2.23606797749979

    """
    vector1 = np.array(profile_1)
    vector2 = np.array(profile_2)
    diffs = np.abs(vector1 - vector2)
    return float(np.sum(diffs**p) ** (1 / p))


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
