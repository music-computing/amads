"""
NAME:
===============================
Key Profile Based Self-Organizing Maps (key_profiles_literature.py)


LICENCE:
===============================
Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/


CITE:
===============================
Toiviainen, P. & Krumhansl, C. L. (2003). Measuring and modeling
real-time responses to music: the dynamics of tonality induction.
Perception, 32(6), 741-766.


ABOUT:
===============================
Self-organizing maps trained on pitch class usage profiles from literature.

A self-organizing map can be trained on key profile with 'major' and 'minor'
data fields. The caller can define the decay rate and neighborhood
function that the profile is trained on.
When visualizing a projection of a pitch-class profile onto a trained
self-organizing map, there are 24 key labels scattered across the map.
The positions of these key labels (upper-case for major, lower-case for minor)
are determined by the position of the BMU node in the trained map to their
corresponding key profiles.
"""

import math

# for function types
from collections.abc import Callable
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from amads.algorithms.norm import euclidean_distance

# from amads.core.basics import Score
from amads.pitch.key import profiles as prof

# import random


# TODO: need pretrained weights on scale pitch profiles or something...


def keysom_inverse_decay(idx: int) -> float:
    """
    Global learning rate per iteration.

    Inverse to the current learning iteration...
    """
    assert idx >= 0
    if idx == 0:
        return 1
    else:
        return 1 / (2 * idx)


def keysom_stepped_inverse_decay(idx: int) -> float:
    """
    Global learning rate per iteration.

    Inverse to a stepped multiplier of the current learning iteration...

    In this case it's stepped to allow all inputs to deterministically
    pass during training (for 12 major and 12 minor key profile entries
    specifically)
    """
    step = idx // (12 * 2)
    if step == 0:
        return 1
    else:
        return 1 / math.log2(step + 2)


def keysom_centroid_euclidean(
    coord: Tuple[int], best_match: Tuple[int], shape: Tuple[int], idx: int
) -> float:
    """
    Neighborhood propagation update function.

    Exponential decay based off of Eucliean distance on a 2-D plane
    assuming the SOM output layer is a 2-D flat plane
    """
    distance = euclidean_distance(coord, best_match, False)

    # 0.95 is purely empirical. Honestly another value might be better
    if distance == 0:
        return 1
    else:
        return (0.95) ** distance


def keysom_toroid_euclidean(
    coord: Tuple[int], best_match: Tuple[int], shape: Tuple[int], idx: int
) -> float:
    """
    Neighborhood propagation update function.

    Exponential decay based off of Eucliean distance on a toroid
    assuming the SOM output layer is a projection of a toroid onto a
    2-D flat plane
    """
    num_rows, num_cols, input_length = shape
    # these are easy to follow since i, j are convention
    # and so is i0, j0
    i, j = coord
    i0, j0 = best_match
    diff_row = abs(i - i0)
    diff_col = abs(j - j0)
    toroid_diff_row = min(diff_row, num_rows - diff_row)
    toroid_diff_col = min(diff_col, num_cols - diff_col)
    distance = math.sqrt(toroid_diff_row**2 + toroid_diff_col**2)
    if distance == 0:
        return 1
    else:
        return (0.9) ** distance


