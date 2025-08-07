"""
This is a wrapper for key_cc to mimic the functionality of kkcc from
miditoolbox for convenience.

Author(s):
Tai Nakamura
Di Wang (diwang2)

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=68
"""

from itertools import chain
from typing import Tuple

from ..core.basics import Score
from .key import profiles as profiles
from .key_cc import key_cc


def kkcc(
    score: Score, profile_name: str = "KRUMHANSL-KESSLER", salience_flag: bool = False
) -> Tuple[float]:
    """
    kkcc wrapper on key_cc that provides the exact behavior of kkcc
    from miditoolbox.
    Namely:
    (1) Provides 3 string options for profile names
    (2) corresponds each string option to a relevant profile and attribute
    name list combination for key_cc that replicates the behavior of
    the relevant kkcc function call.

    Parameters
    ----------
    score (Score): The musical score to analyze.
    profile_name (str): string argument denoting the relevant miditoolbox
    string option for kkcc
    salience_flag (bool): If True, apply salience weighting to the pitch-class
    according to Huron & Parncutt (1993).

    Returns
    -------
    24-tuple of floats
        This denotes the 12 major correlation coefficients and 12 minor correlation
        coefficients from C to B in both major and minor keys, respectively.
    """
    if not isinstance(score, Score):
        raise ValueError("invalid score type!")
    # default is krumhansl kessler, and is what profile_name is set to by default
    profile = None
    attribute_list = None
    if profile_name == "KRUMHANSL-KESSLER":
        profile = profiles.krumhansl_kessler
        attribute_list = ["major", "minor"]
    elif profile_name == "TEMPERLEY":
        profile = profiles.temperley
        attribute_list = ["major", "minor"]
    elif profile_name == "ALBRECHT-SHANAHAN":
        profile = profiles.albrecht_shanahan
        attribute_list = ["major", "minor"]
    else:
        raise ValueError(f'profile_name = "{profile_name}" is not valid')

    # these checks are paranoia mainly to prevent future changes
    # from breaking the code after
    assert not (profile is None or attribute_list is None)
    assert isinstance(profile, profiles._KeyProfile)
    assert len(attribute_list) == 2

    corrcoef_pairs = key_cc(score, profile, attribute_list, salience_flag)
    # check integrity of corrcoef correspondences and whether or not they abide
    # to the output agreed on in key_cc
    assert len(corrcoef_pairs) == len(attribute_list)
    assert all(
        attr_name == target_attr and len(coefs) == 12
        for ((attr_name, coefs), target_attr) in zip(corrcoef_pairs, attribute_list)
    )

    # pattern match, then collect individual coefficients into
    # a single tuple to get our final corrcoefs
    nested_coefs_iter = (coefs for (_, coefs) in corrcoef_pairs)
    corrcoefs = tuple(chain.from_iterable(nested_coefs_iter))

    return corrcoefs
