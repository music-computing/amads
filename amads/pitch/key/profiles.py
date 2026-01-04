"""
Pitch class usage profiles (PCP) from the literature.

In almost all cases reported here, keys are assumed to be
transpositionally equivalent, so the first (0th) entry is the tonic,
and no key-specific information is given.  The exception is QuinnWhite
which provides key-specific data.  In the key-specific case, we
instead store the distributions as a tuple of tuples of distributions
representing each individual key profile.

The profiles here provide the values exactly as reported in the
literature.  Where a profile does not sum to 1, an additional "_sum"
entry is provided with that normalisation.

The profiles appear below in approximately chronological order.
For reference, the alphabetical ordering is:

 -  AardenEssen
 -  AlbrechtShanahan
 -  BellmanBudge
 -  deClerqTemperley
 -  KrumhanslKessler
 -  KrumhanslSchmuckler
 -  PrinceSchumuckler
 -  QuinnWhite
 -  SappSimple
 -  TemperleyKostkaPayne
 -  TemperleyDeClerq
 -  Vuvan
 -  VuvanHughes

The variable **`source_list`** contains a list of all of these profiles.

Each profile is a dataclass object with the following attributes:

 - **`name`** (str) - the class name
 - **`about`** (str) - a short description
 - **`literature`** (str) - reference to the relevant publication
 - **`major`** (tuple[float]) - original weights for 12 pitch classes, major keys
   (in KrumhanslKessler, KrumhanslSchmuckler, AardenEssen, BellmanBudge,
    TemperleyKostkaPayne, Sapp, AlbrechtShanahan only)
 - **`major_sum`**  (tuple[float]) - weights that sum to 1, major keys
   (in KrumhanslKessler, KrumhanslSchmuckler, AardenEssen, BellmanBudge,
    TemperleyKostkaPayne, Sapp only)
 - **`minor`** (tuple[float]) - original weights for 12 pitch classes, minor keys
   (in KrumhanslKessler, KrumhanslSchmuckler, AardenEssen, BellmanBudge,
    TemperleyKostkaPayne, Sapp, AlbrechtShanahan only)
 - **`minor_sum`**  (tuple[float]) - weights that sum to 1, minor keys
   (in KrumhanslKessler, KrumhanslSchmuckler, AardenEssen, BellmanBudge,
    TemperleyKostkaPayne, Sapp only)
 - **`natural_minor`** (tuple[float]) - original weights, natural minor keys
   (in `Vuvan` only)
 - **`natural_minor_sum`** (tuple[float]) - weights that sum to 1, natural minor keys
   (in `Vuvan` only)
 - **`harmonic_minor`** (tuple[float]) - original weights, harmonic minor keys
   (in `Vuvan` only)
 - **`harmonic_minor_sum`** (tuple[float]) - weights that sum to 1, harmonic minor keys
   (in `Vuvan` only)
 - **`melodic_minor`** (tuple[float]) - original weights, melodic minor keys
   (in `Vuvan` only)
 - **`melodic_minor_sum`** (tuple[float]) - weights that sum to 1, melodic minor keys
   (in `Vuvan` only)
 - **`roots`** (tuple[float]) - original weights that sum to 1, chord roots in rock
   harmony (in DeClerqTemperley only)
 - **`melody_major`** (tuple[float]) - original weights that sum to 1, major melodies
   (in `TemperleyDeClerq` only)
 - **`melody_minor`** (tuple[float]) - original weights that sum to 1, minor melodies
   (in `TemperleyDeClerq` only)
 - **`harmony_major`** (tuple[float]) - original weights that sum to 1, major melodies
   (in `TemperleyDeClerq` only)
 - **`harmony_minor`** (tuple[float]) - original weights that sum to 1, minor melodies
   (in `TemperleyDeClerq` only)
 - **`downbeat_major`** (tuple[float]) - original weights,
   major on downbeats (in `PrinceSchumuckler` only)
 - **`downbeat_major_sum`** (tuple[float]) - original weights that sum to 1,
   major on downbeats (in `PrinceSchumuckler` only)
 - **`downbeat_minor`** (tuple[float]) - original weights,
   minor on downbeats (in `PrinceSchumuckler` only)
 - **`downbeat_minor_sum`** (tuple[float]) - original weights that sum to 1,
   minor on downbeats (in `PrinceSchumuckler` only)
 - **`all_beats_major`** (tuple[float]) - original weights,
   major on all beats (in `PrinceSchumuckler` only)
 - **`all_beats_major_sum`** (tuple[float]) - original weights that sum to 1,
   major on all beats (in `PrinceSchumuckler` only)
 - **`all_beats_minor`** (tuple[float]) - original weights,
   minor on all_beats (in `PrinceSchumuckler` only)
 - **`all_beats_minor_sum`** (tuple[float]) - original weights that sum to 1,
   minor on all_beats (in `PrinceSchumuckler` only)
 - **`major_all`** (tuple[float]) - original weights that sum to 1, all keys
   (in QuinnWhite only)
 - **`major_0`** (tuple[float]) - original weights that sum to 1, C Major
   (in QuinnWhite only)
 - **`major_1`** (tuple[float]) - original weights that sum to 1, C#/Db Major
   (in QuinnWhite only)
 - **`major_2`** (tuple[float]) - original weights that sum to 1, D Major
   (in QuinnWhite only)
 - **`major_3`** (tuple[float]) - original weights that sum to 1, D#/Eb Major
   (in QuinnWhite only)
 - **`major_4`** (tuple[float]) - original weights that sum to 1, E Major
   (in QuinnWhite only)
 - **`major_5`** (tuple[float]) - original weights that sum to 1, F Major
   (in QuinnWhite only)
 - **`major_6`** (tuple[float]) - original weights that sum to 1, F#/Gb Major
   (in QuinnWhite only)
 - **`major_7`** (tuple[float]) - original weights that sum to 1, G Major
   (in QuinnWhite only)
 - **`major_8`** (tuple[float]) - original weights that sum to 1, G#/Ab Major
   (in QuinnWhite only)
 - **`major_9`** (tuple[float]) - original weights that sum to 1, A Major,
   (in QuinnWhite only)
 - **`major_10`** (tuple[float]) - original weights that sum to 1, A#/Bb Major
   (in QuinnWhite only)
 - **`major_11`** (tuple[float]) - original weights that sum to 1, B Major
   (in QuinnWhite only)
 - **`minor_all`** (tuple[float]) - original weights that sum to 1, all keys
   (in QuinnWhite only)
 - **`minor_0`** (tuple[float]) - original weights that sum to 1, C Minor
   (in QuinnWhite only)
 - **`minor_1`** (tuple[float]) - original weights that sum to 1, C#/Db Minor
   (in QuinnWhite only)
 - **`minor_2`** (tuple[float]) - original weights that sum to 1, D Minor
   (in QuinnWhite only)
 - **`minor_3`** (tuple[float]) - original weights that sum to 1, D#/Eb Minor
   (in QuinnWhite only)
 - **`minor_4`** (tuple[float]) - original weights that sum to 1, E Minor
   (in QuinnWhite only)
 - **`minor_5`** (tuple[float]) - original weights that sum to 1, F Minor
   (in QuinnWhite only)
 - **`minor_6`** (tuple[float]) - original weights that sum to 1, F#/Gb Minor
   (in QuinnWhite only)
 - **`minor_7`** (tuple[float]) - original weights that sum to 1, G Minor
   (in QuinnWhite only)
 - **`minor_8`** (tuple[float]) - original weights that sum to 1, G#/Ab Minor
   (in QuinnWhite only)
 - **`minor_9`** (tuple[float]) - original weights that sum to 1, A Minor,
   (in QuinnWhite only)
 - **`minor_10`** (tuple[float]) - original weights that sum to 1, A#/Bb Minor
   (in QuinnWhite only)
 - **`minor_11`** (tuple[float]) - original weights that sum to 1, B Minor
   (in QuinnWhite only)
 - **`classical`** (tuple[float]) - original weights for 12 pitch classes,
   all classical keys
   (in VuvanHuges only)
 - **`classical_sum`**  (tuple[float]) - weights that sum to 1, all classical keys
   (in VuvanHuges only)
 - **`rock`** (tuple[float]) - original weights for 12 pitch classes, all rock keys
   (in VuvanHuges only)
 - **`rock_sum`**  (tuple[float]) - weights that sum to 1, all rock keys
   (in VuvanHuges only)

<small>**Author**: Mark Gotham, 2021, Huw Cheston, 2025</small>

REFERENCE
---------
Gotham et al. "What if the 'When' Implies the 'What'?". ISMIR, 2021
(see README.md)
"""

