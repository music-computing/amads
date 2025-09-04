"""
NAME:
===============================
Key Profiles (key_profiles_literature.py)


BY:
===============================
Mark Gotham, 2021
Huw Cheston, 2025
Tai Nakamura, 2025
Di Wang, 2025


LICENCE:
===============================
Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/


CITE:
===============================
Gotham et al. "What if the 'When' Implies the 'What'?". ISMIR, 2021
(see README.md)


ABOUT:
===============================
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

    AardenEssen,
    AlbrechtShanahan,
    BellmanBudge,
    deClerqTemperley,
    KrumhanslKessler,
    KrumhanslSchmuckler,
    PrinceSchumuckler,
    QuinnWhite,
    SappSimple,
    TemperleyKostkaPayne,
    TemperleyDeClerq,
    Vuvan,
    VuvanHughes,
"""

from collections import deque
from dataclasses import dataclass
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

import amads.core.norm as norm
from amads.core.distribution import DEFAULT_BAR_COLOR, Distribution


class PitchProfile(Distribution):
    """
    A set of weights for each pitch class.
    Weights are proportional to the expected number of occurrences of the
    pitch class in pieces transposed to the key of C (major or minor).

    We provide methods to allow users to obtain or visualize the information in a useful state.

    We define a canonical order of pitches as the order of pitches specified in
    the PitchProfile._pitches class variable

    In our implementation, a pitch profile is a collection of pitch class
    distributions stored in a canonical form convenient for conversion
    into other useful forms, whether to provide methods in a useful state
    or for custom visualization.
    We store the pitch profile canonically in two following cases.
    In the transpositionally equivalent case, we store the data as a set of 12 weights
    in canonical order (following the order of pitches specified in the _pitches variable).
    In the case of profiles that are not transpositionally equivalent, there is a
    pitch-class distribution for each key.
    These profiles are ordered in canonical order both by key and by pitch weights in each
    profile
    """

    _possible_types = ("assymetric_key_profile", "symmetric_key_profile")
    _pitches = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    _x_label = "Keys"
    _y_cats_2d = ["tonic"] + [f"{idx + 1}^" for idx in range(len(_pitches) - 1)]
    _possible_y_labels = ["Relative Pitch Offsets", "Weights"]

    def __init__(self, name, profile_tuple):
        if not PitchProfile._check_init_data_integrity(profile_tuple):
            raise ValueError(f"invalid profile tuple {profile_tuple}")
        profile_data = None
        profile_shape = None
        dist_type = None

        x_cats = None
        x_label = PitchProfile._x_label
        y_cats = None
        y_label = None
        if isinstance(profile_tuple[0], float):
            profile_data = deque(profile_tuple)
            profile_shape = [len(profile_data)]
            dist_type = "symmetric_key_profile"

        elif isinstance(profile_tuple[0], tuple):
            # we need to change this since the data is given through?
            profile_data = [
                deque(elem).rotate(idx) for idx, elem in enumerate(profile_tuple)
            ]
            profile_shape = [len(profile_data), len(profile_data[0])]
            dist_type = "assymetric_key_profile"

        else:
            raise ValueError(f"invalid profile tuple {profile_tuple}")
        super().__init__(
            name,
            profile_data,
            dist_type,
            profile_shape,
            x_cats,
            x_label,
            y_cats,
            y_label,
        )

    @classmethod
    def _check_init_data_integrity(cls, data):
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
        is_valid_assym = all(
            isinstance(elem, tuple) and len(elem) == 12 and allisfloat(elem)
            for elem in data
        )
        return is_valid_assym

    def normalize(self):
        """
        normalize the pitch-class distributions within the PitchProfile
        """
        assert self.distribution_type in PitchProfile._possible_types
        if self.distribution_type == "symmetric_key_profile":
            self.data = deque(norm.normalize(self.data, "sum"))
            return self
        else:
            self.data = [deque(norm.normalize(elem, "sum")) for elem in self.data]
            return self

    def as_tuple(self, key):
        """
        Given a key string, returns the corresponding weights in a 12-tuple for the profile
        where the order of weights is the canonical order rotated such that
        the first weight corresponds to the tonic.
        """
        shift_idx = None
        try:
            shift_idx = PitchProfile._pitches.index(key)
        except ValueError:
            raise ValueError(
                f"invalid key {key}, expected one of {PitchProfile._pitches}"
            )
        assert shift_idx is not None
        assert shift_idx >= 0 and shift_idx < len(PitchProfile._pitches)
        assert self.distribution_type in PitchProfile._possible_types
        if self.distribution_type == "symmetric_key_profile":
            # symmetrical case
            ret_data_tuple = tuple(self.data.rotate(-shift_idx))
            self.data.rotate(shift_idx)
            return ret_data_tuple
        else:
            # assymetrical case
            ret_data_tuple = tuple(self.data[shift_idx].rotate(-shift_idx))
            self.data[shift_idx].rotate(shift_idx)
            return ret_data_tuple

    def as_matrix_canonical(self) -> np.array:
        """
        returns a matrix of weights where both the rows and columns
        are in canonical order.
        """
        assert self.distribution_type in PitchProfile._possible_types
        assert self.dimensions[0] == 12
        if self.distribution_type == "symmetric_key_profile":
            profile_matrix = np.zeros((self.dimensions[0], self.dimensions[0]))
            for i in range(12):
                profile_matrix[i] = self.data
                self.data.rotate(1)
            return profile_matrix
        else:
            return np.array(self.data)

    def plot(
        self, keys: Optional[list], color=DEFAULT_BAR_COLOR, show: bool = True
    ) -> Figure:
        """
        custom plot method for PitchProfile.

        In this plot function's context:
        (1) Plot 1d is to plot a bar graph in canonical order of pitches.
        (2) Plot 2d takes a list of keys to plot, where the data corresponding
        to each key is plotted in canonical order rotated such that
        the given key is a tonic.

        The default option for keys is when keys is None and is as follows:
        In the default symmetric case, we plot the 1-d case.
        In the default assymetric case, we plot the 2-d case.

        Disclaimer:
        TODO: need to play around a bit more with this...

        Args:
        keys is a list of key pitches for which we want the corresponding pitch profiles
        to be visualized
        color is the color to put the plot in
        show is whether or not we want to display the plot immediately

        Returns:
        Figure that has been plotted to
        """
        plot_keys = keys
        # in the default case, we have default presets to plot the data
        if plot_keys is None:
            # 1-D plot
            if self.distribution_type == "symmetric_key_profile":
                self.x_categories = PitchProfile._pitches
                self.y_categories = PitchProfile._y_cats_2d
                self.y_label = PitchProfile._possible_y_labels[1]
                fig = super().plot(color, show)
                self.x_categories = None
                self.y_categories = None
                self.y_label = None
                return fig
            else:
                plot_keys = PitchProfile._pitches

        plot_data = [self.as_tuple(key) for key in plot_keys]

        self.x_categories = plot_keys
        self.y_categories = PitchProfile._y_cats_2d
        self.y_label = PitchProfile._possible_y_labels[0]
        fig = self._plot_2d(plot_data, color)
        self.x_categories = None
        self.y_categories = None
        self.y_label = None
        if show:
            plt.show()
        return fig

    def _plot_2d(self, plot_data, color=DEFAULT_BAR_COLOR) -> Figure:
        """Create a 2D plot of the PitchProfile.
        Returns:
            Figure - A matplotlib figure object.
        """
        fig, ax = plt.subplots()
        cax = ax.imshow(plot_data, cmap="gray_r", interpolation="nearest")
        fig.colorbar(cax, ax=ax, label="Proportion")
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        fig.suptitle(self.name)

        # Set x and y axis tick labels
        ax.set_xticks(range(len(self.x_categories)))
        ax.set_xticklabels(self.x_categories, rotation=45)
        ax.set_yticks(range(len(self.y_categories)))
        ax.set_yticklabels(self.y_categories)

        ax.invert_yaxis()
        return fig


