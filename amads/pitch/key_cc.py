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
from collections import deque
from dataclasses import fields
from typing import List, Optional, Tuple, Union

import numpy as np

from ..core.basics import Score
from .key import profiles as prof
from .pcdist1 import pcdist1


def key_cc(
    score: Score,
    profile: prof._KeyProfile = prof.krumhansl_kessler,
    attribute_names: Optional[List[str]] = None,
    salience_flag: bool = False,
) -> List[Tuple[str, Optional[Tuple[float]]]]:
    """
    Calculate the correlation coefficients of a score's pitch-class distribution
    with a key profile from profiles.py.
    Return a list of tuples, each containing the attribute name
    and the corresponding correlation coefficients.

    Parameters
    ----------
    score: Score
        The score to analyze.

    profile: prof._KeyProfile
        The key profile to use for analysis.

    attribute_names: List[str]
        List of attribute names to compute correlations for.

    salience_flag: bool
        If True, apply salience weighting to the pitch-class according
        to Huron & Parncutt (1993).

    Returns
    -------
    List[Tuple[str, Optional[Tuple[float]]]]
        A list of tuples where each tuple contains the attribute name and the
        corresponding correlation coefficients. If an attribute is invalid
        or None, it will return (attribute_name, None).

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
        sal = deque([1, 0, 0.25, 0, 0, 0.5, 0, 0, 0.33, 0.17, 0.2, 0])
        salm = np.zeros((12, 12))
        for i in range(salm.shape[0]):
            salm[i] = sal
            sal.rotate(1)
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

        # Convert to numpy array or handle special cases
        # Check if attr_value is a tuple of tuples(non-transpositionally equivalent)
        profile_matrix = _get_profile_matrix(attr_value)
        correlations = tuple(_compute_correlations(pcd, profile_matrix))
        if any(math.isnan(val) for val in correlations):
            raise RuntimeError(
                "key_cc has encountered a score or key profile with equal pitch weights!"
            )
        results.append((attr_name, correlations))

    return results


def _get_profile_matrix(
    attr_value: Union[Tuple[prof.PitchProfile], prof.PitchProfile]
) -> np.ndarray:
    """
    Retrieves the profile matrix from a given attribute value

    Parameters
    ----------
    attr_value
        attribute value that is a valid profile value within a profile dataclass

    Returns
    -------
    np.ndarray
        12x12 matrix where each row represents a key profile in a given pitch
        with the following encoding (row and column-wise):
        0 -> C, 1 -> C#, ... , 11 -> B

    Raises
    ------
    ValueError
        If the attribute value is not a valid profile
    """
    # check the only two valid pitch profile cases
    if isinstance(attr_value, prof.PitchProfile):
        profile_tuple = attr_value.as_tuple()
        # Handle asymmetric profiles (tuple of tuples)
        profile_matrix = _create_transposed_profile_matrix(profile_tuple)
        return profile_matrix
    elif (
        isinstance(attr_value, tuple)
        and len(attr_value) == 12
        and all(isinstance(elem, prof.PitchProfile) for elem in attr_value)
    ):
        assym_profile_tuple = tuple(elem.as_tuple() for elem in attr_value)
        profile_matrix = _handle_asymmetric(assym_profile_tuple)
        return profile_matrix
    else:
        raise ValueError("attribute value is invalid to a _KeyProfile dataclass")


def _create_transposed_profile_matrix(profile_tuple: Tuple[float]) -> np.ndarray:
    """
    Create a 12x12 matrix with transposed versions of the profile.
    Assumes that profile is transpositionally equivalent.

    Parameters
    ----------
    profile_tuple : tuple[float]
        12-float tuple representation of a pitch-class distribution

    Returns
    -------
    np.ndarray
        12x12 matrix where each row is the profile transposed to a different key
        with the following encoding (row and column-wise):
        0 -> C, 1 -> C#, ... , 11 -> B
    """
    profile_deque = deque(profile_tuple)
    profile_matrix = np.zeros((12, 12))
    for i in range(12):
        profile_matrix[i] = profile_deque
        profile_deque.rotate(1)
    return profile_matrix


def _handle_asymmetric(assym_profile_tuple: Tuple[Tuple[float]]) -> np.ndarray:
    """
    Handle asymmetric profiles (e.g., QuinnWhite major_assym, minor_assym).

    These profiles contain separate key-specific profiles, one for each key.
    (Not transpositionally equivalent)

    Parameters
    ----------
    assym_profile_tuple : tuple of tuples
        Nested tuple structure containing key-specific profiles.
        Expected structure: ((C_profile_tuple), (C#_profile_tuple), ..., (B_profile_tuple))
        where each key_profile is a 12-element tuple/list.

    Returns
    -------
    np.ndarray
        12x12 matrix where each row is a key-specific profile
        with the following encoding (row and column-wise):
        0 -> C, 1 -> C#, ... , 11 -> B

    Raises
    ------
    ValueError
        If the input does not have shape (12, 12) or is not a valid asymmetric profile.
    """
    try:
        # Convert tuple of tuples to numpy array
        profile_matrix = np.array(assym_profile_tuple)

        # Verify each non-transpositional profile attribute has 12 pitch classes
        if profile_matrix.shape != (12, 12):
            raise ValueError(
                f"malformed profile matrix with shape {profile_matrix.shape}, expected (12, 12)"
            )

        return profile_matrix

    except Exception as e:
        raise ValueError(f"Failed to process asymmetric profile: {e}")


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