from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np

import amads.algorithms.norm as norm
from amads.core.distribution import Distribution
from amads.core.pitch import CHROMATIC_NAMES


class PitchProfile(Distribution):
    """
     A set of weights for each pitch class denoting the expected frequency
     of pitches for collections of notes (typically songs, can be chords)
     of a given key.

     We provide methods to allow users to obtain or visualize this information
     in a useful state.

     Definitions:
     Define a canonical order of pitches as the order of pitches specified in
     relative chromatic degree.

     In our implementation, a pitch profile is a collection of pitch class
     distributions stored in a canonical form convenient for conversion
     into other useful forms, whether to provide methods in a useful state
     or for custom visualization.
     We store the pitch profile canonically in one of two forms:

     1. In the transpositionally equivalent case, we store the data as a
         list of 12 (float) weights beginning with the tonic.
     2. In the case of profiles that are not transpositionally equivalent,
         there is are weights for each key which are collectively stored
         as a list of 12 key profiles, each a list of 12 weights. Each
         profile begins with the tonic. Therefore `data[2][5]` represents
         the 5th weight (for pitch class G) in the 2nd key (D).

     For visualization, our design envisions the following use-cases:

     1. Compare and contrast data within a single PitchProfile object,
         especially between different key profiles beginning at their
         respecive tonic. Hence, our custom plot method allows a list
         of keys to plot the data side by side in a heatmap.
     2. Compare and contrast PitchProfile data with other pitch-class
         distributions, hence why we also satisfy the specifications
         for both singular plot and multiple plots from its parent
         class Distribution.

     Class Attributes (in this case, attributes specifying possible class
     configuration options and visualization elements)
     ----------
    _pitches:
         list of pitches in canonical order
     _profile_label:
         histogram label for 1-D histogram (x-axis), or representing the
         key of the current profile in the 2-D heatmap (y-axis)
     _data_cats_2d:
         data categories for the 2-D heatmap, which are labelled in terms
         of relative chromatic degree
     _data_labels:
         possible data labels, Relative Chromatic Degree for 2-D case (x-axis),
         and Weights for 1-D case (y-axis)
    """

    # possible pitches
    _profile_label = "Keys"
    _data_cats_2d = [f"{idx}" for idx in range(12)]
    _data_labels = ["Chromatic Scale Degree", "Weights"]

    def __init__(
        self,
        name: str,
        profile_tuple: Union[Tuple[float, ...], Tuple[Tuple[float, ...], ...]],
    ):
        if not PitchProfile._check_init_data_integrity(profile_tuple):
            raise ValueError(f"invalid profile tuple {profile_tuple}")
        profile_data = None
        profile_shape = None
        dist_type = None

        x_cats = None
        x_label = None
        y_cats = None
        y_label = None
        if isinstance(profile_tuple[0], float):
            profile_data = list(profile_tuple)
            profile_shape = [len(profile_data)]
            dist_type = "symmetric_key_profile"
            x_cats = CHROMATIC_NAMES
            x_label = PitchProfile._profile_label
            y_cats = None
            y_label = PitchProfile._data_labels[1]

        elif isinstance(profile_tuple[0], tuple):
            # convert data from tonic-first to non-rotated canonical order
            profile_data = [
                elem[-idx:] + elem[:-idx]  # type: ignore
                for idx, elem in enumerate(profile_tuple)
            ]
            profile_shape = [len(profile_data), len(profile_data[0])]
            dist_type = "asymmetric_key_profile"
            x_cats = PitchProfile._data_cats_2d
            x_label = PitchProfile._data_labels[0]
            y_cats = CHROMATIC_NAMES
            y_label = PitchProfile._profile_label

        else:
            raise ValueError(f"invalid profile tuple {profile_tuple}")
        super().__init__(
            name,
            profile_data,
            dist_type,
            profile_shape,
            x_cats,  # type: ignore (strings are ok)
            x_label,
            y_cats,  # type: ignore (strings are ok)
            y_label,
        )

    @classmethod
    def _check_init_data_integrity(
        cls, data: Union[Tuple[float, ...], Tuple[Tuple[float, ...], ...]]
    ) -> bool:
        """
        checks the integrity of the data tuple that is supplied in init
        """

        def allisfloat(data_tuple):
            return all(isinstance(elem, float) for elem in data_tuple)

        if len(data) != 12:
            return False
        is_valid_sym = allisfloat(data)
        if is_valid_sym:
            return True
        is_valid_asym = all(
            isinstance(elem, tuple) and len(elem) == 12 and allisfloat(elem)
            for elem in data
        )
        return is_valid_asym

    def normalize(self):
        """
        normalize the pitch-class distributions within the PitchProfile s.t.
        for each key, the sum of all weights in the corresponding key profile data
        adds to 1.
        """
        if self.distribution_type == "symmetric_key_profile":
            self.data = norm.normalize(self.data, "sum").tolist()
            return self
        else:
            self.data = [
                norm.normalize(elem, "sum").tolist() for elem in self.data
            ]
            return self

    def key_to_weights(self, key: str) -> List[float]:
        """
        Given a key, computes the corresponding weights for the key profile
        rotated to the key as the tonic and organized in relative chromatic degree

        Parameters
        ----------
        key: str
            pitch string denoting the key of the key profile data we want to retrieve

        Returns
        -------
        list[float]
            weights: list of 12 floats
        """
        key_idx = None
        try:  # C -> 0, C# -> 1, D -> 2, ..., B -> 11
            key_idx = CHROMATIC_NAMES.index(key.capitalize())
        except ValueError:
            raise ValueError(
                f"invalid key {key}, expected one of {CHROMATIC_NAMES}"
            )
        assert key_idx is not None
        assert key_idx >= 0 and key_idx < 12
        if self.distribution_type == "symmetric_key_profile":
            # symmetrical case
            return self.data
        elif self.distribution_type != "asymmetric_key_profile":
            ValueError(f"invalid distribution type {self.distribution_type}")
            # asymmetrical case
        return self.data[key_idx]

    def as_canonical_matrix(self) -> np.ndarray:
        """
        Computes a 12x12 matrix of the profile data where:
        (1) The i-th row corresponds to the key profile of the
        i-th chromatic degree
        (2) Each row's weights begins from C and is ordered canonically
        (by relative chromatic degree)

        Returns:
            a 12x12 numpy matrix of floats
        """
        assert self.dimensions[0] == 12
        if self.distribution_type == "symmetric_key_profile":
            # in this case, symmetric profile is transpositionally equivalent,
            # so for instance, in C# major, the pitch weights would be
            # transposed (rotated) as B -> C, C -> C#, C# -> D, ...
            profile_matrix = np.zeros((self.dimensions[0], self.dimensions[0]))
            for i in range(12):
                data = self.data[-i:] + self.data[:-i]
                profile_matrix[i] = data
            return profile_matrix
        else:
            assert self.distribution_type == "asymmetric_key_profile"
            assert self.dimensions == [12, 12]
            return np.array(self.data)

    # def profile_plot(
    #     self,
    #     color: str = Distribution.DEFAULT_BAR_COLOR,
    #     option: str = "bar",
    #     show: bool = True,
    #     fig: Optional[Figure] = None,
    #     ax: Optional[Axes] = None,
    # ) -> Figure:
    #     """
    #     Plot method overriding the original plot method in the parent class.
    #     Instead of using the behavior of the plot method in the parent class,
    #     this plot uses the default plot behavior (keys = None) from PitchProfile's
    #     plot_custom.

    #     See plot_custom for more details about argument behavior.

    #     Returns:
    #         Figure - A matplotlib figure object
    #     """
    #     # Figure/axes handling: either both `fig` and `ax` are provided, or
    #     # neither; in the latter case, create a new figure/axes pair.
    #     if fig is None:
    #         if ax is not None:
    #             raise ValueError("invalid figure/axis combination")
    #         fig, ax = plt.subplots()
    #     else:
    #         if ax is None:
    #             raise ValueError("invalid figure/axis combination")
    #     return self.plot_custom(
    #         keys=None, color=color, option=option, show=show, fig=fig, ax=ax
    #     )

    # def plot_custom(
    #     self,
    #     keys: Optional[List[str]] = None,
    #     color: str = Distribution.DEFAULT_BAR_COLOR,
    #     option: str = "bar",
    #     show: bool = True,
    #     fig: Optional[Figure] = None,
    #     ax: Optional[Axes] = None,
    # ) -> Figure:
    #     """
    #     custom plot method for PitchProfile.

    #     There are largely 3 cases of behavior, revolving around the keys variable.

    #     When keys is an empty list, return None.

    #     When the keys argument is a non-empty list of pitches:
    #     (1) Plot a heatmap where the i-th row is the key profile for the i-th key in keys.
    #     (2) Each row in the heatmap is ordered canonically (by relative chromatic degree)
    #     and begins with its corresponding tonic.

    #     The default custom plot option, or when keys argument is None, is as follows:
    #     (1) If the current PitchProfile is transpositionally equivalent, plot a bar graph
    #     or line graph depending on what is specified in the option argument with the
    #     specified color.
    #     (1) If the current PitchProfile is non-transpositionally equivalent, plot a grey
    #     2d heatmap

    #     Args:
    #     keys: Optional[list]
    #         a list of key pitches for which we want the corresponding pitch profiles
    #         to be visualized
    #     color: str
    #         (1) In the transpositionally equivalent case and keys is None,
    #         color is the color of the graph
    #         (2) Ignored otherwise
    #     option: str
    #         (1) In the transpositionally equivalent case and keys is None,
    #         "bar" for plotting a bar graph,
    #         or "line" or "plot" for plotting a line graph.
    #         (2) Ignored otherwise
    #     show: bool
    #         whether or not we want to display the plot before returning from this function
    #     fig, ax : matplotlib Figure and Axes
    #         Provide an existing figure/axes to draw on; if omitted, a new
    #         figure and axes are created.

    #     Returns:
    #         Figure - A matplotlib figure object.
    #     """
    #     # Figure/axes handling: either both `fig` and `ax` are provided, or
    #     # neither; in the latter case, create a new figure/axes pair.
    #     if fig is None:
    #         if ax is not None:
    #             raise ValueError("invalid figure/axis combination")
    #         fig, ax = plt.subplots()
    #     else:
    #         if ax is None:
    #             raise ValueError("invalid figure/axis combination")
    #     # similar logic to the plot method in distribution.py
    #     plot_keys = keys
    #     # in the default case, we have default presets to plot the data
    #     if plot_keys is None:
    #         # 1-D plot
    #         if self.distribution_type == "symmetric_key_profile":
    #             return super().plot(
    #                 fig=fig, ax=ax, color=color, option=option, show=show
    #             )
    #         else:
    #             plot_keys = CHROMATIC_NAMES
    #     assert isinstance(plot_keys, list)
    #     if not plot_keys:
    #         raise ValueError("empty keys list provided")

    #     plot_data = [self.key_to_weights(key) for key in plot_keys]
    #     # save original plot labels
    #     save_state = (self.x_categories, self.x_label, self.y_categories, self.y_label)

    #     self.x_categories = PitchProfile._data_cats_2d
    #     self.x_label = PitchProfile._data_labels[0]
    #     self.y_categories = plot_keys
    #     self.y_label = PitchProfile._profile_label
    #     fig = self._plot_2d(fig=fig, ax=ax, plot_data=plot_data)

    #     # restore original plot labels
    #     self.x_categories, self.x_label, self.y_categories, self.y_label = save_state

    #     if show:
    #         plt.show()
    #     return fig

    # def _plot_2d(
    #     self,
    #     fig: Figure,
    #     ax: Axes,
    #     plot_data: List[List[float]],
    # ) -> Figure:
    #     """Create a 2D heatmap of a non-transpositionally equivalent PitchProfile.
    #     This is currently only used as internal logic for plot_custom.
    #     Returns:
    #         Figure - A matplotlib figure object.
    #     """
    #     if plot_data is None or fig is None or ax is None:
    #         raise ValueError("invalid plotting arguments")
    #     cax = ax.imshow(
    #         plot_data, cmap="gray_r", interpolation="nearest", aspect="auto"
    #     )
    #     fig.colorbar(cax, ax=ax, label="Proportion")
    #     ax.set_xlabel(self.x_label)
    #     ax.set_ylabel(self.y_label)
    #     fig.suptitle(self.name)

    #     # Set x and y axis tick labels
    #     ax.set_xticks(range(len(self.x_categories)))
    #     ax.set_xticklabels(self.x_categories, rotation=45)
    #     ax.set_yticks(range(len(self.y_categories)))
    #     ax.set_yticklabels(self.y_categories)

    #     ax.invert_yaxis()
    #     return fig