@dataclass
class _KeyProfile:
    """This is the base class for all key profiles.

    This is the body of the docstring description.

    Attributes
    ----------
    name: str
        name of the profile

    literature: str
        citations for the profile in the literature

    about: str
        a longer description of the profile.

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
class KrumhanslKessler(_KeyProfile):
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
class KrumhanslSchmuckler(_KeyProfile):
    name: str = "KrumhanslSchmuckler"
    literature: str = "Krumhansl (1990)"
    about: str = "Early case of key-estimation through matching usage with profiles"
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
class AardenEssen(_KeyProfile):
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
class BellmanBudge(_KeyProfile):
    name: str = "BellmanBudge"
    literature: str = "Bellman (2005, sometimes given as 2006) after Budge (1943)"
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
class Temperley(_KeyProfile):
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
class TemperleyKostkaPayne(_KeyProfile):
    name: str = "TemperleyKostkaPayne"
    literature: str = "Temperley (2007 and 2008)"
    about: str = "Usage by section and excerpts from a textbook (Kostka & Payne)"
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
class Sapp(_KeyProfile):
    name: str = "Sapp"
    literature: str = "Sapp (PhD thesis, 2011)"
    about: str = (
        "Simple set of scale degree intended for use with Krumhansl Schmuckler (above)"
    )
    major: PitchProfile = PitchProfile(
        "Sapp.major", (2.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 1.0)
    )
    minor: PitchProfile = PitchProfile(
        "Sapp.minor", (2.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 2.0, 1.0, 0.0, 1.0, 0.0)
    )


@dataclass
class Vuvan(_KeyProfile):
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
class DeClerqTemperley(_KeyProfile):
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
class TemperleyDeClerq(_KeyProfile):
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
class AlbrechtShanahan(_KeyProfile):
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
class PrinceSchumuckler(_KeyProfile):
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
class QuinnWhite(_KeyProfile):
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
    major_assym: tuple[PitchProfile] = (
        PitchProfile(
            "QuinnWhite.major_assym.C",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.C#",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.D",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.Eb",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.E",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.F",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.F#",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.G",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.Ab",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.A",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.Bb",
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
        ),
        PitchProfile(
            "QuinnWhite.major_assym.B",
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
    minor_assym: tuple[tuple[float]] = (
        PitchProfile(
            "QuinnWhite.minor_assym.C",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.C#",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.D",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.Eb",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.E",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.F",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.F#",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.G",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.Ab",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.A",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.Bb",
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
        ),
        PitchProfile(
            "QuinnWhite.minor_assym.B",
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
class VuvanHughes(_KeyProfile):
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
