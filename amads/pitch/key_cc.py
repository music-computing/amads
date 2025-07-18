"""
Correlations of pitch-class distribution with Krumhansl-Kessler tonal
hierarchies
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
from typing import List, Tuple, Optional, Union

import numpy as np
from .key import profiles as prof

from ..core.basics import Score
from .pcdist1 import pcdist1


def key_cc(
    score: Score,
    profile: prof._KeyProfile,
    attribute_names: List[str],
    salienceFlag: bool = False,
) -> List[Tuple[str, Optional[np.ndarray]]]:
    # Get pitch-class distribution
    pcd = np.array([pcdist1(score, False)])
    
    # Apply salience weighting if requested
    if salienceFlag:
        sal = deque([1, 0, 0.25, 0, 0, 0.5, 0, 0, 0.33, 0.17, 0.2, 0])
        salm = np.zeros((12, 12))
        for i in range(salm.shape[0]):
            salm[i] = sal
            sal.rotate(1)
        pcd = np.matmul(pcd, salm) #shape (1, 12)
    
    results = []
    
    for attr_name in attribute_names:
        try:
            # Get the attribute from the profile
            attr_value = getattr(profile, attr_name)
            
            if attr_value is None:
                print(f"Warning: Attribute '{attr_name}' exists but is None for profile '{profile.name}'")
                results.append((attr_name, None))
                continue
            
            # Convert to numpy array or handle special cases
            # Check if attr_value is a tuple of tuples(QuinnWhite)
            if isinstance(attr_value, tuple) and len(attr_value) > 0 and isinstance(attr_value[0], tuple):
                # Handle QuinnWhite asymmetric profiles (tuple of tuples)
                if profile.name == "QuinnWhite" and attr_name.endswith("_assym"):
                    profile_matrix = _handle_quinn_white_asymmetric(attr_value)
                    correlations = _compute_correlations(pcd, profile_matrix)
                    results.append((attr_name, correlations))
                else:
                    print(f"Warning: Nested tuple structure not supported for '{attr_name}' in profile '{profile.name}'")
                    results.append((attr_name, None))
                continue
            
            attr_array = np.array(attr_value)
            
            # Handle different profile types
            if attr_array.ndim == 1 and len(attr_array) == 12:
                # Standard transpositionally equivalent profile
                profile_matrix = _create_transposed_matrix(attr_array)
                correlations = _compute_correlations(pcd, profile_matrix)
                results.append((attr_name, correlations))
                
            else:
                print(f"Warning: Attribute '{attr_name}' has unexpected shape {attr_array.shape} for profile '{profile.name}'")
                results.append((attr_name, None))
                
        except AttributeError:
            print(f"Warning: Attribute '{attr_name}' does not exist for profile '{profile.name}'")
            results.append((attr_name, None))
        except Exception as e:
            print(f"Error processing attribute '{attr_name}' for profile '{profile.name}': {e}")
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


def _handle_quinn_white_asymmetric(attr_value) -> np.ndarray:
    """
    Handle QuinnWhite asymmetric profiles (major_assym, minor_assym).
    
    These profiles contain 12 separate key-specific profiles, one for each key.
    
    Parameters
    ----------
    attr_value : tuple of tuples
        Nested tuple structure containing 12 key-specific profiles
        
    Returns
    -------
    np.ndarray
        12x12 matrix where each row is a key-specific profile
    """
    # Convert tuple of tuples to numpy array
    profile_matrix = np.array(attr_value)
    
    # Verify shape
    if profile_matrix.shape != (12, 12):
        raise ValueError(f"Expected shape (12, 12) for Quinn-White asymmetric profile, got {profile_matrix.shape}")
    
    return profile_matrix


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
    combined_matrix = np.concatenate((pcd, profile_matrix), axis=0) #shape (25, 12)
    correlation_matrix = np.corrcoef(combined_matrix)
    
    # Extract correlations between pcd (first row) and all profiles
    correlations = correlation_matrix[0, 1:]
    
    return correlations