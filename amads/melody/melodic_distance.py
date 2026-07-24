"""
Melodic accent salience according to Thomassen's model.

Ports the `melaccent` function in Midi Toolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 70.
"""

from collections.abc import Callable
from typing import Tuple

import numpy as np

from amads.algorithms.norm import pnorm_distance
from amads.core.basics import Score

# ivdist1, ivdist2, pcdist1, pcdist2
from amads.pitch.ivdist1 import interval_distribution_1
from amads.pitch.ivdist2 import interval_distribution_2
from amads.pitch.pcdist1 import pitch_class_distribution_1
from amads.pitch.pcdist2 import pitch_class_distribution_2


repr = ["ivdist1", "ivdist2", "pcdist1", "pcdist2", "durdist1", "durdist2"]

# calculating the numbers and putting them into the score

# Need to think about metric... there seems to be a ton of metric problems here
# how do I make a metric?
def melodic_distance(
    score1: Score,
    score2: Score,
    repr: str = "pcdist1",
    metric: str = "taxi",
    samples: int = 10,
    rescale: bool = False,
) -> float:
    """
    Measurement of distance between specified feature data extracted from two
    Score objects.

    This function currently does not support all the functionality present
    in the miditoolbox version. Namely, there is no support for melcontour
    and combcontour repr options, which means the samples argument is
    not in use as of now. As more feature branches are included, more support
    will be included. 

    NOTE: (documentation for limits on repr_func and metric_func)
    Enforce dimensionality 

    Parameters
    ----------
    score1 : Score
        The first Score object.
    score2 : Score
        The second Score object.
    repr : str
        # This is not a representation though...
        The representation used for comparison.
    metric : str
        There are two options here:
        (1) A norm metric as specified in norm.py
        (2) "cosine" to specify the angle between the two vectors obtained
        from repr.
    samples : int
        Number of samples for contour representation.
    rescale : bool
        Rescale distance to similarity value between 0 and 1.

    Returns
    -------
    float
        Value representing the distance between the two scores under the given
        representation and metric.
    """
    if repr == "pcdist1":
        dist1 = pitch_class_distribution_1(score1)
        dist2 = pitch_class_distribution_1(score2)
    elif repr == "pcdist2":
        dist1 = pitch_class_distribution_2(score1)
        dist2 = pitch_class_distribution_2(score2)
    elif repr == "ivdist1":
        dist1 = interval_distribution_1(score1)
        dist2 = interval_distribution_1(score2)
    elif repr == "ivdist2":
        dist1 = interval_distribution_2(score1)
        dist2 = interval_distribution_2(score2)
    elif repr == "melcontour":
        raise ValueError("melcontour not implemented on this feature branch")
    elif repr == "combcontour":
        raise ValueError("combcontour not implemented on this feature branch")
    else:
        raise ValueError("Unsupported representation type.")

    dist1_data = np.array(dist1.data)
    dist2_data = np.array(dist2.data)
    rescale_val = 0
    if metric == "taxi":
        rescale_val = 1
        distance = pnorm_distance(dist1_data, dist2_data, 1)
    elif metric == "euc":
        rescale_val = 1
        distance = pnorm_distance(dist1_data, dist2_data, 2)
    elif metric == "cosine":
        rescale_val = 0.15
        distance = np.dot(dist1_data, dist2_data) / (
            np.linalg.norm(dist1_data) * np.linalg.norm(dist2_data)
        )
    else:
        raise ValueError("Unsupported metric type.")

    if rescale:
        if distance < rescale_val:
            distance = (2 * (rescale_val - distance) + distance) / 2
        else:
            distance = (2 * (distance - rescale_val) + rescale_val) / 2

    return distance
