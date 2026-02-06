"""
Assuming key of C, find a score's mode based on key profiles using key_cc.

This function is primarily used to estimate the mode, an attribute of a given
KeyProfile collection. The key of C is assumed, and cross-correlation with
profiles for other keys are ignored.

Reference
---------
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=65
"""

from typing import List, Optional

import amads.pitch.key.profiles as prof
from amads.core.basics import Score
from amads.pitch.key.key_cc import key_cc


def keymode(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = ["major", "minor"],
    salience_flag: bool = False,
) -> List[str]:
    """
    Find the mode based on cross-correlation values.

    Returns the list of mode(s) whose profile(s) have a maximal
    cross-correlation with the score's pitch distribution.

    Parameters
    ----------
    score: Score
        The musical score to analyze.
    profile: Profile
        collection of profile data for different modes (attributes)
    attribute_names: Optional[List[str]]
        List of attribute names that denote the particular PitchProfiles
        within the KeyProfile and generally indicate different modes.
        See profiles.py for more details.
    salience_flag: bool
        Indicate whether we want to turn on salience weights in key_cc
        which is used to compute the cross-correlations.

    Returns
    -------
    List[str]
        List of attribute names that have maximal cross-correlation with
        the score's profile (usually, length will be 1).

    See Also
    --------
    key_cc
    """

    # This algorithm is not very efficient: It computes 12 correlations
    # for each mode, but only uses one. Then, it iterates through the
    # results, once to find the maximum, and again to form a list of
    # modes that achieve that maximum.

    corrcoef_pairs = key_cc(score, profile, attribute_names, salience_flag)

    c_max_val_iter = (
        coefs[0] for (_, coefs) in corrcoef_pairs if coefs is not None
    )
    c_max_val = max(c_max_val_iter)
    keymode_attributes = [
        attr
        for (attr, coefs) in corrcoef_pairs
        if coefs is not None and coefs[0] == c_max_val
    ]
    return keymode_attributes
