"""
Relative mode calculated by taking the difference between the highest correlating major and minor key profiles.


<small>**Author**: Tuomas Eerola</small>


Reference
---------
Eerola, T., & Schutz, M. (2025). Major-minorness in tonal music: Evaluation of relative mode estimation using expert ratings and audio-based key-finding principles. Psychology of Music, 0(0). https://doi.org/10.1177/03057356251326065
"""

__author__ = ["Tuomas Eerola"]

import numpy as np

from amads.core.basics import Score
from amads.pitch.key.kkcc import kkcc


def relative_mode(
    score: Score,
    profile_name: str = "ALBRECHT-SHANAHAN",
    salience_flag: bool = False,
) -> float:
    """Return a single relative-mode scalar (-1 to +1) for the given score and profile.

    The scalar is computed as (max_major_corr - max_minor_corr) * 10 where
    max_major_corr is the maximum correlation between the score's pitch-class
    distribution and the profile's major keys, and max_minor_corr is the
    analogous maximum for minor keys. Multiplication by 10 is just a convenience operation
    to take the values more closely between -1 and +1.

    """
    # compute correlations between the chosen profile and the score's pitch-class distribution, with optional salience weighting
    keycorrs = kkcc(
        score, profile_name=profile_name, salience_flag=salience_flag
    )
    # Note. kkcc had a bug with the salience weighting, which has been fixed in the current version. TE

    # Compute the relative mode value as the difference between the maximum major and maximum minor correlations, multiplied by 3 for scaling
    value = (float(np.max(keycorrs[:12])) - float(np.max(keycorrs[12:]))) * 3.0
    # Different distance metrics (cosine, euclidean) have not been implemented in the kkcc function, but could be implemented in the future. TE
    return value
