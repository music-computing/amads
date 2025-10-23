"""
Projection of pitch-class distribution on a self-organizing map
(Toiviainen & Krumhansl, 2003)

Description:
    TODO: not enough understanding of this function here

Problems:
    - Keysomdata is missing (even from the github repository)
    in the matlab version.
    - The original version of this function was also called as a
    subfunction of keysomanim.
    I think this behavior is worth implementing in our version of these functions.
    However, a windowed slice of a score is not a Score (see salami.py and
    slice.py in algorithms), but rather a Slice in this library.
    Alternative is to specify note_collection as a Concurrence instead,
    but then we wouldn't be able to call pcdist1 properly.
    TLDR: type of note collection is something we need to decide on
    - The self-organizing map itself was trained on a data-field
    based off of the Krumhansl-Kessler profiles. Are these the same profiles
    referenced in profiles.py?
    - Should we generalize this algorithm to use self-organizing maps
    trained on data other than Krumhansl-kessler key profiles?

See https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=66 for more details
"""

import numpy as np

from amads.core.basics import Concurrence


def keysom(
    note_collection: Concurrence, cbar: bool = True, cmap: str = "jet", tsize: int = 16
) -> np.array[float]:
    """
    Projects the pitch-class distribution of a note-collection to a
    self-organized map trained on key profile (?) data.
    Returns the resulting projection matrix.

    Parameters
    ----------
    note_collection: Concurrence
        Collection of notes to calculate the pitch-class distribution of and
        project onto the pre-trained SOM.
        TODO: some thought needed into the type of this argument
    cbar: bool
        Whether or not a color scaling legend will appear on the visualization
        True (default) for appearing color bar, False otherwise.
    cmap: str
        color map scheme used in the visualization of the projection matrix
        e.g. 'jet' (Default), 'gray', etc.
        TODO: make sure these are converted to matplotlib color map strings
    tsize: int
        text size for the annotations on the map itself.
        Default is 16

    Returns
    -------
    np.array[float]
        Resulting projection matrix
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
    assert 0
