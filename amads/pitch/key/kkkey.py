"""
Maximal correlation value's attribute and index pair from key_cc algorithm.

Corresponds to kkkey in miditoolbox.

Reference
---------
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=68
"""

from itertools import chain
from typing import List, Optional, Tuple

from amads.core.basics import Score
from amads.pitch.key import profiles as prof
from amads.pitch.key.key_cc import key_cc

# TODO: include exceptions comments


def kkkey(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = ["major", "minor"],
    salience_flag: bool = False,
) -> Tuple[str, int]:
    """
    Finds the pitch profile with the highest correlation value.

    Within `profile` there are multiple profiles named by attributes.
    This function returns the "best" attribute (string) and the best
    key (int) where the int corresponds to the 12 keys in order:
    0 -> C, 1 -> C#, ..., 11 -> B. (see key_cc.py for more details)

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
    tuple[str, int]
        The attribute name and key with the highest correlation coefficient.

    See Also
    --------
    key_cc
    """
    corrcoef_pairs = key_cc(score, profile, attribute_names, salience_flag)

    max_val_iter = (coefs for (_, coefs) in corrcoef_pairs if coefs is not None)
    max_val = max(chain.from_iterable(max_val_iter))
    nested_coefs_iter = (
        (attr, coefs.index(max_val))
        for (attr, coefs) in corrcoef_pairs
        if coefs is not None and max_val in coefs
    )
    return next(nested_coefs_iter)
