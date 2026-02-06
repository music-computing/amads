"""
Projection of pitch-class distribution on a self-organizing map.

Computes the projection of a pitch-class distribution on a trained
self-organizing map, and visualize it in a 2-D heatmap with a custom color
gradient.

Unlike the original miditoolbox implementation in matlab, the SOM here
is allowed to use any key profile in literature as long as it contains
valid major and minor pitch profile attributes. See key/profiles.py for more
details.

Warnings
--------
(Remove this after testing and experimentation)

References
----------
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=66 for more details

Toiviainen & Krumhansl, 2003

"""

# for function types
from typing import Tuple, Union, Optional

import numpy as np
import matplotlib.colors as mcolors
from matplotlib.figure import Figure

from amads.core.basics import Score
from amads.pitch.key import keysomdata as ksom
from amads.pitch.pcdist1 import pitch_class_distribution_1

# ! make sure to get rid of some of the random asserts used in development


def keysom(
    note_collection: Score,
    map: Union[ksom.KeyProfileSOM, str],
    has_legend: bool = True,
    scaled_legend: bool = True,
    font_size: Optional[Union[float, str]] = None,
    color_map: Optional[Union[str, mcolors.LinearSegmentedColormap]] = None,
    show: bool = True,
) -> Tuple[np.ndarray, Figure]:
    """
    Projects the pitch-class distribution of a note-collection to a SOM.

    The SOM (self-organized map) is trained on key profile data.
    Returns the resulting projection matrix.

    Parameters
    ----------
    note_collection : Score
        Collection of notes to calculate the pitch-class distribution of and
        project onto the pre-trained SOM.
    map : KeyProfileSOM
        A pretrained self-organizing map trained on major + minor pitch profiles.
        Or, a file path string to load the map from a .npz file.
    has_legend : bool
        Whether or not the plot should include a color legend
    scaled_legend: bool
        Whether or not the color legend scales with the projection's minimum
        and maximum, or (by default) scales with the trained SOM's global
        minimum and maximum.
    font_size: Optional[Union[float, str]] = None,
        Font size, either:
        (1) Font size of the labels (in points) or a string option from
        matplotlib
        (2) None for the default font size provided by matplotlib
        Shares the same effects as the option of the same name in the
        project_and_visualize method of KeyProfileSOM.
    color_map: Optional[Union[str, mcolors.LinearSegmentedColormap]]
        Color map describing the color gradient of the resulting visualization.
        Option has same functionality of the argument with the same name in the
        project_and_visualize method of KeyProfileSOM.
    show : bool
        Whether or not we suspend execution and display the plot before returning
        from this function

    Returns
    -------
    np.array[float]
        Returns a 2-D numpy array that contains the projection of the input
        data onto the self-organizing map.
    Figure
        Matplotlib figure that contains the axes with a plot of the projection
    """
    target_map = None
    if isinstance(map, str):
        target_map = ksom.KeyProfileSOM.from_trained_SOM(map)
    elif isinstance(map, ksom.KeyProfileSOM):
        target_map = map
    else:
        raise ValueError("invalid map argument!")
    input = tuple(pitch_class_distribution_1(note_collection).data)
    projection, Figure = target_map.project_and_visualize(
        input, has_legend, scaled_legend, font_size, color_map, show
    )
    # a good idea would probably be to return a tuple containing projection and
    # Figure/axes
    return projection, Figure
