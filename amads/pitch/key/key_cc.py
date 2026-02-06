"""
Cross-correlations between pitch-class distributions and key profiles.


<small>**Author**: Tai Nakamura, Di Wang</small>


Reference
---------
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=68 for more details
"""

__author__ = ["Tai Nakamura", "Di Wang"]

import math
from dataclasses import fields
from typing import List, Optional, Tuple

import numpy as np

import amads.pitch.key.profiles as prof
from amads.core.basics import Score
from amads.pitch.pcdist1 import pitch_class_distribution_1


def key_cc(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = None,
    salience_flag: bool = False,
) -> List[Tuple[str, Optional[Tuple[float]]]]:
    """
    Calculate the correlation coefficients with specific pitch profiles.

    A score's pitch-class distribution is computed and generally,
    KeyProfiles come from existing data in profiles.py. Within each
    KeyProfile are one or more distributions, e.g. for "major" and
    "minor" keys, so you must specify which distributions you want
    correlations for.  Return a list of tuples, each containing the
    attribute name (e.g., "major") and the corresponding 12 correlation
    coefficients.

    When `salience_flag` is True, the pitch class distribution from the score
    (pcd) is replaced by a new one (pcd2) where each element is a weighted sum
    of the elements of pcd. The weights are rotated for each element. Thus,
    pcd2[i] = sum(pcd[j] * weight[(j + i) mod 12].

    The idea here is that the perception of significance of a certain pitch in
    a score depends not only on its naive unweighted frequency, but also (to a
    lesser extent) on the frequency of functionally harmonic pitches present
    in the score.

    Parameters
    ----------
    score: Score
        The score to analyze.

    profile: prof.KeyProfile
        The key profile to use for analysis.

    attribute_names: Optional[List[str]]
        List of attribute names that denote the particular PitchProfiles
        within the KeyProfile to compute correlations for. An example
        `attribute_names` for profile prof.vuvan could be
        `["natural_minor", "harmonic_minor"]`, which says to
        compute the cross-correlation between the pitch-class distribution
        of the score and both prof.vuvan's natural_minor and prof.vuvan's
        harmonic_minor. `None` can be supplied when we want to specify all
        valid pitch profiles within a given key profile.

    salience_flag: bool
        If True, apply salience pitch-wise bias weights to the score's
        pitch-class distribution.

    Returns
    -------
    List[Tuple[str, Optional[Tuple[float]]]]
        A list of tuples where each tuple contains the attribute name, from
        parameter `attribute_names`, and the corresponding 12-tuple of
        correlation coefficients. If an attribute name does not reference
        a valid data field within the specified key profile, it will yield
        `(`*attribute_name*`, None)`.

    Raises
    ------
    RuntimeError
        If the score or key profile contains equal pitch weights,
        resulting in correlation not being able to be computed.
    """

    # Get pitch-class distribution
    pcd = np.array([pitch_class_distribution_1(score, weighted=False).data])

    # Apply salience weighting if requested
    if salience_flag:
        # NOTE: this is not the weight vector,
        # the salience weights for the c-pitch in the pitch-class distribution
        # is [1, 0, 0.2, 0.17, 0.33, 0, 0, 0.5, 0, 0, 0.25, 0].
        # These weights form the first column of the 12x12 matrix salm.
        sal2 = [1, 0, 0.25, 0, 0, 0.5, 0, 0, 0.33, 0.17, 0.2, 0] * 2
        salm = np.zeros((12, 12))
        for i in range(salm.shape[0]):
            salm[i] = sal2[12 - i : 23 - i]
        pcd = np.matmul(pcd, salm.T)  # shape (1, 12)

    results = []

    true_attribute_names = attribute_names

    if true_attribute_names is None:
        true_attribute_names = [
            f.name
            for f in fields(profile)
            if f.name not in ["name", "literature", "about"]
        ]

    for attr_name in true_attribute_names:
        # ! we should probably treat the special attributes as proper attribute names
        if attr_name in ["name", "literature", "about"]:
            print(
                f"Warning! Attempting to access metadata in profile '{profile.name}"
            )
            results.append((attr_name, None))
            continue
        # Get the attribute from the profile
        attr_value = getattr(profile, attr_name, None)

        if attr_value is None:
            print(
                f"Warning: Attribute '{attr_name}' is invalid or None in profile '{profile.name}'"
            )
            results.append((attr_name, None))
            continue
        profiles_matrix = attr_value.as_canonical_matrix()
        correlations = tuple(_compute_correlations(pcd, profiles_matrix))
        if any(math.isnan(val) for val in correlations):
            raise RuntimeError(
                "key_cc has encountered either an invalid or equal weight"
                " score, or invalid pitch profile\n"
                f"correlations = {list(correlations)}\n"
                f"score pitch-class distribution = {list(pcd)}\n"
                f"profiles matrix = \n{profiles_matrix}\n"
            )
        results.append((attr_name, correlations))

    return results


def _compute_correlations(
    pcd: np.ndarray, profile_matrix: np.ndarray
) -> np.ndarray:
    """
    Compute correlations between pitch-class distribution and profile matrix.

    Parameters
    ----------
    pcd : np.ndarray
        Pitch-class distribution (1x12)
    profile_matrix : np.ndarray
        Profile matrix (Nx12 where N is number of keys/profiles)

    Returns
    -------
    np.ndarray
        Correlation coefficients
    """
    # Combine pcd and profile matrix for correlation computation
    combined_matrix = np.concatenate(
        (pcd, profile_matrix), axis=0
    )  # shape (25, 12)
    correlation_matrix = np.corrcoef(combined_matrix)

    # Extract correlations between pcd (first row) and all profiles
    correlations = correlation_matrix[0, 1:]

    return correlations
