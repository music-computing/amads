"""Ports `plotdist` Function

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=83
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import figure


def plotdist(dist, *, ivdir=False) -> figure.Figure:
    """Creates a graph of note, interval, or duration distributions/transitions.

    Serves mostly as a parser, with the graphing done in helper functions.

    Args:
        dist (List[int] or List[List[int]]):
            Distribution of pitch-classes (12), intervals (25) or durations (9)
            OR the transitions of the same features;
            pitch-class transitions (12 x 12), interval transitions (25 x 25),
            durations transitions (9 x 9) or key correlations (24),
            interval sizes (13) or intervals directions (12).

        ivdir (bool, keyword only):
            A boolean to check if the plot is for interval
            directions or pitch-classes. Needed since both distribution
            have the same data-structure shape.

    Returns:
        A figure of the graph of the input distribution
    """

    dist_array = np.array(dist)

    match dist_array.shape:
        case (12,):
            if ivdir:
                return interval_direction(dist_array)
            return pitch_class(dist_array)
        case (25,):
            return interval(dist_array)
        case (9,):
            return duration(dist_array)
        case (12, 12):
            return pitch_class_transition(dist_array)
        case (25, 25):
            return interval_transition(dist_array)
        case (9, 9):
            return duration_transition(dist_array)
        case (24,):
            return key_correlation(dist_array)
        case (13,):
            return interval_size(dist_array)
        case _:
            raise ValueError("Invalid input data-structure")


def pitch_class(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a pitch-class distribution

    Helper function for plotdist()

    Args:
        dist (List[int]):
            Distribution of pitch-classes

    Returns:
        A figure of the graph of the pitch-class distribution
    """

    fig, ax = plt.subplots()

    # Used code from pcdist1_test.py
    pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    ax.bar(pitch_classes, dist_array, color="skyblue")
    ax.set_xlabel("Pitch Class")
    ax.set_ylabel("Probability")
    ax.set_title("Pitch-Class Distribution")

    return fig