@dataclass
class KeyProfile:
    """This is the base class for all key profiles.

    Attributes:
        name (str): the name of the profile
        literature (str): citations for the profile in the literature
        about (str): a longer description of the profile.
    """

    name: str = ""
    literature: str = ""
    about: str = ""

    def __getitem__(self, key: str):
        """This is added for (some) backwards compatibility, allowing objects
        to be accessed as dictionaries using bracket notation.

        Examples
        --------
            >>> kp = KrumhanslKessler()
            >>> kp["name"]
            'KrumhanslKessler'
        """
        try:
            return getattr(self, key)
        # Slightly nicer error handling
        except AttributeError:
            raise AttributeError(
                f"Key Profile '{self.__str__()}' has no attribute '{key}'"
            )

    def __str__(self) -> str:
        return self.name


@dataclass
class KrumhanslKessler(KeyProfile):
    name: str = "KrumhanslKessler"
    literature: str = (
        "Krumhansl and Kessler (1982). See also Krumhansl and Shepard (1979)"
    )
    about: str = (
        "Early PCP from psychological 'goodness of fit' tests using probe-tones"
    )
    major: PitchProfile = PitchProfile(
        "KrumhanslKessler.major",
        (
            6.35,
            2.23,
            3.48,
            2.33,
            4.38,
            4.09,
            2.52,
            5.19,
            2.39,
            3.66,
            2.29,
            2.88,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "KrumhanslKessler.minor",
        (
            6.33,
            2.68,
            3.52,
            5.38,
            2.6,
            3.53,
            2.54,
            4.75,
            3.98,
            2.69,
            3.34,
            3.17,
        ),
    )


@dataclass
class KrumhanslSchmuckler(KeyProfile):
    name: str = "KrumhanslSchmuckler"
    literature: str = "Krumhansl (1990)"
    about: str = (
        "Early case of key-estimation through matching usage with profiles"
    )
    major: PitchProfile = PitchProfile(
        "KrumhanslSchmuckler.major",
        (
            6.35,
            2.33,
            3.48,
            2.33,
            4.38,
            4.09,
            2.52,
            5.19,
            2.39,
            3.66,
            2.29,
            2.88,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "KrumhanslSchmuckler.minor",
        (
            6.33,
            2.68,
            3.52,
            5.38,
            2.6,
            3.53,
            2.54,
            4.75,
            3.98,
            2.69,
            3.34,
            3.17,
        ),
    )


@dataclass
class AardenEssen(KeyProfile):
    name: str = "AardenEssen"
    literature: str = "Aarden (2003) based on Schaffrath (1995)"
    about: str = "Folk melody transcriptions from the Essen collection"
    major: PitchProfile = PitchProfile(
        "AardenEssen.major",
        (
            17.7661,
            0.145624,
            14.9265,
            0.160186,
            19.8049,
            11.3587,
            0.291248,
            22.062,
            0.145624,
            8.15494,
            0.232998,
            4.95122,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "AardenEssen.minor",
        (
            18.2648,
            0.737619,
            14.0499,
            16.8599,
            0.702494,
            14.4362,
            0.702494,
            18.6161,
            4.56621,
            1.93186,
            7.37619,
            1.75623,
        ),
    )


@dataclass
class BellmanBudge(KeyProfile):
    name: str = "BellmanBudge"
    literature: str = (
        "Bellman (2005, sometimes given as 2006) after Budge (1943)"
    )
    about: str = "Chords in Western common practice tonality"
    major: PitchProfile = PitchProfile(
        "BellmanBudge.major",
        (
            16.8,
            0.86,
            12.95,
            1.41,
            13.49,
            11.93,
            1.25,
            20.28,
            1.8,
            8.04,
            0.62,
            10.57,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "BellmanBudge.minor",
        (
            18.16,
            0.69,
            12.99,
            13.34,
            1.07,
            11.15,
            1.38,
            21.07,
            7.49,
            1.53,
            0.92,
            10.21,
        ),
    )


@dataclass
class Temperley(KeyProfile):
    name: str = "Temperley"
    literature: str = (
        "Temperley (1999). What's Key for Key? The Krumhansl-Schmuckler Key-Finding Algorithm Reconsidered. Music Perception, 17, 65-100."
    )
    about: str = (
        "Psychological data revised - Temperley's revision of Krumhansl-Schmuckler profiles"
    )
    major: PitchProfile = PitchProfile(
        "Temperley.major",
        (
            5.0,
            2.0,
            3.5,
            2.0,
            4.5,
            4.0,
            2.0,
            4.5,
            2.0,
            3.5,
            1.5,
            4.0,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "Temperley.minor",
        (
            5.0,
            2.0,
            3.5,
            4.5,
            2.0,
            4.0,
            2.0,
            4.5,
            3.5,
            2.0,
            1.5,
            4.0,
        ),
    )


@dataclass
class TemperleyKostkaPayne(KeyProfile):
    name: str = "TemperleyKostkaPayne"
    literature: str = "Temperley (2007 and 2008)"
    about: str = (
        "Usage by section and excerpts from a textbook (Kostka & Payne)"
    )
    major: PitchProfile = PitchProfile(
        "TemperleyKostkaPayne.major",
        (
            0.748,
            0.06,
            0.488,
            0.082,
            0.67,
            0.46,
            0.096,
            0.715,
            0.104,
            0.366,
            0.057,
            0.4,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "TemperleyKostkaPayne.minor",
        (
            0.712,
            0.084,
            0.474,
            0.618,
            0.049,
            0.46,
            0.105,
            0.747,
            0.404,
            0.067,
            0.133,
            0.33,
        ),
    )


@dataclass
class Sapp(KeyProfile):
    name: str = "Sapp"
    literature: str = "Sapp (PhD thesis, 2011)"
    about: str = (
        "Simple set of scale degree intended for use with Krumhansl Schmuckler (above)"
    )
    major: PitchProfile = PitchProfile(
        "Sapp.major",
        (2.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 1.0),
    )
    minor: PitchProfile = PitchProfile(
        "Sapp.minor",
        (2.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 2.0, 1.0, 0.0, 1.0, 0.0),
    )


@dataclass
class Vuvan(KeyProfile):
    name: str = "Vuvan"
    literature: str = "Vuvan et al. (2011)"
    about: str = "Different profiles for natural, harmonic, and melodic minors"
    natural_minor: PitchProfile = PitchProfile(
        "Vuvan.natural_minor",
        (
            5.08,
            3.03,
            3.73,
            4.23,
            3.64,
            3.85,
            3.13,
            5.29,
            4.43,
            3.95,
            5.26,
            3.99,
        ),
    )
    harmonic_minor: PitchProfile = PitchProfile(
        "Vuvan.harmonic_minor",
        (
            4.62,
            2.63,
            3.74,
            4.23,
            3.63,
            3.81,
            4.15,
            5.21,
            4.77,
            3.95,
            3.79,
            5.3,
        ),
    )
    melodic_minor: PitchProfile = PitchProfile(
        "Vuvan.melodic_minor",
        (
            4.75,
            3.26,
            3.76,
            4.46,
            3.49,
            4.09,
            3.67,
            5.08,
            4.14,
            4.43,
            4.51,
            4.91,
        ),
    )


@dataclass
class DeClerqTemperley(KeyProfile):
    name: str = "DeClerqTemperley"
    literature: str = "deClerq and Temperley (Popular Music, 2011)"
    about: str = "Chord roots (specifically) in rock harmony."
    roots: PitchProfile = PitchProfile(
        "DeClerqTemperley.roots",
        (
            0.328,
            0.005,
            0.036,
            0.026,
            0.019,
            0.226,
            0.003,
            0.163,
            0.04,
            0.072,
            0.081,
            0.004,
        ),
    )


@dataclass
class TemperleyDeClerq(KeyProfile):
    name: str = "TemperleyDeClerq"
    literature: str = "Temperley and deClerq (JNMR, 2013)"
    about: str = """Rock music and a distinction between melody and harmony.
               distributions as reported in Vuvan and Hughes (2021, see below)
               following personal correspondence with Temperley."""
    major: PitchProfile = PitchProfile(
        "TemperleyDeClerq.major",
        (
            0.223,
            0.001,
            0.158,
            0.015,
            0.194,
            0.071,
            0.002,
            0.169,
            0.003,
            0.119,
            0.008,
            0.035,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "TemperleyDeClerq.minor",
        (
            0.317,
            0.001,
            0.09,
            0.159,
            0.046,
            0.097,
            0.007,
            0.131,
            0.009,
            0.047,
            0.087,
            0.009,
        ),
    )
    harmony_major: PitchProfile = PitchProfile(
        "TemperleyDeClerq.harmony_major",
        (
            0.231,
            0.002,
            0.091,
            0.004,
            0.149,
            0.111,
            0.004,
            0.193,
            0.004,
            0.126,
            0.011,
            0.076,
        ),
    )
    harmony_minor: PitchProfile = PitchProfile(
        "TemperleyDeClerq.harmony_minor",
        (
            0.202,
            0.006,
            0.102,
            0.127,
            0.047,
            0.113,
            0.005,
            0.177,
            0.046,
            0.051,
            0.09,
            0.034,
        ),
    )


@dataclass
class AlbrechtShanahan(KeyProfile):
    name: str = "AlbrechtShanahan"
    literature: str = "Albrecht and Shanahan (Music Perception, 2013)"
    about: str = """Partial pieces for more stable within-key environment.
               Note that the two pairs of distributions reported in the appendix are identical"""
    major: PitchProfile = PitchProfile(
        "AlbrechtShanahan.major",
        (
            0.238,
            0.006,
            0.111,
            0.006,
            0.137,
            0.094,
            0.016,
            0.214,
            0.009,
            0.08,
            0.008,
            0.081,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "AlbrechtShanahan.minor",
        (
            0.220,
            0.006,
            0.104,
            0.123,
            0.019,
            0.103,
            0.012,
            0.214,
            0.062,
            0.022,
            0.061,
            0.052,
        ),
    )


@dataclass
class PrinceSchumuckler(KeyProfile):
    name: str = "PrinceSchumuckler"
    literature: str = "Prince and Schmuckler (Music Perception, 2014)"
    about: str = """Distinction between downbeat and all beats.
               Note they also provide profiles for metrical position usage."""
    downbeat_major: PitchProfile = PitchProfile(
        "PrinceSchumuckler.downbeat_major",
        (
            1.0,
            0.088610811,
            0.569205361,
            0.140888014,
            0.615384615,
            0.481864956,
            0.140888014,
            0.976815092,
            0.156831608,
            0.433398971,
            0.122721209,
            0.427237502,
        ),
    )
    downbeat_minor: PitchProfile = PitchProfile(
        "PrinceSchumuckler.downbeat_minor",
        (
            1.0,
            0.127885863,
            0.516472114,
            0.640207523,
            0.174189364,
            0.537483787,
            0.160311284,
            0.989883268,
            0.426588846,
            0.172114137,
            0.430350195,
            0.286381323,
        ),
    )
    major: PitchProfile = PitchProfile(
        "PrinceSchumuckler.major",
        (
            0.919356471,
            0.114927991,
            0.729198287,
            0.144709771,
            0.697021822,
            0.525970522,
            0.214762724,
            1.0,
            0.156143546,
            0.542952545,
            0.142399406,
            0.541215555,
        ),
    )
    minor: PitchProfile = PitchProfile(
        "PrinceSchumuckler.minor",
        (
            0.874192439,
            0.150655606,
            0.637256776,
            0.697274361,
            0.162238618,
            0.62471807,
            0.167131771,
            1.0,
            0.47788524,
            0.212622807,
            0.467754884,
            0.298711724,
        ),
    )


@dataclass
class QuinnWhite(KeyProfile):
    name: str = "QuinnWhite"
    literature: str = "Quinn and White (Music Perception 2017)"
    about: str = "Separate profiles for each key"
    # this used to be major_all, but is the symmetrical version of
    # the major key profile in QuinnWhite
    major: PitchProfile = PitchProfile(
        "QuinnWhite.major",
        (
            0.172,
            0.014,
            0.107,
            0.011,
            0.160,
            0.099,
            0.018,
            0.231,
            0.017,
            0.059,
            0.016,
            0.093,
        ),
    )
    # instead of ordering them by circle of fifths, we order the distributions by
    # incrementing key number the non-transpositionally equivalent distributions
    # represent instead
    major_asym: PitchProfile = PitchProfile(
        "QuinnWhite.major_asym",
        (
            (
                0.174,
                0.014,
                0.112,
                0.010,
                0.160,
                0.100,
                0.016,
                0.230,
                0.015,
                0.058,
                0.016,
                0.096,
            ),
            (
                0.173,
                0.016,
                0.103,
                0.014,
                0.165,
                0.091,
                0.020,
                0.234,
                0.018,
                0.055,
                0.018,
                0.093,
            ),
            (
                0.175,
                0.013,
                0.113,
                0.010,
                0.155,
                0.102,
                0.017,
                0.227,
                0.017,
                0.061,
                0.015,
                0.094,
            ),
            (
                0.173,
                0.015,
                0.108,
                0.011,
                0.160,
                0.098,
                0.019,
                0.231,
                0.016,
                0.059,
                0.015,
                0.094,
            ),
            (
                0.171,
                0.013,
                0.108,
                0.010,
                0.161,
                0.106,
                0.015,
                0.229,
                0.019,
                0.059,
                0.016,
                0.092,
            ),
            (
                0.173,
                0.014,
                0.108,
                0.009,
                0.161,
                0.096,
                0.018,
                0.231,
                0.016,
                0.063,
                0.016,
                0.095,
            ),
            (
                0.166,
                0.018,
                0.096,
                0.014,
                0.170,
                0.085,
                0.019,
                0.240,
                0.019,
                0.062,
                0.020,
                0.091,
            ),
            (
                0.175,
                0.013,
                0.108,
                0.011,
                0.156,
                0.102,
                0.017,
                0.233,
                0.016,
                0.058,
                0.019,
                0.091,
            ),
            (
                0.171,
                0.014,
                0.099,
                0.013,
                0.164,
                0.099,
                0.018,
                0.235,
                0.016,
                0.064,
                0.015,
                0.093,
            ),
            (
                0.174,
                0.014,
                0.108,
                0.012,
                0.160,
                0.101,
                0.017,
                0.232,
                0.018,
                0.059,
                0.014,
                0.093,
            ),
            (
                0.169,
                0.016,
                0.107,
                0.013,
                0.158,
                0.099,
                0.020,
                0.230,
                0.017,
                0.060,
                0.017,
                0.096,
            ),
            (
                0.167,
                0.014,
                0.106,
                0.014,
                0.164,
                0.100,
                0.018,
                0.233,
                0.021,
                0.054,
                0.020,
                0.089,
            ),
        ),
    )
    minor: PitchProfile = PitchProfile(
        "QuinnWhite.minor",
        (
            0.170,
            0.012,
            0.115,
            0.149,
            0.013,
            0.095,
            0.027,
            0.211,
            0.074,
            0.024,
            0.026,
            0.085,
        ),
    )
    minor_asym: PitchProfile = PitchProfile(
        "QuinnWhite.minor_asym",
        (
            (
                0.170,
                0.012,
                0.118,
                0.141,
                0.011,
                0.098,
                0.026,
                0.212,
                0.074,
                0.024,
                0.023,
                0.091,
            ),
            (
                0.168,
                0.014,
                0.112,
                0.152,
                0.014,
                0.093,
                0.028,
                0.212,
                0.078,
                0.022,
                0.026,
                0.082,
            ),
            (
                0.172,
                0.010,
                0.118,
                0.158,
                0.012,
                0.092,
                0.023,
                0.211,
                0.067,
                0.027,
                0.027,
                0.084,
            ),
            (
                0.168,
                0.014,
                0.111,
                0.152,
                0.015,
                0.087,
                0.032,
                0.213,
                0.073,
                0.025,
                0.027,
                0.082,
            ),
            (
                0.174,
                0.012,
                0.114,
                0.149,
                0.013,
                0.098,
                0.029,
                0.202,
                0.076,
                0.025,
                0.023,
                0.087,
            ),
            (
                0.167,
                0.011,
                0.117,
                0.141,
                0.012,
                0.093,
                0.026,
                0.217,
                0.077,
                0.024,
                0.025,
                0.089,
            ),
            (
                0.172,
                0.013,
                0.109,
                0.149,
                0.014,
                0.091,
                0.029,
                0.215,
                0.075,
                0.025,
                0.028,
                0.081,
            ),
            (
                0.174,
                0.011,
                0.116,
                0.152,
                0.014,
                0.094,
                0.028,
                0.208,
                0.069,
                0.027,
                0.026,
                0.081,
            ),
            (
                0.168,
                0.014,
                0.106,
                0.151,
                0.014,
                0.093,
                0.028,
                0.212,
                0.076,
                0.022,
                0.030,
                0.085,
            ),
            (
                0.175,
                0.010,
                0.114,
                0.149,
                0.012,
                0.096,
                0.025,
                0.217,
                0.073,
                0.021,
                0.026,
                0.083,
            ),
            (
                0.164,
                0.011,
                0.113,
                0.150,
                0.014,
                0.095,
                0.033,
                0.205,
                0.078,
                0.027,
                0.027,
                0.083,
            ),
            (
                0.164,
                0.012,
                0.120,
                0.144,
                0.013,
                0.102,
                0.024,
                0.208,
                0.074,
                0.022,
                0.028,
                0.088,
            ),
        ),
    )


@dataclass
class VuvanHughes(KeyProfile):
    name: str = "VuvanHughes"
    literature: str = "Vuvan and Hughes (Music Perception 2021)"
    about: str = "A comparison of Classical and Rock music."
    classical: PitchProfile = PitchProfile(
        "VuvanHughes.classical",
        (
            5.38,
            2.65,
            3.39,
            3.01,
            3.62,
            3.96,
            2.83,
            4.93,
            2.9,
            3.38,
            2.91,
            3.03,
        ),
    )
    rock: PitchProfile = PitchProfile(
        "VuvanHughes.rock",
        (
            5.34,
            3.33,
            3.73,
            3.39,
            3.95,
            3.99,
            2.82,
            4.54,
            2.9,
            3.21,
            2.88,
            2.71,
        ),
    )


source_list = (
    AardenEssen,
    AlbrechtShanahan,
    BellmanBudge,
    DeClerqTemperley,
    KrumhanslKessler,
    KrumhanslSchmuckler,
    PrinceSchumuckler,
    QuinnWhite,
    Sapp,
    Temperley,
    TemperleyKostkaPayne,
    TemperleyDeClerq,
    Vuvan,
    VuvanHughes,
)


aarden_essen = AardenEssen()
albrecht_shanahan = AlbrechtShanahan()
bellman_budge = BellmanBudge()
declerq_temperley = DeClerqTemperley()
krumhansl_kessler = KrumhanslKessler()
krumhansl_schmuckler = KrumhanslSchmuckler()
prince_schmuckler = PrinceSchumuckler()
quinn_white = QuinnWhite()
sapp = Sapp()
temperley = Temperley()
temperley_kostka_payne = TemperleyKostkaPayne()
temperley_de_clerq = TemperleyDeClerq()
vuvan = Vuvan()
vuvan_hughes = VuvanHughes()
