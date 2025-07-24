"""
Inspired by miditoolbox's kkkey.
Calculates the index of the maximum correlation value for a collection of
attributes in a profile

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=68
"""

from typing import List, Tuple

from ..core.basics import Score
from .key import profiles as prof
from .key_cc import key_cc


def key_attr_maxkey(
    score: Score,
    profile: prof._KeyProfile = prof.krumhansl_kessler,
    attribute_names: List[str] = ["major", "minor"],
    salience_flag: bool = False,
) -> List[Tuple[str, int]]:
    """
    Calculates the index of the maximum correlation value for
    each attribute name and a corresponding profile (see key_cc.py for more details)

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
    List
        list of (attribute name, index of max coefficient value for said attribute) pairs
        Encoding for argmax indices: 0 = C, 1 = C#, ... , 12 = B
    """
    key_cc_pairs = key_cc(score, profile, attribute_names, salience_flag)

    return [(attr, cc_vals.index(max(cc_vals))) for attr, cc_vals in key_cc_pairs]