def interval(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a interval distribution

    Helper function for plotdist()

    Args:
        dist (List[int]):
            Distribution of intervals

    Returns:
        A figure of the graph of the interval distribution
    """

    fig, ax = plt.subplots()

    # Used code from ivdist1_test.py
    interval_names = [
        "-P8",
        "-M7",
        "-m7",
        "-M6",
        "-m6",
        "-P5",
        "-d5",
        "-P4",
        "-M3",
        "-m3",
        "-M2",
        "-m2",
        "P1",
        "+m2",
        "+M2",
        "+m3",
        "+M3",
        "+P4",
        "+d5",
        "+P5",
        "+m6",
        "+M6",
        "+m7",
        "+M7",
        "+P8",
    ]
    ax.bar(interval_names, dist_array, color="skyblue")

    tick_indices = list(range(0, len(interval_names), 3))  # Every 3 ticks
    tick_labels = [interval_names[i] for i in tick_indices]

    ax.set_xlabel("Interval")
    ax.set_ylabel("Probability")
    ax.set_title("Interval Distribution")

    # Apply every three ticks labels
    ax.set_xticks(ticks=tick_indices, labels=tick_labels)

    return fig


def duration(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a duration distribution

    Helper function for plotdist()

    Args:
        dist (List[int]):
            Distribution of durations

    Returns:
        A figure of the graph of the duration distribution
    """

    fig, ax = plt.subplots()

    # Used code from durdist1_test.py
    bin_centers = [
        "1/4",
        "sqrt(2)/4",
        "1/2",
        "sqrt(2)/2",
        "1",
        "sqrt(2)",
        "2",
        "2*sqrt(2)",
        "4",
    ]
    ax.bar(bin_centers, dist_array, color="skyblue")
    ax.set_xlabel("Duration (in beats)")
    ax.set_ylabel("Probability")
    ax.set_title("Duration Distribution")

    return fig


def interval_direction(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a interval direction distribution

    Helper function for plotdist()

    Args:
        dist (List[int]):
            Distribution of interval directions

    Returns:
        A figure of the graph of the interval direction distribution
    """

    fig, ax = plt.subplots()

    # Used code from ivdirdist1_test.py
    interval_names = [
        "m2",
        "M2",
        "m3",
        "M3",
        "P4",
        "d5",
        "P5",
        "m6",
        "M6",
        "m7",
        "M7",
        "P8",
    ]
    ax.bar(
        interval_names,
        height=[abs(i - 0.5) if i != 0 else 0 for i in id],
        bottom=[min(0.5, i) if i != 0 else 0.5 for i in id],
        color="skyblue",
    )
    ax.set_ylim(0, 1)
    ax.set_xlabel("Interval")
    ax.set_ylabel("Probability")
    ax.set_title("Interval Distribution")

    return fig


def pitch_class_transition(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a pitch class transition

    Helper function for plotdist()

    Args:
        dist (List[List[int]]):
            transition of pitch-classes

    Returns:
        A figure of the graph of the pitch class transition
    """

    fig, ax = plt.subplots()

    # Used code from pcdist2_test.py
    fig.set_figwidth(8)
    fig.set_figheight(6)
    im = ax.imshow(dist_array, cmap="hot", interpolation="nearest")
    fig.colorbar(im, label="Probability")
    ax.set_xlabel("Pitch Class (to)")
    ax.set_ylabel("Pitch Class (from)")
    ax.set_title("2nd Order Pitch-Class Distribution")

    pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    ax.set_xticks(range(12), pitch_classes)
    ax.set_yticks(range(12), pitch_classes)

    return fig


def interval_transition(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of an interval transition

    Helper function for plotdist()

    Args:
        dist (List[List[int]]):
            transition of intervals

    Returns:
        A figure of the graph of the interval transition
    """

    fig, ax = plt.subplots()

    # Used code from ivdist2_test.py
    fig.set_figwidth(8)
    fig.set_figheight(6)
    im = ax.imshow(dist_array, cmap="hot", interpolation="nearest")
    fig.colorbar(im, label="Probability")
    ax.set_xlabel("Interval (to)")
    ax.set_ylabel("Interval (from)")
    ax.set_title("2nd Order Interval Distribution")

    interval_names = [
        "-P8",
        "-M7",
        "-m7",
        "-M6",
        "-m6",
        "-P5",
        "-d5",
        "-P4",
        "-M3",
        "-m3",
        "-M2",
        "-m2",
        "P1",
        "+m2",
        "+M2",
        "+m3",
        "+M3",
        "+P4",
        "+d5",
        "+P5",
        "+m6",
        "+M6",
        "+m7",
        "+M7",
        "+P8",
    ]
    ax.set_xticks(range(25), interval_names, rotation=90)
    ax.set_yticks(range(25), interval_names)

    return fig


def duration_transition(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a duration transition

    Helper function for plotdist()

    Args:
        dist (List[List[int]]):
            transition of durations

    Returns:
        A figure of the graph of the duration transition
    """

    fig, ax = plt.subplots()

    # Used code from durdist2_test.py
    fig.set_figwidth(8)
    fig.set_figheight(6)
    im = ax.imshow(dist_array, cmap="gray_r", interpolation="nearest")
    fig.colorbar(im, label="Probability")
    ax.set_xlabel("Duration (to)")
    ax.set_ylabel("Duration (from)")
    ax.title("2nd Order Duration Distribution")

    bin_centers = [
        "1/4",
        "sqrt(2)/4",
        "1/2",
        "sqrt(2)/2",
        "1",
        "sqrt(2)",
        "2",
        "2*sqrt(2)",
        "4",
    ]
    ax.set_xticks(range(len(bin_centers)), bin_centers)
    ax.set_yticks(range(len(bin_centers)), bin_centers)

    ax.invert_yaxis()

    return fig


def key_correlation(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a key correlation

    Helper function for plotdist()

    Args:
        dist (List[int]):
            Distribution of interval sizes

    Returns:
        A figure of the graph of the interval size distribution
    """

    fig, ax = plt.subplots()

    keys = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
        "c",
        "c#",
        "d",
        "d#",
        "e",
        "f",
        "f#",
        "g",
        "g#",
        "a",
        "a#",
        "b",
    ]

    ax.bar(keys, dist_array, color="skyblue")
    ax.set_xlabel("Key")
    ax.set_ylabel("Correlation Coefficient")
    ax.set_title("Key Correlation")

    return fig


def interval_size(dist_array: np.ndarray) -> figure.Figure:
    """Creates a graph of a interval size distribution

    Helper function for plotdist()

    Args:
        dist (List[int]):
            Distribution of interval sizes

    Returns:
        A figure of the graph of the interval size distribution
    """

    fig, ax = plt.subplots()

    # Used code from ivsizedist1_test.py
    interval_names = [
        "P1",
        "m2",
        "M2",
        "m3",
        "M3",
        "P4",
        "d5",
        "P5",
        "m6",
        "M6",
        "m7",
        "M7",
        "P8",
    ]
    ax.bar(interval_names, dist_array, color="skyblue")
    ax.set_xlabel("Interval Size")
    ax.set_ylabel("Proportion (%)")
    ax.set_title("Interval Size Distribution")

    return fig
