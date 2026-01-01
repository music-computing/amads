"""
The Distribution class represents distributions and distribution metadata.

"""

from typing import Any, List, Union

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# We should not force this on users as it is not compatible with all backends:
# matplotlib.use('TkAgg')


__author__ = "Roger B. Dannenberg"

DEFAULT_BAR_COLOR = "skyblue"


class Distribution:
    """
    Represents a probability distribution or histogram and its metadata.

    See histogram.py for Histogram1D and Histogram2D, which facilitate the
    computation of distributions from data.

    <small>**Author**: Roger B. Dannenberg</small>

    Attributes
    ----------
    name: str
        The name of the distribution used for plot titles.

    data: List[Any]
        The data points for the distribution.

    distribution_type: str
        The type of distribution. Currently used values are
        "pitch_class", "interval", "pitch_class_interval", "duration",
        "interval_size", "interval_direction", "duration",
        "pitch_class_transition", "interval_transition",
        "duration_transition", "key_correlation". This list is
        open-ended and is currently just informational. The value is
        not used for plotting or any other purpose.

    dimensions : List[int]
        The dimensions of the distribution, e.g.
        [12] for a pitch class distribution or [25, 25] for an
        interval_transition (intervals are from -12 to +12 and include
        0 for unison, intervals larger than one octave are ignored).

    x_categories: List[Union[int, float, str]]
        The categories for the x-axis.

    x_label: str
        The label for the x-axis.

    y_categories: List[Union[int, float, str]]
        The categories for the y-axis.

    y_label: str
        The label for the y-axis.

    """

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
        self.name = name
        self.data = data
        self.distribution_type = distribution_type
        self.dimensions = dimensions
        self.x_categories = x_categories
        self.x_label = x_label
        self.y_categories = y_categories
        self.y_label = y_label

    def plot(self, color=DEFAULT_BAR_COLOR, show: bool = True) -> Figure:
        """Create a plot of the distribution.

        Parameters
        ----------
        color
            the color for histogram bars

        show : Optional[bool]
            show the plot before returning

        Returns
        -------
        Figure
            a matplotlib figure object
        """
        if not show:
            plt.ioff()  # turn off interactive mode just in case
        if len(self.dimensions) == 1:
            fig = self._plot_1d(color)
        elif len(self.dimensions) == 2:
            fig = self._plot_2d(color)
        else:
            raise ValueError("Unsupported number of dimensions")
        if show:
            plt.show()
        return fig

    def _plot_1d(self, color=DEFAULT_BAR_COLOR) -> Figure:
        """Create a 1D plot of the distribution.

        Returns
        -------
        Figure
            A matplotlib figure object.
        """

        fig, ax = plt.subplots()
        ax.bar(self.x_categories, self.data, color=color)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        fig.suptitle(self.name)
        return fig

    def _plot_2d(self, color=DEFAULT_BAR_COLOR) -> Figure:
        """Create a 2D plot of the distribution.

        Returns
        -------
        Figure
            A matplotlib figure object.
        """
        fig, ax = plt.subplots()
        cax = ax.imshow(self.data, cmap="gray_r", interpolation="nearest")
        fig.colorbar(cax, ax=ax, label="Proportion")
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        fig.suptitle(self.name)

        # Set x and y axis tick labels
        ax.set_xticks(range(len(self.x_categories)))
        ax.set_xticklabels([str(x) for x in self.x_categories], rotation=45)
        if self.y_categories is not None:
            ax.set_yticks(range(len(self.y_categories)))
            ax.set_yticklabels([str(y) for y in self.y_categories])

        ax.invert_yaxis()
        return fig

    def show(self) -> None:
        """Print information about the distribution"""
        plural = "" if len(self.dimensions) == 1 else "s"
        print(
            f'Distribution: "{self.name}" has dimension{plural} '
            f'{self.dimensions}, x_label: "{self.x_label}", '
            f'y_label: "{self.y_label}", '
            f'distribution_type: "{self.distribution_type}"'
        )
