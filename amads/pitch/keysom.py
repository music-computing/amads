"""
Projection of pitch-class distribution on a self-organizing map
(Toiviainen & Krumhansl, 2003)

Description:

Problems:
Should we generalize this algorithm to use self-organizing maps
trained on data other than Krumhansl-kessler key profiles?
Proposal:
    - Add a cached trainer function that takes in a profile and spits out a
    self-organizing map
Second thoughts (about this):
    - Probably not yet. Get a toy working version first that's completely
    faithful to the miditoolbox version.
    - Another gripe I have is the width of the SOM (36 indices) seem
    specifically tailored to a profile with 12 major and 12 minor key weights.

Things to watch out for:
    - crank the learning rate low enough so that order of selection for the
    very small (profile) data set doesn't really matter. (let's start with 0.2)
    - Make sure the weight propagation is a toroid (circular propagation based
    off of 1-norm?).

See https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=66 for more details
"""

import random
from typing import List, Optional, Tuple

import numpy as np

from amads.algorithms.norm import euclidean_distance
from amads.core.basics import Concurrence
from amads.pitch.key import profiles as prof

# TODO: make sure to get rid of some of the random asserts used in development
# no need to add these restrictions


def decay_function(idx: int) -> float:
    """
    Global learning rate per iteration.

    """
    assert idx >= 0
    return (0.95) ** idx


def neighborhood_propagation(
    coord: Tuple[int], best_match: Tuple[int], idx: int
) -> float:
    """
    Neighborhood propagation update function from BMU.

    This propagation function is designed to decay exponential
    to the euclidean distance of the node to the BMU on the SOM.
    """
    distance = euclidean_distance(coord, best_match, False)

    return (0.5) ** distance


def data_selector(list_of_canonicals: List[np.array], idx: int) -> np.array:
    """
    Data selector given a list of attribute nmaes and current iteration.

    Current iteration is ignored in this function for now.
    """
    return random.choice(list_of_canonicals)[random.randrange(0, 12), :]


def update_SOM(SOM: np.array, best_match: Tuple[int], input_data: np.array, idx: int):
    """
    updates the SOM on the input data based off of the best matching unit, and the current
    global training iteration.
    """
    dim0, dim1, input_length = SOM.shape
    if input_length == input_data.shape[0]:
        raise ValueError(
            f"self-organizing map has invalid shape {SOM.shape}"
            "or input is of invalid shape {input_data.shape}"
        )
    for i in range(dim0):
        for j in range(dim1):
            rate = decay_function(idx) * neighborhood_propagation(
                (i, j), best_match, idx
            )
            SOM[i, j, :] = (1 - rate) * SOM[i, j, :] + rate * input_data


def trainprofilesom(
    profile: prof.KeyProfile = prof.KrumhanslKessler,
    attribute_names: Optional[List[str]] = ["major_sum", "minor_sum"],
):
    """
    Trains a self-organizing map based off of the profile and attribute names
    of the specific pitch profiles we want to train our self-organizing map on.

    The various configurations for training are empirically determined.

    - Should we have a configuration state that we can pass in to make training
    deterministic?

    Parameters
    ----------
    profile: prof.KeyProfile
        The key profile to use for analysis.

    attribute_names: Optional[List[str]]
        List of attribute names that denote the particular PitchProfiles
        within the KeyProfile to compute correlations for.
        An example of a valid key profile, attribute names combination is
        something like (prof.vuvan, ["natural_minor", "harmonic_minor"]),
        which specifies training data from the pitch-class distributions
        of the score and both prof.vuvan.natural_minor and
        prof.vuvan.harmonic_minor.
        None can be supplied when we want to specify all valid pitch
        profiles within a given key profile.

    Returns
    -------
    Any
        A self-organizing map (dimensions, type undecided yet)
    """
    # TODO: fix this later
    assert attribute_names == ["major_sum", "minor_sum"]

    list_of_canonicals = [
        profile[attribute].normalize().as_canonical_matrix()
        for attribute in attribute_names
    ]

    # 12 is the input length
    # 36 is data width/feature width/something else?
    # 24 is the 12 major and 12 minor keys for the profile data
    #
    # SOM indices have been rearranged from matlab version for convenience
    # in this implementation
    SOM = np.random.rand(24, 36, 12)

    max_iterations = 36

    for idx in range(max_iterations):
        data_vector = data_selector(list_of_canonicals, idx)
        # tensor multiplication (need to figure out index)
        application = SOM @ data_vector
        # figure out best match
        best_match = np.unravel_index(np.argmax(application))
        update_SOM(SOM=SOM, best_match=best_match, input_data=data_vector, idx=idx)

    return SOM


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

    """

    # projects pitch-class distribution to trained SOM on major and minor key
    # profiles

    # plot projection on a 2-D linearly-interpolated heatmap
    # TODO:
    # figure out how the notes are plotted, or rather what criteria let the
    # notes be plotted where they have been?
    # basically figure out how the keyx and keyy functions operate...
    # keyx(key: int) -> float
    # keyy(key: int) -> float
    # keyname(key: int) -> str

    # additional things to figure out for keysomanim later (especially quirks
    # with matplotlib)
    assert 0
