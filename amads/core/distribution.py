"""
Distributions Module

The Distribution class represents distributions and distribution metadata.

Author(s): [Roger Dannenberg, Tai Nakamura, Di Wang]
Date: [2024-12-04]

Description:
    [Add a detailed description of what this module does and its primary responsibilities]

Dependencies:
    - matplotlib

Usage:
    [Add basic usage examples or import statements]
"""

from typing import Any, Iterable, List, Optional, Union

# We should not force this on users as it is not compatible with all backends:
# matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def norm_1d(
    profile: Iterable,
    round_places: Optional[int] = None,
) -> np.array:
    """
    Copied implementation from algorithms/norm.py with some modification
    because using the original will cause a circular dependency in the package

    Notes
    -----
    - This normalizes a 1-D vector to L1 (sum to 1). If `round_places` is
      provided, the result is rounded for display/consistency.
    """
    norm_ord = 1
    norm_dist = profile / np.linalg.norm(profile, ord=norm_ord)

    if round_places is None:
        return norm_dist
    elif isinstance(round_places, int):
        return np.round(norm_dist, round_places)
    else:
        raise ValueError(
            f"invalid round_places parameter {round_places}, expected int or None"
        )


# Default color for 1-D bar charts
DEFAULT_BAR_COLOR = "skyblue"


