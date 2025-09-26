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
        color: str = DEFAULT_BAR_COLOR,
        show: bool = True,
        fig: Optional[Figure] = None,
        ax: Optional[Axes] = None,
        kind: str = "bar",
    ) -> Figure:
        """Plot this distribution.

        Parameters
        ----------
        color : str
            Color used for 1-D plots.
        show : bool
            Whether to call ``plt.show()`` at the end.
        fig, ax : matplotlib Figure and Axes
            Provide an existing figure/axes to draw on; if omitted, a new
            figure and axes are created.
        kind : {"bar", "line"}
            Plot style used for 1-D distributions. Ignored for 2-D.

        Notes
        -----
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
            x = range(len(self.x_categories))
            # 1-D distributions: draw either a bar chart or a line chart.
            if kind == "bar":
                ax.bar(x, self.data, color=color)
            elif kind == "line":
                ax.plot(x, self.data, color=color, marker="o")
            else:
                raise ValueError(f"unknown kind for 1D plot: {kind}")

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
            if self.y_categories is not None:
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
        color=DEFAULT_BAR_COLOR,
        show: bool = True,
        kinds: Optional[list[str]] = None,
        colors: Optional[list[str]] = None,
    ) -> Optional[Figure]:
        """
        Plot multiple distributions into a single Figure using vertically
        stacked subplots.

        Notes
        -----
        - 2-D distributions are drawn first (heatmaps), followed by the 1-D
          distributions stacked below them.
        - `kinds` and `colors` apply only to 1-D distributions and must have
          length equal to the number of 1-D inputs.

        Returns
        -------
        Figure or None
            A matplotlib Figure when at least one distribution is plotted;
            otherwise None when `dists` is empty.
        """
        if not dists:
            return None

        # Partition inputs by dimensionality to control layout ordering
        d2 = [d for d in dists if len(d.dimensions) == 2]
        d1 = [d for d in dists if len(d.dimensions) == 1]

        total = len(d2) + len(d1)
        # Create a vertical stack of subplots sized to total count
        fig, axes = plt.subplots(total, 1, squeeze=False)
        axes = axes.ravel()

        # `kinds`/`colors` apply to 1-D only; enforce alignment
        n1 = len(d1)
        if kinds is None:
            kinds = ["bar"] * n1
        if colors is None:
            colors = [DEFAULT_BAR_COLOR] * n1
        if len(kinds) != n1 or len(colors) != n1:
            raise ValueError("kinds/colors must match number of 1-D distributions")

        idx = 0
        # Plot 2-D first to match the documented layout
        for d in d2:
            d.plot(show=False, fig=fig, ax=axes[idx])
            idx += 1
        # Then 1-D with per-kind/color
        for d, k, c in zip(d1, kinds, colors):
            d.plot(kind=k, color=c, show=False, fig=fig, ax=axes[idx])
            idx += 1

        fig.tight_layout()
        if show:
            plt.show()
        return fig

    @classmethod
    def plot_grouped_1d(
        cls,
        dists: List["Distribution"],
        show: bool = True,
        kinds: Optional[list[str]] = None,
        colors: Optional[list[str]] = None,
    ) -> Optional[Figure]:
        """Overlay multiple 1-D distributions on a single axes as grouped bars/lines.

        This function draws all input 1-D distributions in one matplotlib Axes so
        that each category (x bin) shows a "group" of values—one per distribution.
        You can mix plotting styles using the `kinds` argument (for example, some as
        bars and others as lines with markers. Colors are controlled via the
        `colors` list.

        Constraints
        -----------
        - Only 1-D distributions are accepted. All inputs must have the same
          length (number of categories) so they can be grouped per category.
        - The x/y labels and category names are taken from the first
          distribution in `dists`.

        Parameters
        ----------
        dists : list[Distribution]
            1-D distributions to compare in a single plot.
        show : bool
            Whether to call ``plt.show()`` at the end.
        kinds : list[str] | None
            Per-distribution plot style. Allowed values: "bar" or "line".
            Length must match `len(dists)`. If None, all series default to "bar".
        colors : list[str] | None
            Per-distribution color list. Length must match `len(dists)`. If None,
            defaults to a simple palette.

        Returns
        -------
        Figure or None
            A matplotlib Figure if any distributions are plotted; None when
            `dists` is empty.

        How this differs from plot_multiple
        -----------------------------------
        - plot_grouped_1d overlays all 1-D series on a single axes to make
          per-category (bin-by-bin) comparison easy and compact, with a single
          legend.
        - plot_multiple creates a vertical stack of subplots, one per
          distribution (and also supports 2-D heatmaps).
        """
        # Validate inputs
        if not dists:
            return None
        n = len(dists)
        if any(len(d.dimensions) != 1 for d in dists):
            raise ValueError("All distributions must be 1-D for grouped plotting")
        dimension = dists[0].dimensions[0]
        if any(d.dimensions[0] != dimension for d in dists):
            raise ValueError("All 1-D distributions must have the same length")

        labels = [d.name for d in dists]
        if kinds is None:
            kinds = ["bar"] * n
        if colors is None:
            colors = [DEFAULT_BAR_COLOR] * n
        if len(kinds) != n or len(colors) != n:
            raise ValueError("kinds and colors must match number of distributions")

        fig, ax = plt.subplots()

        # Grouped bar arithmetic (unit bar width, grouped per category)
        bar_width = 1
        x_coords = np.arange(dimension) * bar_width * n
        bottom_half, upper_half = n // 2, n - n // 2
        width_idxes = range(-bottom_half, upper_half + 1)
        is_even_offset = ((n + 1) % 2) * bar_width / 2

        ax.set_xticks(x_coords)
        ax.set_xticklabels(dists[0].x_categories)
        ax.set_xlabel(dists[0].x_label)
        ax.set_ylabel(dists[0].y_label)
        ax.set_title("Grouped Histogram Plot for 1-D Distributions")

        for width_idx, dist, label, color, kind in zip(
            width_idxes, dists, labels, colors, kinds
        ):
            x_axis = x_coords + width_idx * bar_width + is_even_offset
            if kind == "bar":
                ax.bar(x_axis, dist.data, width=bar_width, label=label, color=color)
            elif kind in ("line", "plot"):
                ax.plot(x_axis, dist.data, color=color, marker="o", label=label)
            else:
                raise ValueError(f"unsupported kind for grouped plot: {kind}")

        ax.legend()
        fig.tight_layout()
        if show:
            plt.show()
        return fig
