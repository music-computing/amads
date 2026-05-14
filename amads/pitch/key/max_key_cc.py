"""
Maximal correlation value from key_cc algorithm.

Corresponds to maxkkcc in miditoolbox

Reference
---------
https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 70.
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

    This is an implementation of the maxkkcc function in Matlab MIDItoolbox.

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