def keysom_toroid_clamped(
    coord: Tuple[int], best_match: Tuple[int], shape: Tuple[int], idx: int
) -> float:
    """
    Neighborhood propagation update function.

    Same behavior as keysom_toroid_euclidean (see for more details),
    except distances past a certain radius is clamped to 0
    """
    num_rows, num_cols, input_length = shape
    # these are easy to follow since i, j are convention
    # and so is i0, j0
    i, j = coord
    i0, j0 = best_match
    diff_row = abs(i - i0)
    diff_col = abs(j - j0)
    toroid_diff_row = min(diff_row, num_rows - diff_row)
    toroid_diff_col = min(diff_col, num_cols - diff_col)
    distance = math.sqrt(toroid_diff_row**2 + toroid_diff_col**2)
    radius = 36.0 * (1 / (idx // 24 + 1))

    if distance > radius:
        return 0.0001
    elif distance == 0:
        return 1.0
    else:
        return (0.9) ** distance


class KeyProfileSOM:
    """
    Define coordinate of a node as the coordinate within the array of output nodes
    in a self-organizing map.
    Since each output node is
    """

    # TODO: need additional logging facilities,
    # primarily for visualizing training process:
    # (1) need a logging format to be able to intuitively visualize the intermediate
    # parameters
    # (2) need a few metrics to visualize the training process of the SOM.

    # corresponds to the number of weights in a pitch-class distribution
    _input_length = 12
    # possible pitches
    _pitches = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    # labels (major and minor)
    _labels = _pitches + [pitch.lower() for pitch in _pitches]

    def __init__(self, output_layer_dimensions: Tuple[int] = (24, 36)):
        self.SOM_output_dims = output_layer_dimensions
        self.SOM = None
        # best matching units to each of the corresponding coordinates
        self.label_coord_list = []

    def update_SOM(
        self,
        best_match: Tuple[int],
        input_data: np.array,
        idx: int,
        neighborhood: Callable[[Tuple[int], Tuple[int], Tuple[int], int], float],
        global_decay: Callable[[int], float],
    ) -> "KeyProfileSOM":
        """
        Updates the SOM on the input data based off of the best matching unit,
        and the current global training iteration.

        Parameters
        ----------
        best_match: Tuple[int]
            Coordinate of the best-matching node in the output layer of the
            self-organizing map and its corresponding connector weights
            (to the input)
        input_data: np.array
            data vector that was selected to train on for the current
            training iteration
        idx: int
            Current training iteration in training session.
        neighborhood: Callable[[Tuple[int], Tuple[int], Tuple[int], int], float]
            Neighborhood function, denoting the update rate component depending
            on coordinate differences to the best matching unit and training
            iteration.
        global_decay: Callable[[int], float]
            Global decay function, denoting the update rate component dependent
            solely on training iteration.

        Returns
        -------
        KeyProfileSOM
            Current object
        """
        if input_data.shape != (KeyProfileSOM._input_length,):
            raise ValueError(
                f"input {input_data} is of invalid shape {input_data.shape}"
            )

        dim0, dim1, input_length = self.SOM.shape
        if input_length != KeyProfileSOM._input_length:
            raise ValueError(f"Corrupted SOM =\n{self.SOM}\nof shape {self.SOM.shape}")
        if len(best_match) != 2:
            raise ValueError(f"Invalid best matching unit coords {best_match}")

        # update all weights in the SOM based on competitive learning
        # (where the only things that truly matter in a training iteration
        # is the BMU and the input data)
        for i in range(dim0):
            for j in range(dim1):
                rate = global_decay(idx) * neighborhood(
                    (i, j), best_match, self.SOM.shape, idx
                )
                self.SOM[i, j, :] = (1 - rate) * self.SOM[i, j, :] + rate * input_data

        return self

    def find_best_matching_unit(self, input_data: np.array) -> Tuple[int]:
        """
        Finds best matching unit given a self-organizing map and input data,
        or the coordinate of the output node whose weights has the smallest
        Euclidean distance from the input data.

        Parameters
        ----------
        input_data: np.array
            1-D data vector of input length containing the input weights

        Returns
        -------
        Tuple[int]
            Coordinates of the node that has the connector weights with the
            smallest Euclidean distance to the input data
        """
        # input data length needs to match
        if input_data.shape != (KeyProfileSOM._input_length,):
            raise ValueError(
                f"input {input_data} is of invalid shape {input_data.shape}"
            )

        dim0, dim1, input_length = self.SOM.shape
        if input_length != KeyProfileSOM._input_length:
            raise ValueError(f"Corrupted SOM =\n{self.SOM}\nof shape {self.SOM.shape}")

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

    def _data_selector(self, training_data: np.array, idx: int) -> np.array:
        """
        Internal data selector amongst training inputs represented as a list of
        canonical matrices (See the PitchProfile class in key/profiles.py for
        more detials on canonical matrices).

        This training data selector very specific to amads implementation
        of PitchProfile (See key/profiles.py for more details on the
        PitchProfile class).

        Parameters
        ----------
        Training data:
            2-D numpy array where each row is a training data input, and each column
            index correspond to the indices in a chromatic scale
        idx:
            Index of current training iteration

        Returns
        -------
        np.array[float]
            An input vector (with the weights of a normalized pitch profile)
            that is a 1-D numpy vector.
        """

        num_data, input_length = training_data.shape
        if input_length != KeyProfileSOM._input_length:
            raise ValueError(
                f"invalid training data dimensions {training_data.shape},"
                " expected (num_data, 12))"
            )

        # instead of random.randrange(0, num_data), let's just see the
        # deterministic version instead...

        # first scan through all major keys in the chromatic order of circle of
        # fifths
        # then scan through all minor keys in the same chromatic order
        if idx % 24 < 12:
            return training_data[(idx * 5) % 12, :]
        else:
            return training_data[12 + ((idx - 12) * 5) % 12, :]

    def zero_SOM_init(self):
        # zero SOM init...
        self.SOM = np.zeros((*self.SOM_output_dims, KeyProfileSOM._input_length))

    def random_SOM_init(self):
        """
        Included self-organizing map initialization

        Randomly initializes all weights in the self-organizing map
        to something between 0 and 1 inclusive
        """
        self.SOM = np.random.rand(*self.SOM_output_dims, KeyProfileSOM._input_length)
        self.SOM /= 2

    def _log_training_iteration(
        self,
        training_data: np.array,
        idx: int,
        bmu: Tuple[int],
        neighborhood: Callable[
            [Tuple[int], Tuple[int], Tuple[int], int], float
        ] = keysom_toroid_clamped,
        global_decay: Callable[[int], float] = keysom_stepped_inverse_decay,
    ):
        # TODO: records training iteration into the self-organizing map
        assert 0

    def train_SOM(
        self,
        profile: prof.KeyProfile = prof.krumhansl_kessler,
        max_iterations: int = 1024,
        neighborhood: Callable[
            [Tuple[int], Tuple[int], Tuple[int], int], float
        ] = keysom_toroid_clamped,
        global_decay: Callable[[int], float] = keysom_stepped_inverse_decay,
    ) -> "KeyProfileSOM":
        """
        Trains a self-organizing map based off of the given training data
        and training parameters.

        Parameters
        ----------
        profile: prof.KeyProfile
            The key profile to use for analysis.

        max_iterations: int
            The number of iterations to train the self-organizing map for

        neighborhood: Callable[[Tuple[int], Tuple[int], Tuple[int], int], float]
            Neighborhood function, denoting the update rate component depending
            on coordinate differences to the best matching unit and training
            iteration.

        global_decay: Callable[[int], float]
            Global decay function, denoting the update rate component dependent
            solely on training iteration.

        Returns
        -------
        KeyProfileSOM
            Current object
        """
        # TODO: this messed up the labels... need to fix
        attribute_names = ["major", "minor"]

        data_multiplier = 12

        # multiplied by 12 so that each row sums up to 12 instead of 1
        list_of_canonicals = [
            profile[attribute].normalize().as_canonical_matrix() * data_multiplier
            for attribute in attribute_names
        ]

        # stack into matrix representation to satisfy _data_selector argument
        # specification
        # Additionally, training data here is ordered (per row) in chromatic
        # scale order, first in major pitch profile weights then minor pitch
        # profile weights.
        training_data = np.vstack(list_of_canonicals)

        # 12 is the input length
        # 36 is data width/feature width/something else?
        # 24 is the 12 major and 12 minor keys for the profile data
        #
        # SOM indices have been rearranged from matlab version for convenience
        # in this implementation
        self.random_SOM_init()

        for idx in range(max_iterations):
            data_vector = self._data_selector(training_data, idx)
            best_match = self.find_best_matching_unit(data_vector)
            self.update_SOM(
                best_match=best_match,
                input_data=data_vector,
                idx=idx,
                neighborhood=neighborhood,
                global_decay=global_decay,
            )

        self.label_coord_list.clear()
        # need to find BMU to each of the key profile input vectors in the trained SOM
        # since training_data is already ordered properly, we just need to find BMU
        # over all the inputs
        for label, input in zip(KeyProfileSOM._labels, training_data):
            best_match = self.find_best_matching_unit(input)
            self.label_coord_list.append(best_match)
            print(f"label: {label}, best_match: {best_match}")

        return self

    def project_input_onto_SOM(self, input_data: np.array) -> np.array:
        """
        Computes the resulting projection weights of the input on a
        trained self-organizing map.

        Parameters
        ----------
        input_data: np.array
            1-D data vector of input length containing the input weights

        Returns
        -------
        np.array[float]
            Returns a 2-D numpy array that contains the projection of the input
            data onto the self-organizing map.
        """
        # input data length needs to match
        if input_data.shape != (KeyProfileSOM._input_length,):
            raise ValueError(
                f"input {input_data} is of invalid shape {input_data.shape}"
            )

        dim0, dim1, input_length = self.SOM.shape
        if input_length != KeyProfileSOM._input_length:
            raise ValueError(f"Corrupted SOM =\n{self.SOM}\nof shape {self.SOM.shape}")
        # projection of input data onto current self-organizing map
        # matrix multiplication (tensor extension)
        application = self.SOM @ input_data
        assert application.shape == (dim0, dim1)
        return application

    def project_and_visualize(
        self, input: Tuple[float], has_legend: bool = True, show: bool = True
    ) -> Tuple[np.array, Figure]:
        """
        Projects a pitch-class distribution and visualizes it

        ! Currently only supports basic version, need additional plotting
        ! options for more functionality
        TODO: need to support colormap and textsize
        Parameters
        ----------
        input: np.array
            1-D data vector of input length containing the input
            pitch-class distribution

        has_legend: bool
            Whether or not the plot should include a color legend

        show: bool
            Whether or not we suspend execution and display the plot before
            returning from this function

        Returns
        -------
        np.array[float]
            Returns a 2-D numpy array that contains the projection of the input
            data onto the self-organizing map.
        Figure
            Matplotlib figure that contains the axes with a plot of the projection
        """
        # prep data
        projection = self.project_input_onto_SOM(np.array(input))

        dim0, dim1, _ = self.SOM.shape
        assert projection.shape == (dim0, dim1)

        # visualize
        fig, ax = plt.subplots()

        # there should be some thought put into the actual interpolation formula
        cax = ax.imshow(projection, aspect="auto", interpolation="quadric")

        assert len(self.label_coord_list) == len(KeyProfileSOM._labels)

        # key labels in the plot
        for (i, j), label in zip(self.label_coord_list, KeyProfileSOM._labels):
            _ = ax.text(j, i, label, ha="center", va="center", color="w")

        # legend
        if has_legend:
            fig.colorbar(cax, ax=ax, label="Proportion")

        if show:
            plt.show()

        return projection, fig


# TODO: include some pretrained examples here!
