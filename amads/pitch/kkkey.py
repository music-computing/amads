"""
Maximal correlation value's attribute and index pair from key_cc algorithm.
Corresponds to kkkey in miditoolbox

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=68
"""

from itertools import chain
from typing import List, Tuple

from ..core.basics import Score
from .key import profiles as prof
from .key_cc import key_cc


def kkkey(
    score: Score,
    profile: prof._KeyProfile = prof.krumhansl_kessler,
    attribute_names: List[str] = ["major", "minor"],
    salience_flag: bool = False,
) -> Tuple[str, int]:
    """
    provides the associated attribute name and index of the
    maximal correlation value for each attribute list
    from calling key_cc with relevant parameters
    (see key_cc.py for more details)

    The indices correspond to the following keys in ascending order:
    0 -> C, 1 -> C#, ..., 12 -> B

    Parameters
    ----------
    score (Score): The musical score to analyze.
    profile (Profile): Relevant key profile to obtain data from
    attribute_names: List of strings to relevant attribute names
    within the profile
    salience_flag: boolean to indicate whether we want to turn on
    salience weights in key_cc

    Returns
    -------
    tuple[str, int]
        the attribute name and key index of the corresponding maximum
        correlation coefficient
    """
    corrcoef_pairs = key_cc(score, profile, attribute_names, salience_flag)

    # I'm too lazy to write my own for loop so please forgive this
    max_val_iter = (coefs for (_, coefs) in corrcoef_pairs if coefs is not None)
    max_val = max(chain.from_iterable(max_val_iter))
    nested_coefs_iter = (
        (attr, coefs.index(max_val))
        for (attr, coefs) in corrcoef_pairs
        if max_val in coefs
    )
    return next(nested_coefs_iter)
