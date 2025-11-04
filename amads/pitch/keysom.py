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

# for function types
from collections.abc import Callable
from typing import List, Optional, Tuple

import numpy as np

from amads.algorithms.norm import euclidean_distance
from amads.core.basics import Concurrence
from amads.pitch.key import profiles as prof

# ! make sure to get rid of some of the random asserts used in development


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
    Neighborhood propagation update function.

    Centroid with exponential decay (i.e. exponential decay
    based off euclidean distance)
    """
    distance = euclidean_distance(coord, best_match, False)

    return (0.5) ** distance


# TODO: explore just shoving all the training specific code into KeyProfileSOM
# also explore getting training specific code and SOM
class KeyProfileSOM:
    def __init__(
        self, output_layer_dimensions: Tuple[int] = (24, 36), input_length: int = 12
    ):
        self.SOM = np.random.rand(*output_layer_dimensions, input_length)

    def update_SOM(
        self,
        best_match: Tuple[int],
        input_data: np.array,
        idx: int,
        neighborhood: Callable[[Tuple[int], Tuple[int], int], float],
        global_decay: Callable[[int], float],
    ):
        """
        updates the SOM on the input data based off of the best matching unit,
        and the current global training iteration.

        TODO
        Parameters
        ----------

        """
        dim0, dim1, input_length = self.SOM.shape
        if input_length != input_data.shape[0]:
            raise ValueError(
                f"self-organizing map has invalid shape {self.SOM.shape}"
                "or input is of invalid shape {input_data.shape}"
            )
        for i in range(dim0):
            for j in range(dim1):
                rate = global_decay(idx) * neighborhood((i, j), best_match, idx)
                self.SOM[i, j, :] = (1 - rate) * self.SOM[i, j, :] + rate * input_data

    def find_best_matching_unit(self, input_data: np.array) -> Tuple[int]:
        """
        Finds best matching unit given a self-organizing map and input data

        TODO
        Parameters
        ----------

        TODO
        Returns
        -------
        """
        # input data length needs to match
        dim0, dim1, input_length = self.SOM.shape
        if input_length != input_data.shape[0]:
            raise ValueError(
                f"self-organizing map has invalid shape {self.SOM.shape}"
                "or input is of invalid shape {input_data.shape}"
            )
        best_i, best_j = 0, 0
        best_distance = euclidean_distance(
            input_data, self.SOM[best_i, best_j, :], False
        )
        for i in range(dim0):
            for j in range(dim1):
                distance = euclidean_distance(input_data, self.SOM[i, j, :], False)
                if best_distance > distance:
                    best_i, best_j = i, j
                    best_distance = distance
        return (best_i, best_j)

    def _data_selector(self, list_of_canonicals: List[np.array], idx: int) -> np.array:
        """
        Data selector given a list of attribute nmaes and current iteration.

        Current iteration is ignored in this function for now.

        TODO
        Parameters
        ----------

        TODO
        Returns
        -------
        np.array[float]
        """

        return random.choice(list_of_canonicals)[random.randrange(0, 12), :]

    def train_SOM(
        self,
        profile: prof.KeyProfile = prof.KrumhanslKessler,
        attribute_names: Optional[List[str]] = ["major", "minor"],
        max_iterations: int = 36,
        neighborhood: Callable[
            [Tuple[int], Tuple[int], int], float
        ] = neighborhood_propagation,
        global_decay: Callable[[int], float] = decay_function,
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

        max_iterations: int
            The number of iterations to train the self-organizing map for

        neighborhood: Callable[[Tuple[int], Tuple[int], int], float]
            Neighborhood function, denoting the update rate component depending
            on coordinate differences to the best matching unit and training
            iteration.

        global_decay: Callable[[int], float]
            Global decay function, denoting the update rate component dependent
            solely on training iteration.
        """
        assert attribute_names == ["major", "minor"]

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

        for idx in range(max_iterations):
            data_vector = self._data_selector(list_of_canonicals, idx)
            best_match = self.find_best_matching_unit(data_vector)
            self.update_SOM(
                best_match=best_match,
                input_data=data_vector,
                idx=idx,
                neighborhood=neighborhood,
                global_decay=global_decay,
            )

        # TODO: need to find BMU to each of the key profile input vectors in the trained SOM

        # data is becoming exceedingly cumbersome to throw around...
        # probably organize in a dedicated keySOM class
        return self

    def project_input(self, input_data: np.array) -> np.array:
        """
        projects input onto self-organizing map

        TODO
        Parameters
        ----------

        TODO
        Returns
        -------
        """
        # input data length needs to match
        dim0, dim1, input_length = self.SOM.shape
        if input_length != input_data.shape[0]:
            raise ValueError(
                f"self-organizing map has invalid shape {self.SOM.shape}"
                "or input is of invalid shape {input_data.shape}"
            )
        # projection of input data onto current self-organizing map
        # matrix multiplication (tensor extension)
        application = self.SOM @ input_data
        return application

    def obtain_key_label_tuples(self) -> List[Tuple[str, int, int]]:
        """
        TODO comments
        """
        assert 0
        return

    def project_and_visualize(self, input_data: np.array):
        """
        TODO comments
        """
        assert 0
        return


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
    # basically figure out how the keyx and keyy functions operate...

    # additional things to figure out for keysomanim later (especially quirks
    # with matplotlib)
    assert 0
