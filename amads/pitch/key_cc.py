"""
Correlations of pitch-class distribution with Krumhansl-Kessler tonal
hierarchies
Author(s): Tai Nakamura
Date: [2025-03-11]
Description:
    Computes correlation coefficients of a score's pitch distribution
    to a specified standard pitch histogram that is key transposed
    over all 24 standard keys
Usage:
    [Add basic usage examples or import statements]
Original doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=68
Reference(s):
    Albrecht, J., & Shanahan, D. (2013). The Use of Large Corpora to
        Train a New Type of Key-Finding Algorithm. Music Perception: An
        Interdisciplinary Journal, 31(1), 59-67.

    Krumhansl, C. L. (1990). Cognitive Foundations of Musical Pitch.
        New York: Oxford University Press.

    Huron, D., & Parncutt, R. (1993). An improved model of tonality
        perception incorporating pitch salience and echoic memory.
        Psychomusicology, 12, 152-169.

    Temperley, D. (1999). What's key for key? The Krumhansl-Schmuckler
        key-finding algorithm reconsidered. Music Perception: An Interdisciplinary
        Journal, 17(1), 65-100.
"""

from collections import deque
from typing import List, Optional, Tuple

import numpy as np

from ..core.basics import Score
from .key import profiles as prof
from .pcdist1 import pcdist1


def key_cc(
    score: Score,
    profile: prof._KeyProfile = prof.krumhansl_kessler,
    attribute_names: List[str] = ["major", "minor"],
    salience_flag: bool = False,
) -> List[Tuple[str, Optional[Tuple[float]]]]:
    # TODO: comments for key_cc
    # Get pitch-class distribution
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

    for attr_name in attribute_names:
        # Get the attribute from the profile
        attr_value = getattr(profile, attr_name)

        if attr_value is None:
            print(
                f"Warning: Attribute '{attr_name}' exists but is None for profile '{profile.name}'"
            )
            results.append((attr_name, None))
            continue

        # Convert to numpy array or handle special cases
        # Check if attr_value is a tuple of tuples(non-transpositionally equivalent)
        if (
            isinstance(attr_value, tuple)
            and len(attr_value) > 0
            and isinstance(attr_value[0], tuple)
        ):
            # Handle asymmetric profiles (tuple of tuples)
            profile_matrix = _handle_asymmetric(attr_value)
            correlations = _compute_correlations(pcd, profile_matrix)
            results.append((attr_name, tuple(correlations)))
            continue

        attr_array = np.array(attr_value)

        # Handle different profile types
        if attr_array.ndim == 1 and len(attr_array) == 12:
            # Standard transpositionally equivalent profile
            profile_matrix = _create_transposed_matrix(attr_array)
            correlations = _compute_correlations(pcd, profile_matrix)
            results.append((attr_name, tuple(correlations)))
        else:
            print(
                f"Warning: Attribute '{attr_name}' has unexpected shape {attr_array.shape} for profile '{profile.name}'"
            )
            results.append((attr_name, None))

    return results


def _create_transposed_matrix(profile: np.ndarray) -> np.ndarray:
    """
    Create a 12x12 matrix with transposed versions of the profile.
    Assumes that profile is transpositionally equivalent.

    Parameters
    ----------
    profile : np.ndarray
        12-element profile array

    Returns
    -------
    np.ndarray
        12x12 matrix where each row is the profile transposed to a different key
    """
    profile_deque = deque(profile)
    profile_matrix = np.zeros((12, 12))
    for i in range(12):
        profile_matrix[i] = profile_deque
        profile_deque.rotate(1)
    return profile_matrix


def _handle_asymmetric(attr_value) -> np.ndarray:
    """
    Handle asymmetric profiles (e.g., QuinnWhite major_assym, minor_assym).

    These profiles contain separate key-specific profiles, one for each key.
    (Not transpositionally equivalent)

    Parameters
    ----------
    attr_value : tuple of tuples
        Nested tuple structure containing key-specific profiles.
        Expected structure: ((key0_profile), (key1_profile), ..., (key11_profile))
        where each key_profile is a 12-element tuple/list.

    Returns
    -------
    np.ndarray
        12x12 matrix where each row is a key-specific profile
    """
    try:
        # Convert tuple of tuples to numpy array
        profile_matrix = np.array(attr_value)

        # Verify it's a 2D array
        if profile_matrix.ndim != 2:
            raise ValueError(
                f"Expected 2D array from tuple of tuples, got {profile_matrix.ndim}D"
            )

        # Verify each non-transpositional profile attribute has 12 pitch classes
        if profile_matrix.shape[1] != 12:
            raise ValueError(
                f"Each profile must have 12 pitch classes, got {profile_matrix.shape[1]}"
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
