"""
NAME:
===============================
Key Profiles (key_profiles_literature.py)


BY:
===============================
Mark Gotham, 2021
Huw Cheston, 2025


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

In almost all cases reported here, keys are assumed to be equivalent, so
the first (0th) entry is the tonic, and
no key-specific information is given.
The exception is QuinnWhite which provides key-specific data.

The profiles here provide the values exactly as reported in the literature.
Where a profile does not sum to 1, an additional
"_sum" entry is provided with that normalisation.

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

from dataclasses import dataclass


@dataclass
class _KeyProfile:
    """This is the base class for all key profiles.

    This is the body of the docstring description.

    Attributes:
        name (str): the name of the profile
        literature (str): citations for the profile in the literature
        about (str): a longer description of the profile.

    """

    name: str = ""
    literature: str = ""
    about: str = ""

    def __getitem__(self, key: str):
        """This is added for (some) backwards compatibility when these objects were dictionaries.
        It means we can still access class attributes using bracket notation.

        Examples:
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
    major: tuple[float] = (
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
    )
    major_sum: tuple[float] = (
        0.152,
        0.053,
        0.083,
        0.056,
        0.105,
        0.098,
        0.06,
        0.124,
        0.057,
        0.088,
        0.055,
        0.069,
    )
    minor: tuple[float] = (
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
    )
    minor_sum: tuple[float] = (
        0.142,
        0.06,
        0.079,
        0.121,
        0.058,
        0.079,
        0.057,
        0.107,
        0.089,
        0.06,
        0.075,
        0.071,
    )


@dataclass
class KrumhanslSchmuckler(_KeyProfile):
    name: str = "KrumhanslSchmuckler"
    literature: str = "Krumhansl (1990)"
    about: str = "Early case of key-estimation through matching usage with profiles"
    major: tuple[float] = (
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
    )
    major_sum: tuple[float] = (
        0.152,
        0.056,
        0.083,
        0.056,
        0.105,
        0.098,
        0.06,
        0.124,
        0.057,
        0.087,
        0.055,
        0.069,
    )
    minor: tuple[float] = (
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
    )
    minor_sum: tuple[float] = (
        0.142,
        0.06,
        0.079,
        0.121,
        0.058,
        0.079,
        0.057,
        0.107,
        0.089,
        0.06,
        0.075,
        0.071,
    )


@dataclass
class AardenEssen(_KeyProfile):
    name: str = "AardenEssen"
    literature: str = "Aarden (2003) based on Schaffrath (1995)"
    about: str = "Folk melody transcriptions from the Essen collection"
    major: tuple[float] = (
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
    )
    major_sum: tuple[float] = (
        0.178,
        0.001,
        0.149,
        0.002,
        0.198,
        0.114,
        0.003,
        0.221,
        0.001,
        0.082,
        0.002,
        0.05,
    )
    minor: tuple[float] = (
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
    )
    minor_sum: tuple[float] = (
        0.183,
        0.007,
        0.14,
        0.169,
        0.007,
        0.144,
        0.007,
        0.186,
        0.046,
        0.019,
        0.074,
        0.018,
    )


@dataclass
class BellmanBudge(_KeyProfile):
    name: str = "BellmanBudge"
    literature: str = "Bellman (2005, sometimes given as 2006) after Budge (1943)"
    about: str = "Chords in Western common practice tonality"
    major: tuple[float] = (
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
    )
    major_sum: tuple[float] = (
        0.168,
        0.009,
        0.13,
        0.014,
        0.135,
        0.119,
        0.013,
        0.203,
        0.018,
        0.08,
        0.006,
        0.106,
    )
    minor: tuple[float] = (
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
    )
    minor_sum: tuple[float] = (
        0.182,
        0.007,
        0.13,
        0.133,
        0.011,
        0.112,
        0.014,
        0.211,
        0.075,
        0.015,
        0.009,
        0.102,
    )


