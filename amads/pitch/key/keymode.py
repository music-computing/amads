"""
For a given key profile and attribute name list, find the individual pitch
profiles that have the strongest cross-correlation between the score to analyze
and the profile at pitch C.

This function is primarily used to find the maximum similarity of a score's
pitch-class distribution to the C pitch-class distribution in the various pitch
profiles of a key profile.
! (Honestly, I never saw a use-case for this function in midi-toolbox)

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

    Filters the list of attribute names so that their 0th cross-correlation
    value or C-pitch cross-correlation value are the maximal among all the
    attributes that are compared

    The indices correspond to the following keys in ascending order:
    0 -> C, 1 -> C#, ..., 11 -> B

    Parameters
    ----------
    score: Score
        The musical score to analyze.
    profile: Profile
        collection of profile data for different modes (attributes)
    attribute_names: Optional[List[str]]
        List of attribute names that denote the particular PitchProfiles
        within the KeyProfile to compute correlations for.
        See key_cc for more details
    salience_flag: bool
        indicate whether we want to turn on salience weights in key_cc

    See Also
    --------
    key_cc

    Returns
    -------
    List[str]
        list of attribute names that have maximal cross-correlation with
        the score's profile (usually, length will be 1).
    """
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
