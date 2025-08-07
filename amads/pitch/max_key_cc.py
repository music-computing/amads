"""
Maximal correlation value from key_cc algorithm.
Corresponds to maxkkcc in miditoolbox

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=69
"""

from itertools import chain
from typing import List

from ..core.basics import Score
from .key import profiles as prof
from .key_cc import key_cc


def max_key_cc(
    score: Score,
    profile: prof._KeyProfile = prof.krumhansl_kessler,
    attribute_names: List[str] = ["major", "minor"],
    salience_flag: bool = False,
) -> float:
    """
    provides the maximal correlation value from calling key_cc
    with relevant parameters (see key_cc.py for more details)

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
    float
        the maximum correlation value computed in key_cc
    """
    corrcoef_pairs = key_cc(score, profile, attribute_names, salience_flag)
    # I'm too lazy to write my own for loop
    nested_coefs_iter = (coefs for (_, coefs) in corrcoef_pairs if coefs is not None)
    return max(chain.from_iterable(nested_coefs_iter))
