"""
Distributions Module

The Distribution class represents distributions and distribution metadata.

Author: [Roger Dannenberg]
Date: [2024-12-04]

Description:
    [Add a detailed description of what this module does and its primary responsibilities]

Dependencies:
    - matplotlib

Usage:
    [Add basic usage examples or import statements]
"""
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import figure
from matplotlib import patches
from typing import Any, List, Union

DEFAULT_BAR_COLOR = "skyblue"

class Distribution:
    """
    Represents a probability distribution and its metadata.

    Attributes:
        name: str - The name of the distribution used for plot titles.

        data: List[Any] - The data points for the distribution.

        distribution_type: str - The type of distribution, one of
            "pitch_class", "interval", "pitch_class_interval", "duration",
            "interval_size", "interval_direction", "duration", 
            "pitch_class_transition", "interval_transition", 
            "duration_transition", "key_correlation"

        dimensions: List[int] - The dimensions of the distribution, e.g.
            [12] for a pitch class distribution or [25, 25] for an
            interval_transition (intervals are from -12 to +12 and include
            0 for unison, intervals larger than one octave are ignored).

        x_categories: List[Union[int, float, str]] - The categories for
            the x-axis.

        x_label: str - The label for the x-axis.

        y_categories: List[Union[int, float, str]] - The categories for
            the y-axis.

        y_label: str - The label for the y-axis.
    """

    def __init__(self, name: str, data: List[Any], distribution_type: str,
                 dimensions: List[int], 
                 x_categories: List[Union[int, float, str]], 
                 x_label: str,
                 y_categories: Union[List[Union[int, float, str]], None], 
                 y_label: str):
        self.name = name
        self.data = data
        self.distribution_type = distribution_type
        self.dimensions = dimensions
        self.x_categories = x_categories
        self.x_label = x_label
        self.y_categories = y_categories
        self.y_label = y_label

    def plot(self, color=DEFAULT_BAR_COLOR):
        if len(self.dimensions) == 1:
            return (plt, self.plot_1d(color))
        elif len(self.dimensions) == 2:
            return (plt, self.plot_2d(color))
        else:
            raise ValueError("Unsupported number of dimensions")

    def plot_1d(self, color=DEFAULT_BAR_COLOR) -> figure.Figure:
        """Create a 1D plot of the distribution.
        Returns:
            figure.Figure - A matplotlib figure object.
        """
        
        fig, ax = plt.subplots()
        ax.bar(self.x_categories, self.data, color=color)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        fig.suptitle(self.name)
        return fig


    def plot_2d(self, color=DEFAULT_BAR_COLOR) -> figure.Figure:
        """Create a 2D plot of the distribution.
        Returns:
            figure.Figure - A matplotlib figure object.
        """
        fig, ax = plt.subplots()
        height = [abs(i - 0.5) if i != 0 else 0 for i in self.x_categories]
        bottom = [min(0.5, i) if i != 0 else 0.5 for i in self.y_categories]
        ax.bar(self.x_categories, height, bottom=bottom, color=color)
        ax.set_ylim(0, 1)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        fig.suptitle(self.name)
        return fig

