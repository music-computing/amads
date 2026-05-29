from typing import List

import matplotlib.pyplot as plt
import numpy as np

from amads.core.distribution import Distribution

toy_distribution_1d: List[float] = [
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
]

toy2_distribution_1d: List[float] = [
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
]

toy3_distribution_1d: List[float] = [
    0.160,
    0.020,
    0.110,
    0.130,
    0.015,
    0.105,
    0.030,
    0.200,
    0.080,
    0.030,
    0.030,
    0.090,
]

toy_distribution_2d: List[List[float]] = np.random.dirichlet(
    [1.0] * 12, size=12
).tolist()

PITCHES = [
    "C",
    "C#/Db",
    "D",
    "D#/Eb",
    "E",
    "F",
    "F#/Gb",
    "G",
    "G#/Ab",
    "A",
    "A#/Bb",
    "B",
]

RELATIVE_TO_TONIC = [f"{i}" for i in range(12)]


def demo_individual_plot_per_window(dists):
    """Plot each distribution in its own window.

    For 1-D distributions, use a line plot and use `kind` option.
    """
    for dist in dists:
        if len(dist.dimensions) == 1:
            _ = dist.plot(option="line", show=False)
        else:
            _ = dist.plot(show=False)

    plt.show()
    return


def demo_multiple_plots_per_window(dists):
    """Stack multiple distributions into one figure.

    Provide `kinds` here to set all 1-D distributions to line plots to test the API.
    """
    kinds = ["line"] * len(dists)
    Distribution.plot_multiple(dists, options=kinds)
    return


def demo_plot_grouped_1d(dists):
    """Grouped bar/line comparison for 1-D dists.

    Mix bar and line kinds to demonstrate the new `kinds` option.
    """
    # If there are exactly two, show bar vs line; otherwise default all to bar
    if len(dists) == 2:
        kinds = ["bar", "line"]
    else:
        kinds = "bar"
    Distribution.plot_grouped_1d(dists, options=kinds)
    return


def demo_vertical_lines_1d(dists):
    """Stack multiple 1-D distributions vertically as line plots.

    This compares shapes without overlapping them in a single axes.
    """
    kinds = "line"
    Distribution.plot_multiple(dists, options=kinds)
    return


def main():
    dist1 = Distribution(
        name="example 1D bar plot",
        data=toy_distribution_1d,
        distribution_type="pitch_class",
        dimensions=[12],
        x_categories=PITCHES,  # type: ignore (list[str] is compatible)
        x_label="Pitch class",
        y_categories=None,
        y_label="Probability",
    )
    dist2 = Distribution(
        name="example 2D heatmap",
        data=toy_distribution_2d,
        distribution_type="pitch_class",
        dimensions=[12, 12],
        x_categories=RELATIVE_TO_TONIC,  # type: ignore (list[str] is compatible)
        x_label="Chromatic Scale Degrees",
        y_categories=PITCHES,  # type: ignore (list[str] is compatible)
        y_label="Key",
    )
    dist3 = Distribution(
        name="example 1D bar plot (toy2)",
        data=toy2_distribution_1d,
        distribution_type="pitch_class",
        dimensions=[12],
        x_categories=PITCHES,  # type: ignore (list[str] is compatible)
        x_label="Pitch class",
        y_categories=None,
        y_label="Probability",
    )
    dist4 = Distribution(
        name="example 1D bar plot (toy3)",
        data=toy3_distribution_1d,
        distribution_type="pitch_class",
        dimensions=[12],
        x_categories=PITCHES,  # type: ignore (list[str] is compatible)
        x_label="Pitch class",
        y_categories=None,
        y_label="Probability",
    )

    dist_list = [dist1, dist2]
    dist_list_1d = [dist1, dist3]
    dist_list_1d_three = [dist1, dist3, dist4]

    # Individual plots: 1-D will be line; 2-D is heatmap
    demo_individual_plot_per_window([dist1, dist2, dist3])
    # Mixed 1D+2D stacked; 1-D entries will be lines
    demo_multiple_plots_per_window(dist_list)
    # Grouped 1-D with bar vs line
    demo_plot_grouped_1d(dist_list_1d)
    # Grouped 1-D with three bar series
    demo_plot_grouped_1d(dist_list_1d_three)
    # Vertically stacked line plots for 1-D distributions
    demo_vertical_lines_1d(dist_list_1d)


if __name__ == "__main__":
    main()
