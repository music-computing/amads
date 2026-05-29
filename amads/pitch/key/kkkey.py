"""
Maximal correlation value's attribute and index pair from key_cc algorithm.

Corresponds to kkkey in miditoolbox.

Reference
---------
https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, kkcc on page 69.
"""

from itertools import chain
from typing import List, Optional, Tuple

from amads.core.basics import Score
from amads.pitch.key import profiles as prof
from amads.pitch.key.key_cc import key_cc


def kkkey(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = ["major", "minor"],
    salience_flag: bool = False,
) -> Tuple[str, int]:
    """
    Finds the pitch profile with the highest correlation value.

    This is an implementation of the kkkey function in the Matlab MIDItoolbox.

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

    Raises
    ------
    RuntimeError
        Propagated from ``key_cc`` when correlations cannot be computed (for
        example, a score with zero pitch-class variance or equal weights).

    See Also
    --------
    key_cc
    """
    corrcoef_pairs = key_cc(score, profile, attribute_names, salience_flag)
    # list of pairs (attribute_name, [correlation coefficients])
    max_val_iter = (coefs for (_, coefs) in corrcoef_pairs if coefs is not None)
    # This code is a little unexpected: it first searches for the maximum
    # correlation value across all attributes and keys, then finds the
    # attribute and key index corresponding to that maximum value.
    max_val = max(chain.from_iterable(max_val_iter))
    nested_coefs_iter = (
        (attr, coefs.index(max_val))
        for (attr, coefs) in corrcoef_pairs
        if coefs is not None and max_val in coefs
    )
    return next(nested_coefs_iter)
