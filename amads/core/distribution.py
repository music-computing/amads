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

    # class variable detailing the possible 1D plot options
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
        option: str = "bar",
        show: bool = True,
    ) -> Figure:
        """
        plot function to visualize a distribution's data.
        In the 1d case, color denotes bar or line color against a white
        background, while option denotes whether the plot is a line plot
        ("line") or bar plot ("bar").
        NOTE: color, and option are ignored in the 2d case.
        If there are worthwhile plot variants or visualization tools
        for 2d distributions, we will add additional options specifically
        for the 2d case in the future.

        Args:
        color: str
            color of the plot. This option is ignored in the 2d case.
        option: str
            (1) In the 1d case, "bar" or "line" for
            plotting a bar or line graph, respectively.
            (2) In the 2d case, this option is ignored
        show: bool
            whether or not to display the plot before returning from this function

        Returns:
            Figure - A matplotlib figure object.
        """
        fig, ax = plt.subplots()
        return self._subplot(fig, ax, color, option, show)

    def _subplot(
        self,
        fig: Figure,
        ax: Axes,
        color: str = DEFAULT_BAR_COLOR,
        option: str = "bar",
        show: bool = True,
    ) -> Figure:
        """
        Subplot is a special function that is invoked when attempting to plot
        multiple things within the same window.

        Has the same toggle options and behavior as the plot method, but
        also includes the addition of fig (matplotlib Figure) and ax
        (matplotlib Axes) to allow a caller to manipulate multiple plots of
        independent Distributions in a single window.
        This is due to matplotlib requiring all plots to be plotted in a single window
        be plotted on to Axes objects pertaining to the same constituent Figure object.

        Returns:
            Figure - A matplotlib figure object.
        """
        if len(self.dimensions) == 1:
            fig = self._plot_1d(fig=fig, ax=ax, color=color, option=option)
        elif len(self.dimensions) == 2:
            fig = self._plot_2d(fig=fig, ax=ax)
        else:
            raise ValueError("Unsupported number of dimensions for Distribution class")
        if show:
            plt.show()
        return fig

    def _plot_1d(
        self, fig: Figure, ax: Axes, color: str = DEFAULT_BAR_COLOR, option: str = "bar"
    ) -> Figure:
        """Create a 1d plot of the distribution.
        Returns:
            Figure - A matplotlib figure object.
        """
        if option not in Distribution.POSSIBLE_1D_PLOT_OPTIONS:
            raise ValueError(
                f"invalid 1-d plot option {option},"
                f" expected one of {Distribution.POSSIBLE_1D_PLOT_OPTIONS}"
            )
        if option == "bar":
            ax.bar(self.x_categories, self.data, color=color)
        elif option == "line":
            # this was what I originally put here for line plots...
            # but it seemed (honestly still seems) extremely ugly... Ah well...
            # Hopefully this helps make a prettier line graph option...
            ax.plot(self.x_categories, self.data, color=color, marker="o")
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_title(self.name)
        return fig

    def _plot_2d(self, fig: Figure, ax: Axes) -> Figure:
        """Create a 2d plot of the distribution.
        Returns:
            Figure - A matplotlib figure object.
        """
        cax = ax.imshow(
            self.data, cmap="gray_r", aspect="auto", interpolation="nearest"
        )
        fig.colorbar(cax, ax=ax, label="Proportion")
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_title(self.name)

        # Set x and y axis tick labels
        ax.set_xticks(range(len(self.x_categories)))
        # we don't need to rotate by 45 degrees since labels are not verbose
        ax.set_xticklabels(self.x_categories)
        ax.set_yticks(range(len(self.y_categories)))
        ax.set_yticklabels(self.y_categories)

        ax.invert_yaxis()
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
        color: str = DEFAULT_BAR_COLOR,
        option: str = "bar",
        show: bool = True,
    ) -> Optional[Figure]:
        """
        Plots multiple distributions into a singular Figure, leveraging
        the _subplot method of Distributions to plot multiple distributions
        stacked on top of each other in a single window.

        Returns:
            Figure - A matplotlib figure object if any distribution gets plotted
        """
        if not dists:
            return None
        fig, axes = plt.subplots(len(dists), 1)
        # apparently when we get a singleton element, axes is not a list
        if len(dists) == 1:
            return dists[0]._subplot(
                fig=fig, ax=axes, color=color, option=option, show=False
            )
        for dist, ax in zip(dists, axes):
            dist._subplot(fig=fig, ax=ax, color=color, option=option, show=False)
        fig.tight_layout()
        if show:
            plt.show()
        return fig

    @classmethod
    def plot_grouped_1d(
        cls,
        dists: List["Distribution"],
        option: str = "bar",
        show: bool = True,
    ) -> Optional[Figure]:
        """
        Plots multiple 1d distributions of the same type (e.g. same dimensions,
        same data visualization) in a grouped graph: either multiple line plot or grouped
        bar graph if option is "line" or "bar", respectively.
        This is a custom plot method specifically for multiple 1d distributions
        of the same type, and is independent of other generic multiple plot methods
        that leverage _subplot.

        Returns:
            Figure - A matplotlib figure object if any distribution gets plotted
        """
        if not dists:
            return None
        if option not in cls.POSSIBLE_1D_PLOT_OPTIONS:
            raise ValueError(
                f"invalid 1-d plot option {option},"
                f" expected one of {cls.POSSIBLE_1D_PLOT_OPTIONS}"
            )
        if any(len(dist.dimensions) != 1 for dist in dists):
            raise ValueError("Invalid list of distributions to be plotted")
        if any(dist.dimensions[0] != dists[0].dimensions[0] for dist in dists):
            raise ValueError("Invalid list of distributions to be plotted")
        if any(dists[0].distribution_type != dist.distribution_type for dist in dists):
            raise ValueError("Not all distributions to be plotted of the same type")
        # actual plotting...
        # data and label iterators
        data_iterator = (dist.data for dist in dists)
        dist_title_iterator = (dist.name for dist in dists)
        # grouped plot related arithmetic (to properly scale the bars)
        num_dists = len(dists)
        # bar width is arbitrary, since everything else is scaled off of bar width
        bar_width = 1
        dimension = dists[0].dimensions[0]
        # since everything is scaled off of each other, we could realistically
        # just ditch bottom_half and upper_half and offset everything...
        bottom_half, upper_half = num_dists // 2, num_dists - num_dists // 2
        width_idxes = range(-bottom_half, upper_half + 1)
        x_coords = np.arange(dimension) * bar_width * num_dists
        is_even_offset = ((num_dists + 1) % 2) * bar_width / 2
        # plotting grouped bar graph
        fig, ax = plt.subplots()
        # set proper scale for tick labels
        ax.set_xticks(x_coords)
        # other plotting stuff like ticks, labels, titles, etc.
        ax.set_title("Grouped Histogram Plot for 1-D Distributions")
        ax.set_xlabel(dists[0].x_label)
        ax.set_xticklabels(dists[0].x_categories)
        ax.set_ylabel(dists[0].y_label)
        for width_idx, data, dist_title in zip(
            width_idxes, data_iterator, dist_title_iterator
        ):
            if option == "bar":
                x_axis = x_coords + width_idx * bar_width + is_even_offset
                ax.bar(x_axis, data, width=bar_width, label=dist_title)
            elif option == "line":
                # this is primarily where the problem occur when plotting a line graph...
                # normalized graphs are very ugly with lots of crossing lines here...
                ax.plot(x_coords, data, marker="o", label=dist_title)
        # labelled in ax.bar already...
        ax.legend()

        if show:
            plt.show()

        return fig