@dataclass
class TemperleyKostkaPayne(_KeyProfile):
    name: str = "TemperleyKostkaPayne"
    literature: str = "Temperley (2007 and 2008)"
    about: str = "Usage by section and excerpts from a textbook (Kostka & Payne)"
    major: tuple[float] = (
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
    )
    major_sum: tuple[float] = (
        0.176,
        0.014,
        0.115,
        0.019,
        0.158,
        0.108,
        0.023,
        0.168,
        0.024,
        0.086,
        0.013,
        0.094,
    )
    minor: tuple[float] = (
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
    )
    minor_sum: tuple[float] = (
        0.17,
        0.02,
        0.113,
        0.148,
        0.012,
        0.11,
        0.025,
        0.179,
        0.097,
        0.016,
        0.032,
        0.079,
    )


@dataclass
class Sapp(_KeyProfile):
    name: str = "Sapp"
    literature: str = "Sapp (PhD thesis, 2011)"
    about: str = (
        "Simple set of scale degree intended for use with Krumhansl Schmuckler (above)"
    )
    major: tuple[float] = (2.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 1.0)
    major_sum: tuple[float] = (
        0.222,
        0.0,
        0.111,
        0.0,
        0.111,
        0.111,
        0.0,
        0.222,
        0.0,
        0.111,
        0.0,
        0.111,
    )
    minor: tuple[float] = (2.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 2.0, 1.0, 0.0, 1.0, 0.0)
    minor_sum: tuple[float] = (
        0.222,
        0.0,
        0.111,
        0.111,
        0.0,
        0.111,
        0.0,
        0.222,
        0.111,
        0.0,
        0.111,
        0.0,
    )


@dataclass
class Vuvan(_KeyProfile):
    name: str = "Vuvan"
    literature: str = "Vuvan et al. (2011)"
    about: str = "Different profiles for natural, harmonic, and melodic minors"
    natural_minor: tuple[float] = (
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
    )
    natural_minor_sum: tuple[float] = (
        0.102,
        0.061,
        0.075,
        0.085,
        0.073,
        0.078,
        0.063,
        0.107,
        0.089,
        0.08,
        0.106,
        0.08,
    )
    harmonic_minor: tuple[float] = (
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
    )
    harmonic_minor_sum: tuple[float] = (
        0.093,
        0.053,
        0.075,
        0.085,
        0.073,
        0.076,
        0.083,
        0.105,
        0.096,
        0.079,
        0.076,
        0.106,
    )
    melodic_minor: tuple[float] = (
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
    )
    melodic_minor_sum: tuple[float] = (
        0.094,
        0.064,
        0.074,
        0.088,
        0.069,
        0.081,
        0.073,
        0.1,
        0.082,
        0.088,
        0.089,
        0.097,
    )


@dataclass
class DeClerqTemperley(_KeyProfile):
    name: str = "DeClerqTemperley"
    literature: str = "deClerq and Temperley (Popular Music, 2011)"
    about: str = "Chord roots (specifically) in rock harmony."
    roots: tuple[float] = (
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
    )


@dataclass
class TemperleyDeClerq(_KeyProfile):
    name: str = "TemperleyDeClerq"
    literature: str = "Temperley and deClerq (JNMR, 2013)"
    about: str = """Rock music and a distinction between melody and harmony.
               Distributions as reported in Vuvan and Hughes (2021, see below)
               following personal correspondence with Temperley."""
    melody_major: tuple[float] = (
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
    )
    melody_minor: tuple[float] = (
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
    )
    harmony_major: tuple[float] = (
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
    )
    harmony_minor: tuple[float] = (
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
    )


@dataclass
class AlbrechtShanahan(_KeyProfile):
    name: str = "AlbrechtShanahan"
    literature: str = "Albrecht and Shanahan (Music Perception, 2013)"
    about: str = """Partial pieces for more stable within-key environment.
               Note that the two pairs of distributions reported in the appendix are identical"""
    major: tuple[float] = (
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
    )
    minor: tuple[float] = (
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
    )


