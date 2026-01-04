"""
Maximal correlation value from key_cc algorithm.

Corresponds to maxkkcc in miditoolbox

Reference
---------
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=69
"""

from itertools import chain
from typing import List, Optional

import amads.pitch.key.profiles as prof
from amads.core.basics import Score
from amads.pitch.key.key_cc import key_cc


def max_key_cc(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = ["major", "minor"],
    salience_flag: bool = False,
) -> float:
    """
    Find the maximal correlation value after calling key_cc
    with relevant parameters (see key_cc.py for more details)

    Parameters
    ----------
    score: Score
        The musical score to analyze.
    profile: Profile
        The key profile to use for analysis.
    attribute_names: Optional[List[str]]
        List of attribute names that denote the particular PitchProfiles
        within the KeyProfile to compute correlations for.
        See key_cc for more details
    salience_flag: bool
        indicate whether we want to turn on salience weights in key_cc

    Returns
    -------
    float
        the maximum correlation value computed in key_cc
    """
    corrcoef_pairs = key_cc(score, profile, attribute_names, salience_flag)
    nested_coefs_iter = (
        coefs for (_, coefs) in corrcoef_pairs if coefs is not None
    )
    return max(chain.from_iterable(nested_coefs_iter))
