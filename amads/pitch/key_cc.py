"""
Correlations of pitch-class distribution with Krumhansl-Kessler tonal
hierarchies
Author(s): Tai Nakamura, Di Wang
Description:
    Compute correlation of a score's pitch distribution with
    a specified pitch histogram in 12 transpositions.
See https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=68 for more details
"""

import math
from dataclasses import fields
from typing import List, Optional, Tuple

import numpy as np

from ..core.basics import Score
from .key import profiles as prof
from .pcdist1 import pcdist1


def key_cc(
    score: Score,
    profile: prof.KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = None,
    salience_flag: bool = False,
) -> List[Tuple[str, Optional[Tuple[float]]]]:
    """
    Calculate the correlation coefficients of a score's pitch-class distribution
    with specific pitch profiles in key profile from profiles.py.
    The names of the pitch profiles to specify in the key profile is
    in attribute_names.
    Return a list of tuples, each containing the attribute name
    and the corresponding correlation coefficients.

    Parameters
    ----------
    score: Score
        The score to analyze.

    profile: prof.KeyProfile
        The key profile to use for analysis.

    attribute_names: Optional[List[str]]
        List of attribute names that denote the particular PitchProfiles
        within the KeyProfile to compute correlations for.
        An example of a valid key profile, attribute names combination is
        something like (prof.vuvan, ["natural_minor", "harmonic_minor"]),
        which specifies key_cc to compute the crosscorrelation between
        the pitch-class distribution of the score and both prof.vuvan.natural_minor
        and prof.vuvan.harmonic_minor.
        None can be supplied when we want to specify all valid pitch
        profiles within a given key profile.

    salience_flag: bool
        If True, apply salience weighting to the pitch-class according
        to Huron & Parncutt (1993).

    Returns
    -------
    List[Tuple[str, Optional[Tuple[float]]]]
        A list of tuples where each tuple contains the attribute name and the
        corresponding 12-tuple of correlation coefficients. If an attribute
        name does not reference a valid data field within the specified key
        profile, it will yield (attribute_name, None).

    Raises
    ------
    RuntimeError
        If the score or key profile contains equal pitch weights,
        resulting in correlation not being able to be computed.
    """

    # Get pitch-class distribution
    # NOTE: pcdist1 still returns a pitch-class distribution in the form of
    # a 12-tuple of floats.
    # Eventually, need to make the transition to returning a distribution object
    pcd = np.array([pcdist1(score, False)])

    # Apply salience weighting if requested
    if salience_flag:
        sal = [1, 0, 0.25, 0, 0, 0.5, 0, 0, 0.33, 0.17, 0.2, 0]
        salm = np.zeros((12, 12))
        for i in range(salm.shape[0]):
            salm[i] = sal
            sal = sal[-1:] + sal[:-1]  # rotate right
        pcd = np.matmul(pcd, salm)  # shape (1, 12)

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
            print(f"Warning! Attempting to access metadata in profile '{profile.name}")
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
        profiles_matrix = attr_value.as_matrix_canonical()
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


def _compute_correlations(pcd: np.ndarray, profile_matrix: np.ndarray) -> np.ndarray:
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
    combined_matrix = np.concatenate((pcd, profile_matrix), axis=0)  # shape (25, 12)
    correlation_matrix = np.corrcoef(combined_matrix)

    # Extract correlations between pcd (first row) and all profiles
    correlations = correlation_matrix[0, 1:]

    return correlations
