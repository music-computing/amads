"""
Projection of pitch-class distribution on a self-organizing map
(Toiviainen & Krumhansl, 2003)

Description:
    Computes the projection of a pitch-class distribution on a self-organizing
    map, and visualize it.

    Unlike the original miditoolbox implementation in matlab, the SOM here
    is allowed to use any key profile in literature as long as it contains
    valid major and minor pitch profile fields. See key/profiles.py for more
    details.

    ! remove this after testing and experimentation
    Things to watch out for:
        - crank the learning rate low enough so that order of selection for the
        very small (profile) data set doesn't really matter. (let's start with 0.2)
        - Make sure the weight propagation is a toroid (circular propagation based
        off of 1-norm?).
        - non-normalized weights? (prefer normalized ones so far due to how
        inconsistent literature weights are otherwise)

See https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=66 for more details
"""

# for function types
from typing import Tuple

import numpy as np
from matplotlib.figure import Figure

from amads.core.basics import Concurrence
from amads.pitch.key import keysomdata as ksom
from amads.pitch.pcdist1 import pcdist1

# ! make sure to get rid of some of the random asserts used in development


def keysom(
    note_collection: Concurrence,
    map: ksom.KeyProfileSOM,
    has_legend: bool = True,
    show: bool = True,
) -> Tuple[np.array[float], Figure]:
    """
    Projects the pitch-class distribution of a note-collection to a
    self-organized map trained on key profile (?) data.
    Returns the resulting projection matrix.

    TODO: need to support colormap and textsize
    Parameters
    ----------
    note_collection: Concurrence
        Collection of notes to calculate the pitch-class distribution of and
        project onto the pre-trained SOM.

    map: KeyProfileSOM
        A pretrained self-organizing map trained on major + minor pitch profiles
        from a single literature.

    has_legend: bool
        Whether or not the plot should include a color legend

    show: bool
        Whether or not we suspend execution and display the plot before returning
        from this function

    TODO: interpolation argument

    Returns
    -------
    np.array[float]
        Returns a 2-D numpy array that contains the projection of the input
        data onto the self-organizing map.
    Figure
        Matplotlib figure that contains the axes with a plot of the projection
    """
    input = pcdist1(note_collection)
    projection, Figure = map.project_and_visualize(input, has_legend, show)
    # a good idea would probably be to return a tuple containing projection and
    # Figure/axes
    return projection, Figure
