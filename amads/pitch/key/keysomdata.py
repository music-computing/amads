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
import os

# for function types
from collections.abc import Callable
from typing import List, Optional, Tuple, Union

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

# from matplotlib.axes import Axes
from matplotlib.figure import Figure

from amads.algorithms.norm import euclidean_distance

# from amads.core.basics import Score
from amads.pitch.key import profiles as prof


def zero_SOM_init(shape: Tuple[int, int, int]) -> np.array:
    """
    Included self-organizing map initialization

    Initializes all weights in the self-organizing map to 0
    """
    # zero SOM init...
    return np.zeros(shape)


def random_SOM_init(shape: Tuple[int, int, int]) -> np.array:
    """
    Included self-organizing map initialization

    Randomly initializes all weights in the self-organizing map
    to something between 0 and 0.5 inclusive
    """
    return np.random.rand(*shape) / 2


def handcrafted_SOM_init(shape: Tuple[int, int, int]) -> np.array:
    """
    Included self-organizing map initialization

    Bespoke initialization for the pretrained weights
    """
    if shape != (
        *KeyProfileSOM._default_output_dimensions,
        KeyProfileSOM._input_length,
    ):
        raise ValueError(f"invalid shape {shape} for handcrafted SOM")

    kkprof = prof.krumhansl_kessler
    list_of_majors = kkprof["major"].normalize().as_canonical_matrix()
    list_of_minors = kkprof["minor"].normalize().as_canonical_matrix()

    max_row, max_col, _ = shape

    init_weights = np.zeros(shape)

    # per "cell" arrangement, where each cell contains a major key label and its
    # corresponding minor key label horizontally adjacent to it

    # arithmetic for a 4x3 grid of cells in a 24x36 SOM
    row_multiplier = 6
    max_row_cells = max_row // row_multiplier
    row_offset = 3
    # twice to accomodate a cell containing 12
    col_multiplier = 6 * 2
    max_col_cells = max_col // col_multiplier
    col_major_offset = 3
    col_minor_offset = col_major_offset + 6

    key_idx = 0
    # the end result should be a rectangular grid in the labels
    for row_cell_idx in range(max_row_cells):
        for col_cell_idx in range(max_col_cells):
            # imprint major key
            major_col_idx = col_cell_idx * col_multiplier + col_major_offset
            major_row_idx = row_cell_idx * row_multiplier + row_offset
            init_weights[major_row_idx, major_col_idx] = list_of_majors[key_idx]

            # imprint minor key
            minor_col_idx = col_cell_idx * col_multiplier + col_minor_offset
            minor_row_idx = row_cell_idx * row_multiplier + row_offset
            init_weights[minor_row_idx, minor_col_idx] = list_of_minors[key_idx]

            # increment key_idx
            key_idx += 1

    assert key_idx == 12

    return init_weights


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
        return 1 / (2 * step)