@dataclass
class PrinceSchumuckler(_KeyProfile):
    name: str = "PrinceSchumuckler"
    literature: str = "Prince and Schmuckler (Music Perception, 2014)"
    about: str = """Distinction between downbeat and all beats.
               Note they also provide profiles for metrical position usage."""
    downbeat_major: tuple[float] = (
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
    )
    downbeat_major_sum: tuple[float] = (
        0.194,
        0.017,
        0.11,
        0.027,
        0.119,
        0.093,
        0.027,
        0.19,
        0.03,
        0.084,
        0.024,
        0.083,
    )
    downbeat_minor: tuple[float] = (
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
    )
    downbeat_minor_sum: tuple[float] = (
        0.183,
        0.023,
        0.095,
        0.117,
        0.032,
        0.098,
        0.029,
        0.181,
        0.078,
        0.032,
        0.079,
        0.052,
    )
    all_beats_major: tuple[float] = (
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
    )
    all_beats_major_sum: tuple[float] = (
        0.16,
        0.02,
        0.127,
        0.025,
        0.122,
        0.092,
        0.037,
        0.175,
        0.027,
        0.095,
        0.025,
        0.094,
    )
    all_beats_minor: tuple[float] = (
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
    )
    all_beats_minor_sum: tuple[float] = (
        0.151,
        0.026,
        0.11,
        0.121,
        0.028,
        0.108,
        0.029,
        0.173,
        0.083,
        0.037,
        0.081,
        0.052,
    )


@dataclass
class QuinnWhite(_KeyProfile):
    name: str = "QuinnWhite"
    literature: str = "Quinn and White (Music Perception 2017)"
    about: str = "Separate profiles for each key"
    major_all: tuple[float] = (
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
    )
    major_6: tuple[float] = (
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
    )
    major_1: tuple[float] = (
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
    )
    major_8: tuple[float] = (
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
    )
    major_3: tuple[float] = (
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
    )
    major_10: tuple[float] = (
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
    )
    major_5: tuple[float] = (
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
    )
    major_0: tuple[float] = (
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
    )
    major_7: tuple[float] = (
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
    )
    major_2: tuple[float] = (
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
    )
    major_9: tuple[float] = (
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
    )
    major_4: tuple[float] = (
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
    )
    major_11: tuple[float] = (
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
    )
    minor_all: tuple[float] = (
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
    )
    minor_6: tuple[float] = (
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
    )
    minor_1: tuple[float] = (
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
    )
    minor_8: tuple[float] = (
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
    )
    minor_3: tuple[float] = (
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
    )
    minor_10: tuple[float] = (
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
    )
    minor_5: tuple[float] = (
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
    )
    minor_0: tuple[float] = (
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
    )
    minor_7: tuple[float] = (
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
    )
    minor_2: tuple[float] = (
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
    )
    minor_9: tuple[float] = (
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
    )
    minor_4: tuple[float] = (
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
    )
    minor_11: tuple[float] = (
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
    )


@dataclass
class VuvanHughes(_KeyProfile):
    name: str = "VuvanHughes"
    literature: str = "Vuvan and Hughes (Music Perception 2021)"
    about: str = "A comparison of Classical and Rock music."
    classical: tuple[float] = (
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
    )
    classical_sum: tuple[float] = (
        0.128,
        0.063,
        0.081,
        0.072,
        0.086,
        0.094,
        0.067,
        0.117,
        0.069,
        0.08,
        0.069,
        0.072,
    )
    rock: tuple[float] = (
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
    )
    rock_sum: tuple[float] = (
        0.125,
        0.078,
        0.087,
        0.079,
        0.092,
        0.093,
        0.066,
        0.106,
        0.068,
        0.075,
        0.067,
        0.063,
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
temperley_kostka_payne = TemperleyKostkaPayne()
temperley_de_clerq = TemperleyDeClerq()
vuvan = Vuvan()
vuvan_hughes = VuvanHughes()