class Distribution:
    """
    Represents a probability distribution and its metadata.

    Attributes
    ----------
    name: str
        The name of the distribution used for plot titles.

    data: List[Any]
        The data points for the distribution.

    distribution_type: str
        The type of distribution, one of "pitch_class", "interval",
        "pitch_class_interval", "duration", "interval_size",
        "interval_direction", "duration", "pitch_class_transition",
        "interval_transition", "duration_transition", "key_correlation"

    dimensions: List[int]
        The dimensions of the distribution, e.g. [12] for a pitch class
        distribution or [25, 25] for an interval_transition (intervals
        are from -12 to +12 and include 0 for unison, intervals larger
        than one octave are ignored).

    x_categories: List[Union[int, float, str]]
        The categories for the x-axis.

    x_label: str
       The label for the x-axis.

    y_categories: List[Union[int, float, str]]
        The categories for the y-axis.

    y_label: str
        The label for the y-axis.
    """

    # Class variable documenting allowable 1-D plotting styles
    POSSIBLE_1D_PLOT_OPTIONS = ["bar", "line"]

    def __init__(
        self,
        name: str,
        data: List[Any],
        distribution_type: str,
        dimensions: List[int],
        x_categories: List[Union[int, float, str]],
        x_label: str,
        y_categories: Union[List[Union[int, float, str]], None],
        y_label: str,
    ):
        """
        Initialize a Distribution instance.
        """
        self.name = name
        self.data = data
        self.distribution_type = distribution_type
        self.dimensions = dimensions
        self.x_categories = x_categories
        self.x_label = x_label
        self.y_categories = y_categories
        self.y_label = y_label

    def normalize(self):
        """
        Convert weights or counts to a probability distribution that sums to 1.
        """
        self.data = norm_1d(self.data).tolist()
        return self

    def plot(
        self,
        color: Optional[str] = DEFAULT_BAR_COLOR,
        option: Optional[str] = "bar",
        show: bool = True,
        fig: Optional[Figure] = None,
        ax: Optional[Axes] = None,
    ) -> Figure:
        """
        Virtual plot function for Distribution.
        Allows standalone plotting of a Distribution (when fig and ax are None),
        while providing enough extensibility to invoke this plot function or its
        overwritten variants for subplotting when fig and ax are provided as
        arguments.

        Parameters
        ----------
        color : Optional[str]
            Plot color string specification. In this particular plot function,
            it is handled in 1-D distributions and ignored in 2-D distributions.
            None for default option (DEFAULT_BAR_COLOR).
        option : Optional[str]
            Plot style string specification. In this particular plot function,
            only {"bar", "line"} are valid string arguments that will be handled
            in a 1-D distribution, while any argument is ignored in 2-D distributions
            None for default option ("bar").
        show : bool
            Whether to call ``plt.show()`` at the end.
        fig, ax : matplotlib Figure and Axes
            Provide an existing figure/axes to draw on; if omitted, a new
            figure and axes are created.

        Notes
        -----
        Behavior to this specific plot method:
        - 1-D: bar (default) or line when kind is "line"
        - 2-D: heatmap
        """
        dims = len(self.dimensions)
        if dims not in (1, 2):
            raise ValueError("Unsupported number of dimensions for Distribution class")

        # Figure/axes handling: either both `fig` and `ax` are provided, or
        # neither; in the latter case, create a new figure/axes pair.
        if fig is None:
            if ax is not None:
                raise ValueError("invalid figure/axis combination")
            fig, ax = plt.subplots()
        else:
            if ax is None:
                raise ValueError("invalid figure/axis combination")

        if dims == 1:
            if color is None:
                color = DEFAULT_BAR_COLOR
            if option is None:
                option = "bar"
            x = range(len(self.x_categories))
            # 1-D distributions: draw either a bar chart or a line chart.
            if option == "bar":
                ax.bar(x, self.data, color=color)
            elif option == "line":
                ax.plot(x, self.data, color=color, marker="o")
            else:
                raise ValueError(f"unknown kind for 1D plot: {option}")

            ax.set_xticks(list(x))
            ax.set_xticklabels(self.x_categories)
            ax.set_xlabel(self.x_label)
            ax.set_ylabel(self.y_label)
            ax.set_title(self.name)

        else:  # dims == 2
            # 2-D distributions: render as a heatmap with a colorbar.
            data = np.asarray(self.data)
            cax = ax.imshow(data, cmap="gray_r", aspect="auto", interpolation="nearest")
            fig.colorbar(cax, ax=ax, label="Proportion")

            ax.set_xlabel(self.x_label)
            ax.set_ylabel(self.y_label)
            ax.set_title(self.name)

            ax.set_xticks(range(len(self.x_categories)))
            ax.set_xticklabels(self.x_categories)
            ax.set_yticks(range(len(self.y_categories)))
            ax.set_yticklabels(self.y_categories)

            ax.invert_yaxis()

        fig.tight_layout()
        if show:
            plt.show()
        return fig

    def show(self) -> None:
        """Print information about the distribution"""
        plural = "" if len(self.dimensions) == 1 else "s"
        print(
            f'Distribution: "{self.name}" has dimension{plural}',
            f' {self.dimensions}, x_label: "{self.x_label}",'
            f' y_label: "{self.y_label}"',
        )

    @classmethod
    def plot_multiple(
        cls,
        dists: List["Distribution"],
        show: bool = True,
        options: Optional[Union[str, List[str]]] = None,
        colors: Optional[Union[str, List[str]]] = None,
    ) -> Optional[Figure]:
        """
        Plot multiple distributions into a single Figure using vertically
        stacked subplots.

        Notes
        -----
        - distributions are plotted in the same order they were presented in
          dists list
        - as long as a Distribution or inherited class has a valid plot function
          implemented, the relevant plot will be mapped here
        - `options` and `colors` apply to all distributions
        - Although the original plot function is only limited to
          `option` and `color` being used in the 1-D case, it is not to say
          that a class inheriting Distribution won't leverage these arguments.
        - You can pass either a list (per-series) or a single string. When a
          single string is provided, it will be broadcast to all inputs.
          For example, kinds="line" makes all 1-D plots line charts.

        Returns
        -------
        Figure or None
            A matplotlib Figure when at least one distribution is plotted;
            otherwise None when `dists` is empty.

        Parameters
        ----------
        dists : list[Distribution]
            Distributions to plot. 2-D are rendered as heatmaps; 1-D below them.
        show : bool
            Whether to call ``plt.show()`` at the end.
        kinds : str | list[str] | None
            plot style per distribution (e.g. "bar" or "line"). If a single
            string is given, it is broadcast to all distributions. If None,
            defaults to "bar".
        colors : str | list[str] | None
            color option per distribution. If a single string is given, it is
            broadcast to all 1-D distributions. If None, defaults to
            the single color DEFAULT_BAR_COLOR.
        """
        if not dists:
            return None

        # when single string, broadcast to all distributions
        if options is None:
            options = ["bar"] * len(dists)
        if colors is None:
            colors = [DEFAULT_BAR_COLOR] * len(dists)
        if isinstance(options, str):
            options = [options] * len(dists)
        if isinstance(colors, str):
            colors = [colors] * len(dists)
        if len(options) != len(dists) or len(colors) != len(dists):
            raise ValueError(
                "kinds/colors must match number of distributions in list case"
            )

        # Create a vertical stack of subplots sized to total count
        fig, axes = plt.subplots(len(dists), 1, squeeze=False)
        axes = axes.ravel()
        # use an axes iterator here
        ax_iter = iter(axes)
        for d, k, c in zip(dists, options, colors):
            ax = next(ax_iter)
            d.plot(color=c, option=k, show=False, fig=fig, ax=ax)

        fig.tight_layout()
        if show:
            plt.show()
        return fig

    @classmethod
    def plot_grouped_1d(
        cls,
        dists: List["Distribution"],
        show: bool = True,
        options: Optional[Union[str, List[str]]] = None,
        colors: Optional[Union[str, List[str]]] = None,
    ) -> Optional[Figure]:
        """Overlay multiple 1-D distributions on a single axes as grouped bars/lines.

        This function draws all input 1-D distributions in one matplotlib Axes so
        that each category (x bin) shows a "group" of values—one per distribution.
        You can mix plotting styles using the `kinds` argument (for example, some as
        bars and others as lines with markers. Colors are controlled via the
        `colors` argument.

        Constraints
        -----------
        - Only 1-D distributions are accepted. All inputs must have the same
          length (number of categories) so they can be grouped per category.
        - The x/y labels and category names are taken from the first
          distribution in `dists`. Hence, this function does not support
          overlaying 1-D distributions with different categories and labels.

        Parameters
        ----------
        dists : list[Distribution]
            1-D distributions to compare in a single plot.
        show : bool
            Whether to call ``plt.show()`` at the end.
        kinds : str | list[str] | None
            Per-distribution plot style. Allowed values: "bar" or "line".
            You can provide a single string to apply to all series (broadcast),
            or a list with length `len(dists)`. If None, all series default to
            "bar".
        colors : str | list[str] | None
            Per-distribution color list. You can provide a single string to
            apply to all series (broadcast), or a list with length `len(dists)`.
            If None, a distinct default color palette is applied (rcParams cycle
            or the tab10 palette).

        Returns
        -------
        Figure or None
            A matplotlib Figure if any distributions are plotted; None when
            `dists` is empty.

        How this differs from plot_multiple
        -----------------------------------
        - plot_grouped_1d overlays all 1-D distributions on a single axes to allow:
          (1) per-category (bin-by-bin) comparison intuitive and compact for grouped bar graphs
          (2) intuitive and compact gradient comparison for overlaid line graphs.
          Since all distributions are plotted in a single plot, we can compare all plots
          within a single legend.
        - plot_multiple creates a vertical stack of subplots, one per
          distribution, while leveraging the plot attribute of each Distribution
          (and also supports 2-D heatmaps).
        """
        # Validate inputs
        if not dists:
            return None
        if any(len(d.dimensions) != 1 for d in dists):
            raise ValueError("All distributions must be 1-D for grouped plotting")
        # number of categories for each plot in the 1d distribution
        dimension = dists[0].dimensions[0]
        if any(d.dimensions[0] != dimension for d in dists):
            raise ValueError("All 1-D distributions must have the same length")
        # labels and categories will need to be the same...
        # or else some of the data visualization for axes will be misleading
        # since this function does not support plotting multiple axes labels
        # and categories on the same plot
        if any(
            d.x_label != dists[0].x_label or d.y_label != dists[0].y_label
            for d in dists
        ):
            raise ValueError("All 1-D distributions must have same axes labels")
        if any(
            d.x_categories != dists[0].x_categories
            or d.y_categories != dists[0].y_categories
            for d in dists
        ):
            raise ValueError("All 1-D distributions must have same axes categories")

        # when single string, broadcast to all
        if isinstance(options, str):
            options = [options] * len(dists)
        if isinstance(colors, str):
            colors = [colors] * len(dists)
        if options is None:
            options = ["bar"] * len(dists)
        if colors is None:
            base_colors = plt.get_cmap("tab10").colors  # デフォルトの10色
            colors = [base_colors[i % len(base_colors)] for i in range(len(dists))]
        if len(options) != len(dists) or len(colors) != len(dists):
            raise ValueError("kinds and colors must match number of distributions")

        bar_graph_info = None
        line_graph_info = None
        # partition bar graphs and line graphs to be plotted separately
        # (so that line graphs don't each take up a bin themselves)
        if isinstance(options, list):
            bar_graph_info = [
                (dist, color)
                for dist, kind, color in zip(dists, options, colors)
                if kind == "bar"
            ]
            line_graph_info = [
                (dist, color)
                for dist, kind, color in zip(dists, options, colors)
                if kind in ("line", "plot")
            ]

        fig, ax = plt.subplots()

        # Grouped bar arithmetic (unit bar width, grouped per category)
        # must have at least 1 bin for the line plot to be valid
        n = max(len(bar_graph_info), 1)
        # bar_width does not matter here, since everything in the grouped bar
        # graph is scaled according to this variable
        bar_width = 1
        x_coords = np.arange(dimension) * bar_width * n
        bottom_half, upper_half = n // 2, n - n // 2
        width_idxes = range(-bottom_half, upper_half + 1)
        is_even_offset = ((n + 1) % 2) * bar_width / 2

        # setting plot axes
        ax.set_xticks(x_coords)
        ax.set_xticklabels(dists[0].x_categories)
        ax.set_xlabel(dists[0].x_label)
        ax.set_ylabel(dists[0].y_label)
        ax.set_title("Grouped Histogram Plot for 1-D Distributions")

        for width_idx, (dist, color) in zip(width_idxes, bar_graph_info):
            x_axis = x_coords + width_idx * bar_width + is_even_offset
            ax.bar(x_axis, dist.data, width=bar_width, label=dist.name, color=color)

        for dist, color in line_graph_info:
            ax.plot(x_coords, dist.data, color=color, marker="o", label=dist.name)

        ax.legend()
        fig.tight_layout()
        if show:
            plt.show()
        return fig