def keysom_stepped_log_inverse_decay(idx: int) -> float:
    """
    Global learning rate per iteration.

    Log inverse to a stepped multiplier of the current learning iteration...

    In this case it's stepped to allow all inputs to deterministically
    pass during training (for 12 major and 12 minor key profile entries
    specifically)

    So why does inverse log work well? I like to think of it as the summation
    of traversing all nodes of a subtree of an imaginary sparse information tree.
    Where each layer of the information tree provides inverse decaying
    returns to the whole tree.
    This justification is very stretched though.
    Namely, each additional data point fed provides an opportunity to add
    another "symbol" to the intrinsic learned "alphabet" of the internal
    representation of the SOM.
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
    except distances past a certain radius is clamped to 0.0001.
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

    # same logic applies to clamp radius as the global learning decay rate.
    # Namely, each additional data point fed provides an opportunity to add
    # another "symbol" to the intrinsic learned "alphabet" of the internal
    # representation of the SOM.
    # diminishing returns...
    radius = 36.0 * (1 / math.log2(idx // 24 + 2))

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

    # corresponds to the number of weights in a pitch-class distribution
    _input_length = 12
    _default_output_dimensions = (24, 36)
    # possible pitches
    _pitches = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    # labels (major and minor)
    _labels = _pitches + [pitch.lower() for pitch in _pitches]

    def __init__(
        self, output_layer_dimensions: Tuple[int] = _default_output_dimensions
    ):
        self.SOM_output_dims = output_layer_dimensions
        self.SOM = None
        # best matching units to each of the corresponding coordinates
        self.label_coord_list = None
        self.log_info = []
        self.name = None

    @classmethod
    def save_trained_SOM(
        cls, obj: "KeyProfileSOM", dir_path: str = "./", file_name: Optional[str] = None
    ):
        """
        saves a trained key profile SOM. Raises a value exception if the object
        does not contain a proper trained SOM or the directory path is not valid.

        Parameters
        ----------
        obj: KeyProfileSOM
            Key Profile SOM object containing a trained SOM
        dir_path: str
            Path to directory to store the trained SOM (in npz format)
        file_name: Optional[str]
            Optional file name argument to save the trained SOM
        """

        if file_name is None:
            file_name = f"{obj.name}_data.npz"

        file_path = os.path.join(dir_path, file_name)

        if obj.SOM is None or not obj.label_coord_list:
            raise ValueError("input SOM is not trained!")

        np.savez(
            file_path,
            SOM=obj.SOM,
            name=np.array(obj.name),
            label_coords=np.array(obj.label_coord_list),
        )

    @classmethod
    def from_trained_SOM(
        cls, file_path: str = "./amads/pitch/key/KrumhanslKessler_SOM_data.npz"
    ) -> "KeyProfileSOM":
        """
        Creates a new KeyProfileSOM object containing the trained KeyProfileSOM
        loaded from the specified file.

        Parameters
        ----------
        file_path: str
            Path to directory containing stored SOM (in npz format)

        Returns
        -------
        KeyProfileSOM
            Key Profile SOM object containing the trained SOM from the file
        """
        load_table = np.load(file_path)
        SOM = load_table["SOM"]
        (dim0, dim1, _) = SOM.shape
        output_dims = (dim0, dim1)
        name = str(load_table["name"])
        label_coord_list = [tuple(coord) for coord in load_table["label_coords"]]

        obj = KeyProfileSOM(output_dims)
        obj.SOM = SOM
        obj.name = name
        obj.label_coord_list = label_coord_list
        obj.vmin = np.min(obj.SOM)
        obj.vmax = np.max(obj.SOM)

        return obj

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

    def _data_selector(
        self, training_data: np.array, training_idx: int
    ) -> Tuple[int, np.array]:
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
        training_idx:
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
        if training_idx % 24 < 12:
            access_idx = (training_idx * 5) % 12
            return access_idx, training_data[access_idx, :]
        else:
            access_idx = 12 + ((training_idx - 12) * 5) % 12
            return access_idx, training_data[access_idx, :]

    def _log_training_iteration(
        self,
        training_idx: int,
        data_idx: int,
        bmu: Tuple[int],
    ):
        """
        logs a training iteration. This function can be used to visualize
        a training iteration.

        Parameters
        ----------
        training_idx: int
            current training iteration

        data_idx: int
            index of the selected data row in the data matrix

        bmu: Tuple[int]
            coordinate of the best matching unit for the selected data during
            the current training iteration.
        """
        self.log_info.append((training_idx, data_idx, bmu))
        return

    def train_SOM(
        self,
        profile: prof.KeyProfile = prof.krumhansl_kessler,
        max_iterations: int = 24 * 64,
        neighborhood: Callable[
            [Tuple[int], Tuple[int], Tuple[int], int], float
        ] = keysom_toroid_clamped,
        global_decay: Callable[[int], float] = keysom_stepped_log_inverse_decay,
        weights_initialization: Callable[
            [Tuple[int, int, int]], np.array
        ] = random_SOM_init,
        log_training: bool = False,
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
            Neighborhood function, denoting the update rate component dependent
            on coordinate differences to the best matching unit and training
            iteration.

        global_decay: Callable[[int], float]
            Global decay function, denoting the update rate component dependent
            solely on training iteration.

        weights_initialization: Callable[[Tuple[int, int, int]], np.array]
            SOM weights initialization function, returning a numpy array of the
            initial SOM weights dependent on its input shape.

        log_training: bool
            Indicator flag for whether or not to keep a semi-detailed log of the
            training process

        Returns
        -------
        KeyProfileSOM
            Current object
        """
        attribute_names = ["major", "minor"]

        data_multiplier = 6

        # multiplied by 6 which is the expected value of randomly initializing
        # the values of each neuron's map weights to a random value between
        # [0, 1]
        # think of this as "normalizing" the input data to the same scale as
        # the original map weights

        # this will not affect the visualization of projections of a pitch-class
        # distribution in any way, since we can simply multiply the SOM
        # globally by the requisite multiplier after it is trained
        # in order to obtain normalized neuron weights.
        list_of_canonicals = [
            profile[attribute].normalize().as_canonical_matrix() * data_multiplier
            for attribute in attribute_names
        ]
        self.name = profile.name + "_SOM"

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
        self.SOM = weights_initialization(
            (*self.SOM_output_dims, KeyProfileSOM._input_length)
        )

        for training_idx in range(max_iterations):
            data_idx, data_vector = self._data_selector(training_data, training_idx)
            best_match = self.find_best_matching_unit(data_vector)
            self.update_SOM(
                best_match=best_match,
                input_data=data_vector,
                idx=training_idx,
                neighborhood=neighborhood,
                global_decay=global_decay,
            )
            if log_training:
                self._log_training_iteration(training_idx, data_idx, best_match)

        self.label_coord_list = []
        # need to find BMU to each of the key profile input vectors in the trained SOM
        # since training_data is already ordered properly, we just need to find BMU
        # over all the inputs
        for label, input in zip(KeyProfileSOM._labels, training_data):
            best_match = self.find_best_matching_unit(input)
            self.label_coord_list.append(best_match)
            print(f"label: {label}, best_match: {best_match}")

        # setting colorbar scale here
        self.vmin = np.min(self.SOM)
        self.vmax = np.max(self.SOM)

        return self

    # TODO: should I have an additional function here to set visualization
    # state so that it's persistent across multiple plots?

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
        self,
        input: Tuple[float],
        has_legend: bool = True,
        scaled_legend: bool = False,
        font_size: Optional[Union[float, str]] = None,
        color_map: Optional[Union[str, mcolors.LinearSegmentedColormap]] = None,
        show: bool = True,
    ) -> Tuple[np.array, Figure]:
        """
        Projects a pitch-class distribution and visualizes it

        Parameters
        ----------
        input: Tuple[float]
            a singular pitch-class distribution, in which case the visualization
            is simply a heatmap of its projection onto the trained SOM.

        has_legend: bool
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

        color_map: Optional[Union[str, mcolors.LinearSegmentedColormap]]
            Color map, either:
             (1) a color map provided by the matplotlib package
             (2) a custom linear segmented colormap
             (3) None for the default color scheme provided by matplotlib

        show: bool
            Whether or not we suspend execution and display the plot before
            returning from this function

        Returns
        -------
        Tuple[np.array, Figure]
            Returns a tuple consisting of:
            (1) the 2-D numpy array that contains the projection of the input
            data onto the self-organizing map.
            (2) Matplotlib figure that contains the axes with a plot of the
            projection
        """
        if not input:
            raise ValueError("empty input not allowed")
        if isinstance(input[0], tuple):
            raise ValueError("only takes 1 pitch-class distribution")
        # prep data
        projection = self.project_input_onto_SOM(np.array(input))

        dim0, dim1, _ = self.SOM.shape
        assert projection.shape == (dim0, dim1)

        fig, ax = plt.subplots()

        # there should be some thought put into the actual interpolation formula
        # cax = ax.contourf(projection)
        cax = ax.imshow(
            projection,
            aspect="auto",
            origin="lower",
            interpolation="nearest",
            cmap=color_map,
        )
        assert len(self.label_coord_list) == len(KeyProfileSOM._labels)

        # key labels in the plot
        for (i, j), label in zip(self.label_coord_list, KeyProfileSOM._labels):
            ax.text(
                j, i, label, ha="center", va="center", color="w", fontsize=font_size
            )

        # legend
        if has_legend:
            actual_vmin, actual_vmax = self.vmin, self.vmax

            if scaled_legend:
                actual_vmin = np.min(projection)
                actual_vmax = np.max(projection)

            cax.set_clim(actual_vmin, actual_vmax)
            fig.colorbar(cax, ax=ax, label="Proportion")

        if show:
            plt.show()

        return projection, fig

    def project_and_animate(
        self,
        input_list: List[Tuple[float]],
        has_legend: bool = True,
        font_size: Union[float, str] = 10.0,
        color_map: Optional[Union[str, mcolors.LinearSegmentedColormap]] = None,
        show: bool = True,
    ) -> Tuple[List[np.array], FuncAnimation]:
        """
        Projects a collection of pitch-class distributions and visualizes them
        in an animation

        Parameters
        ----------
        input_list: List[Tuple[float]]
            a list of pitch-class distributions, in which case the visualization
            is an animation of the sequence of projections of the pitch-class
            distributions onto the trained SOM.

        has_legend: bool
            Whether or not the plot should include a color legend

        font_size: Union[float, str]
            Font size, either:
            (1) Font size of the labels (in points) or a string option from
            matplotlib
            (2) None for the default font size provided by matplotlib

        color_map: Optional[Union[str, mcolors.LinearSegmentedColormap]]
            Color map, either:
             (1) a color map provided by the matplotlib package
             (2) a custom linear segmented colormap
             (see matplotlib.LinearSegmentedColormap for more details)
             (3) None for the default color scheme provided by matplotlib

        show: bool
            Whether or not we suspend execution and display the plot before
            returning from this function

        Returns
        -------
        Tuple[List[np.array], ArtistAnimation]
            (1) A list of 2-D numpy arrays that contain the sequence of
            projections from the list of input data onto the self-organizing map
            (2) The artist animation object of these data
        """
        # visualize
        projection_list = [
            self.project_input_onto_SOM(np.array(input)) for input in input_list
        ]
        print(projection_list)
        if not projection_list:
            print("Warning! No distributions provided to animate!")
            return

        fig, ax = plt.subplots()

        cax = ax.imshow(
            projection_list[0],
            aspect="auto",
            origin="lower",
            interpolation="nearest",
            cmap=color_map,
        )
        cax.set_clim(self.vmin, self.vmax)
        # key labels in the plot
        for (i, j), label in zip(self.label_coord_list, KeyProfileSOM._labels):
            ax.text(
                j, i, label, ha="center", va="center", color="w", fontsize=font_size
            )
        if has_legend:
            fig.colorbar(cax, ax=ax, label="Score Expectation", ticks=None)

        def frame_func(frame_idx):
            idx = frame_idx % len(projection_list)
            cax.set_data(projection_list[idx])

        ani = FuncAnimation(
            fig,
            frame_func,
            frames=len(input_list),
            interval=500,
            repeat=True,
            repeat_delay=2000,
        )

        if show:
            plt.show()

        return projection_list, ani


def pretrained_weights_script() -> KeyProfileSOM:
    """
    Simple script that generates a SOM from a hand-crafted initial SOM.

    This gives us a SOM with key labels in a determinstic grid adjacent to the
    axes of the grid.

    Returns
    -------
    KeyProfileSOM
        Object with training weights
    """

    # for the pretrained version, hand-craft initialization value for the
    # SOM so that we get the rotation and orientation desired for the resulting
    # trained weights
    obj = KeyProfileSOM()
    if obj.SOM_output_dims != KeyProfileSOM._default_output_dimensions:
        raise RuntimeError("invalid output dimensions for default SOM")

    obj.train_SOM(weights_initialization=handcrafted_SOM_init)

    return obj
