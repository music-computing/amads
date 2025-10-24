"""
Projection of pitch-class distribution on a self-organizing map
(Toiviainen & Krumhansl, 2003)

Description:
    TODO: not enough understanding of this function here

Problems:
Should we generalize this algorithm to use self-organizing maps
trained on data other than Krumhansl-kessler key profiles?
Proposal:
    - Add a cached trainer function that takes in a profile and spits out a
    self-organizing map

Keysomdata is missing (even from the github repository)
in the matlab version.
Proposal:
    - Train and get your own training configuration (including initial values
    of the map before training the SOM, rate of learning, and propagation
    function)?

Things to watch out for:
    - crank the learning rate low enough so that order of selection for the
    very small (profile) data set doesn't really matter. (let's start with 0.2)
    - Make sure the weight propagation is a toroid (circular propagation based
    off of 1-norm?).

See https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=66 for more details
"""

from typing import List, Optional

import numpy as np

from amads.core.basics import Concurrence
from amads.pitch.key import profiles as prof


def trainprofilesom(
    profile: prof._KeyProfile = prof.KrumhanslKessler,
    attribute_names: Optional[List[str]] = None,
):
    """
    Trains a self-organizing map based off of the profile and attribute names
    of the specific pitch profiles we want to train our self-organizing map on.

    TODO: Problems
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
        which specifies key_cc to compute the crosscorrelation between
        the pitch-class distribution of the score and both prof.vuvan.natural_minor
        and prof.vuvan.harmonic_minor.
        None can be supplied when we want to specify all valid pitch
        profiles within a given key profile.

    Returns
    -------
    Any
        A self-organizing map (dimensions, type undecided yet)
    """

    assert 0


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
    assert 0
