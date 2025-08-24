"""
Filters the list of attribute names to the ones that contain
the maximal cross-correlation value for the scores in C,
corresponds to keymode in miditoolbox.

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=65
"""

from typing import List, Optional

from ..core.basics import Score
from .key import profiles as prof
from .key_cc import key_cc


def keymode(
    score: Score,
    profile: prof._KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = ["major", "minor"],
    salience_flag: bool = False,
) -> List[str]:
    """
    Filters the list of attribute names so that their 0-crosscorrelation
    value or C-crosscorrelation value are the maximal among all the attributes.

    The indices correspond to the following keys in ascending order:
    0 -> C, 1 -> C#, ..., 11 -> B

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
    List[str]
        filtered list of attribute names
    """
    corrcoef_pairs = key_cc(score, profile, attribute_names, salience_flag)

    # I'm too lazy to write my own for loop so please forgive this
    c_max_val_iter = (coefs[0] for (_, coefs) in corrcoef_pairs if coefs is not None)
    c_max_val = max(c_max_val_iter)
    keymode_attributes = [
        attr
        for (attr, coefs) in corrcoef_pairs
        if coefs is not None and coefs[0] == c_max_val
    ]
    return keymode_attributes
