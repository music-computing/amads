"""
The Distribution class represents distributions and distribution metadata.

<small>**Author**: Roger Dannenberg, Tai Nakamura, Di Wang</small>
"""

import math
from typing import Any, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from amads.algorithms.norm import normalize
from amads.core.histogram import Histogram1D
from amads.core.pitch import Pitch

# We should not force this on users as it is not compatible with all backends:
# matplotlib.use('TkAgg')

__author__ = ["Roger Dannenberg", "Tai Nakamura", "Di Wang"]


class Distribution:
    """
    Represents a probability distribution or histogram and its metadata.

    See histogram.py for Histogram1D and Histogram2D, which facilitate the
    computation of distributions from data.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    name: str
        The name of the distribution used for plot titles.

    data: List[Any]
        The data points for the distribution.

    distribution_type: str
        The type of distribution. Currently used values are described
        below. "weights" can mean either probabilities or raw counts.

        - "pitch_class" - weights for 12 pitch classes, possibly weighted
            by duration.
        - "interval" - weights for pitch intervals, possibly weighted by
            duration.
        - "pitch_class_interval" - weights for pitch class intervals,
            possibly weighted by duration.
            (mod 12, not currently used; should there also be a
            pitch_class_size based on absolute interval size mod 12?
            And if so, should there be an interval_class computed from
            interval mod 12? And interval_size_class based on absolute
            interval size mod 12? Note that "interval" ignores intervals
            larger than one octave.)
        - "duration" - weights for durations
        - "interval_size" - weights for interval sizes, possibly weighted
            by duration.
        - "interval_direction" - proportion of upward intervals for each
            interval size, possibly weighted by duration.
        - "pitch_class_transition" - weights for pitch class transitions,
            possibly weighted by duration (2-dimensional distribution).
        - "interval_transition" - weights for interval transitions,
            possibly weighted by duration (2-dimensional distribution).
        - "duration_transition" - weights for duration transitions,
            possibly weighted by duration (2-dimensional distribution).
        - "key_correlation" - weights for key correlations, generally
            correlation with 12 major key profiles followed by
            correlations with 12 minor key profiles.
        - "symmetric_key_profile" - weights for symmetric key profiles.
            Key profiles themselves are distributions. Symmetric keys
            use the same 12 weights for all keys (e.g.,, Krumhansl-Kessler),
            simply rotated for each key.
        - "asymmetric_key_profile" - weights for asymmetric key profiles,
            where each key has its own set of 12 weights (e.g.,, Bellman-Budge).
        - "root_support_weights" - root support weights (see
            `amads.harmony.root_finding.parncutt`)
        - "pitch" - weights over raw (MIDI) pitch numbers,
            e.g.,, for vocal/instrumental range, as opposed to pitch *class* (as above).
            See `Distribution.from_pitches` for a constructor that builds
            one of these directly from a list of pitches.

        This list is open-ended (see `Distribution.KNOWN_TYPES`) and is
        currently just informational: the value is not used to control
        plotting, except that `distribution_type="pitch"` changes the
        default 1-D plot style from "bar" to "line" (see `plot`).

    dimensions : List[int]
        The dimensions of the distribution, e.g.,
        [12] for a pitch class distribution or [25, 25] for an
        interval_transition (intervals are from -12 to +12 and include
        0 for unison, intervals larger than one octave are ignored).

    x_categories: List[Union[int, float, str]]
        The categories for the x-axis.

    x_label: str
        The label for the x-axis.

    y_categories: Optional[List[Union[int, float, str]]]
        The categories for the y-axis, if any, otherwise None.

    y_label: str
        The label for the y-axis.

    Attributes
    ----------
    same as Parameters (above)
    """

    # Class variable documenting allowable 1-D plotting styles
    POSSIBLE_1D_PLOT_OPTIONS = ["bar", "line"]

    # Default color for 1-D bar charts
    DEFAULT_BAR_COLOR = "skyblue"

    # Known/recommended distribution_type values
    # (informational only, see `distribution_type` docs above)
    KNOWN_TYPES = frozenset(
        {
            "pitch_class",
            "pitch",
            "interval",
            "pitch_class_interval",
            "duration",
            "interval_size",
            "interval_direction",
            "pitch_class_transition",
            "interval_transition",
            "duration_transition",
            "key_correlation",
            "symmetric_key_profile",
            "asymmetric_key_profile",
            "root_support_weights",
        }
    )

    # Special case Beyond this many semitones of span, from_pitches() thins x-axis
    # labels down to one per octave so they stay legible.
    PITCH_WIDE_RANGE_SEMITONES = 24

    def __init__(
        self,
        name: str,
        data: List[Any],
        distribution_type: str,
        dimensions: List[int],
        x_categories: List[Union[int, float, str]],
        x_label: str,
        y_categories: Optional[List[Union[int, float, str]]],
        y_label: str,
    ):
        """
        Initialize a Distribution instance.

        Raises
        ------
        ValueError
            If `dimensions` is not 1-D or 2-D, or if `data`,
            `x_categories`, or `y_categories` are inconsistent with
            `dimensions` (see `_validate`).
        """
        self.name = name
        self.data = data
        self.distribution_type = distribution_type
        self.dimensions = dimensions
        self.x_categories = x_categories
        self.x_label = x_label
        self.y_categories = y_categories
        self.y_label = y_label
        self._validate()

    def _validate(self) -> None:
        """
        Check that `data`, `dimensions`, `x_categories`, and `y_categories` are mutually consistent.
        Called automatically by `__init__`;
        also safe to call again after mutating `data` in place.

        Raises
        ------
        ValueError
            If any of the checks described above fail.
        """
        dims = len(self.dimensions)
        if dims not in (1, 2):
            raise ValueError(
                "Distribution only supports 1-D or 2-D data, got "
                f"dimensions={self.dimensions}"
            )

        data_shape = np.asarray(self.data).shape
        if data_shape != tuple(self.dimensions):
            raise ValueError(
                f"data shape {data_shape} does not match "
                f"dimensions {tuple(self.dimensions)}"
            )

        if len(self.x_categories) != self.dimensions[0]:
            raise ValueError(
                f"x_categories has length {len(self.x_categories)}, "
                f"expected {self.dimensions[0]} (dimensions[0])"
            )

        if dims == 1:
            if self.y_categories is not None:
                raise ValueError(
                    "y_categories must be None for a 1-D distribution"
                )
        else:  # dims == 2
            if self.y_categories is None:
                raise ValueError(
                    "y_categories is required for a 2-D distribution"
                )
            if len(self.y_categories) != self.dimensions[1]:
                raise ValueError(
                    f"y_categories has length {len(self.y_categories)}, "
                    f"expected {self.dimensions[1]} (dimensions[1])"
                )

    def normalize(self, method: str = "Sum"):
        """
        Convert weights or counts to a probability distribution.

        Parameters
        ----------
        method : str
            Normalization method, forwarded to
            `amads.algorithms.norm.normalize`.
            Any value accepted there is valid here, e.g., "Sum"/"l1"
            (values sum to 1, the default and previous hard-coded behavior),
            "Euclidean"/"l2" (vector length 1), or "max"/"infinity"
            (largest value becomes 1).

        Returns
        -------
        Distribution
            self, for chaining.

        Notes
        -----
        For a 2-D distribution, `data` is flattened before normalizing and reshaped back afterward,
        so e.g., the default "Sum" normalizes over the *entire* matrix
        (all cells sum to 1), not per row or column.
        If you want each row to be its own conditional distribution summing to 1
        (e.g., for a transition matrix),
        normalize each row individually before constructing the Distribution,
        or call `normalize` on single-row slices.
        """
        arr = np.asarray(self.data, dtype=float)
        flat = normalize(arr.flatten(), method)
        self.data = np.asarray(flat).reshape(arr.shape).tolist()
        return self

    @classmethod
    def from_pitches(
        cls,
        pitches: List[Union[Pitch, int, float]],
        name: str = "Pitch Distribution",
        weights: Optional[List[float]] = None,
        buffer: int = 2,
        use_spelling: Optional[bool] = None,
    ) -> "Distribution":
        """
        Build a 1-D `Distribution` of raw pitch (not pitch *class*) from a list of pitches,
        e.g., to plot a vocal or instrumental range.
        Bins are one per semitone across the observed range.

        Parameters
        ----------
        pitches : list of Pitch | int | float
            The pitches to histogram.
            Entries may be `amads.core.pitch.Pitch` instances, or raw numeric MIDI key numbers
            (usually ints; any floats are binned to the nearest semitone).
            The two kinds may be mixed in one list.
        name : str
            Name used for the distribution and as the plot title.
        weights : list of float, optional Per-pitch weights,
            e.g., note durations, aligned element-for-element with `pitches`.
            Defaults to a weight of 1 per pitch, i.e. a plain count histogram.
        buffer : int
            Semitones of empty margin added on each side of the observed min/max pitch
            so extreme values aren't plotted right at the axis edge (default 2).
            Use 0 for no buffer.
        use_spelling : bool, optional
            If True, x-axis bin labels are spelled note names (e.g., "C#4")
            taken from the `Pitch` objects in `pitches`;
            every entry in `pitches` must then be a `Pitch`
            (raw numbers have no spelling to draw on).
            If False, labels are plain MIDI key numbers.
            If None (default), spelling is used automatically when every entry in `pitches` is a `Pitch`,
            and MIDI numbers are used otherwise.

        Returns
        -------
        Distribution
            A 1-D distribution with `distribution_type="pitch"`.
            Bin values are raw (weighted) counts; call `.normalize()` for a probability distribution.
            Bins with no observed pitch get a value of 0.
            For ranges wider than `Distribution.PITCH_WIDE_RANGE_SEMITONES`,
            all but one x-axis label per octave are blanked out so they stay legible;
            the underlying bins/data are unaffected.

        Raises
        ------
        ValueError
            If `pitches` is empty;
            if `weights` is provided and its length doesn't match `pitches`;
            if any entry of `pitches` is not a `Pitch`, `int`, or `float`;
            if any `Pitch` is unpitched (`midi_num is None`);
            or if `use_spelling=True` but not every entry of `pitches` is a `Pitch`.

        Examples
        --------
        >>> from amads.core.pitch import Pitch
        >>> notes = [Pitch("C4"), Pitch("E4"), Pitch("G4"), Pitch("C5"), Pitch("E5"), Pitch("G5")]
        >>> dist = Distribution.from_pitches(notes, name="Soprano range example")
        >>> dist.distribution_type
        'pitch'
        """
        if not pitches:
            raise ValueError("from_pitches requires at least one pitch")
        if weights is not None and len(weights) != len(pitches):
            raise ValueError("weights must be the same length as pitches")
        counted_label = "Count" if weights is None else "Weight"

        midi_nums: List[float] = []
        all_are_pitches = True
        for p in pitches:
            if isinstance(p, Pitch):
                if p.midi_num is None:
                    raise ValueError(
                        "from_pitches does not support unpitched "
                        "Pitch instances (midi_num is None)"
                    )
                midi_nums.append(p.midi_num)
            elif isinstance(p, (int, float)):
                midi_nums.append(float(p))
                all_are_pitches = False
            else:
                raise ValueError(
                    "pitches must contain Pitch, int, or float "
                    f"entries, got {type(p)}"
                )

        if use_spelling is None:
            use_spelling = all_are_pitches
        elif use_spelling and not all_are_pitches:
            raise ValueError(
                "`use_spelling=True` requires every entry in pitches to be a Pitch instance"
            )

        lo = math.floor(min(midi_nums)) - buffer
        hi = math.ceil(max(midi_nums)) + buffer
        bin_centers = list(range(lo, hi + 1))

        hist = Histogram1D(bin_centers=bin_centers, ignore_extrema=False)
        point_weights = (
            weights if weights is not None else [1.0] * len(midi_nums)
        )
        for midi_num, weight in zip(midi_nums, point_weights):
            hist.add_point(midi_num, weight=weight)

        if use_spelling:
            # Prefer the actual spelling of an observed Pitch at each bin (e.g., "C#4" vs "Db4" if given);
            # fall back to the MIDI number for any bin center that wasn't actually observed.
            spellings = {}
            for p in pitches:
                spellings.setdefault(round(p.midi_num), p.name_with_octave)
            labels = [spellings.get(c, str(c)) for c in bin_centers]
            x_label = "Pitch (spelled)"
        else:
            labels = [str(c) for c in bin_centers]
            x_label = "Pitch (MIDI key number)"

        # For wide ranges, thin labels to one per octave for legibility.
        if (hi - lo) > cls.PITCH_WIDE_RANGE_SEMITONES:
            labels = [
                label if (c - lo) % 12 == 0 else ""
                for c, label in zip(bin_centers, labels)
            ]

        return cls(
            name=name,
            data=hist.bins,
            distribution_type="pitch",
            dimensions=[len(bin_centers)],
            x_categories=labels,
            x_label=x_label,
            y_categories=None,
            y_label=counted_label,
        )

    def plot(
        self,
        color: Optional[str] = None,
        option: Optional[str] = None,
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
            None for default option (Distribution.DEFAULT_BAR_COLOR).
        option : Optional[str]
            Plot style string specification. In this particular plot function,
            only {"bar", "line"} are valid string arguments that will be handled
            in a 1-D distribution, while any argument is ignored in 2-D
            distributions. None for default option ("bar").
        show : bool
            Whether to call ``plt.show()`` at the end.
        fig : Figure
            Provide existing Figure to draw on; if omitted, a new
            figure is created.
        ax : Axes
            Provide existing axes to draw on; if omitted, a new
            figure and axes are created.

        Raises
        ------
        ValueError
            A ValueError is raised if:

            - `ax` (axes) but not `fig` (Figure) is provided
            - `dims` is not 1 or 2

        Notes
        -----
        Behavior to this specific plot method:

        - 1-D: bar (default) or line when kind is "line"
        - 2-D: heatmap
        """
        dims = len(self.dimensions)
        if dims not in (1, 2):
            raise ValueError(
                "Unsupported number of dimensions for Distribution class"
            )

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
                color = Distribution.DEFAULT_BAR_COLOR
            if option is None:
                # Dense numeric ranges like raw pitch usually read
                # better as a contour than as many individual bars.
                option = "line" if self.distribution_type == "pitch" else "bar"
            x = range(len(self.x_categories))
            # 1-D distributions: draw either a bar chart or a line chart.
            if option == "bar":
                ax.bar(x, self.data, color=color)
            elif option == "line":
                ax.plot(x, self.data, color=color, marker="o")
            else:
                raise ValueError(f"unknown kind for 1D plot: {option}")

            ax.set_xticks(list(x))
            ax.set_xticklabels([str(label) for label in self.x_categories])
            ax.set_xlabel(self.x_label)
            ax.set_ylabel(self.y_label)
            ax.set_title(self.name)

        else:  # dims == 2
            # 2-D distributions: render as a heatmap with a colorbar.
            data = np.asarray(self.data)
            cax = ax.imshow(
                data, cmap="gray_r", aspect="auto", interpolation="nearest"
            )
            fig.colorbar(cax, ax=ax, label="Proportion")

            ax.set_xlabel(self.x_label)
            ax.set_ylabel(self.y_label)
            ax.set_title(self.name)

            ax.set_xticks(range(len(self.x_categories)))
            ax.set_xticklabels([str(label) for label in self.x_categories])
            if self.y_categories is not None:
                ax.set_yticks(range(len(self.y_categories)))
                ax.set_yticklabels([str(label) for label in self.y_categories])

            ax.invert_yaxis()

        fig.tight_layout()
        if show:
            plt.show()
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
        options : str | list[str] | None
            plot style per distribution (e.g., "bar" or "line").
            If a single string is given, it is broadcast to all distributions.
            If None, defaults to "bar".
        colors : str | list[str] | None
            color option per distribution.
            If a single string is given, it is broadcast to all 1-D distributions.
            If None, defaults to the single color Distribution.DEFAULT_BAR_COLOR.

        Notes
        -----
        - distributions are plotted in the same order they were presented in
          dists list
        - as long as a Distribution or inherited class has a valid plot function
          implemented, the relevant plot will be added to the figure at the
          specified axes.
        - `options` and `colors` apply to all distributions
        - Although the original plot function is only limited to
          `option` and `color` being used in the 1-D case, it is not to say
          that a class inheriting Distribution won't leverage these arguments.
        - You can pass either a list (per-series) or a single string. When a
          single string is provided, it will be broadcast to all inputs.
          For example, kinds="line" makes all 1-D plots line charts.
        """
        if not dists:
            return None

        # when single string, broadcast to all distributions
        options = options or ["bar"] * len(dists)
        colors = colors or [Distribution.DEFAULT_BAR_COLOR] * len(dists)
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
        """Overlay multiple 1-D distributions on a single axes.

        This function draws all input 1-D distributions in one matplotlib
        Axes so that each category (x bin) shows a "group" of values—one
        per distribution. You can mix plotting styles using the `kinds`
        argument (for example, some as bars and others as lines with
        markers. Colors are controlled via the `colors` argument.

        Parameters
        ----------
        dists : list[Distribution]
            1-D distributions to compare in a single plot.
        show : bool
            Whether to call ``plt.show()`` at the end.
        options : str | list[str] | None
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

        Constraints
        -----------
        - Only 1-D distributions are accepted. All inputs must have the same
          length (number of categories) so they can be grouped per category.
        - The x/y labels and category names are taken from the first
          distribution in `dists`. Hence, this function does not support
          overlaying 1-D distributions with different categories and labels.

        How this differs from plot_multiple
        -----------------------------------
        - plot_grouped_1d overlays all 1-D distributions on a single axes
          to allow:
            1. per-category (bin-by-bin) comparison intuitive and compact
               for grouped bar graphs
            2. intuitive and compact gradient comparison for overlaid line
               graphs.

          Since all distributions are plotted in a single plot, we can
          compare all plots within a single legend.
        - plot_multiple creates a vertical stack of subplots, one per
          distribution, while leveraging the plot attribute of each
          Distribution (and also supports 2-D heatmaps).
        """
        # Validate inputs
        if not dists:
            return None
        if any(len(d.dimensions) != 1 for d in dists):
            raise ValueError(
                "All distributions must be 1-D for grouped plotting"
            )
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
            raise ValueError(
                "All 1-D distributions must have same axes categories"
            )

        # when single string, broadcast to all
        if isinstance(options, str):
            options = [options] * len(dists)
        if isinstance(colors, str):
            colors = [colors] * len(dists)
        if options is None:
            options = ["bar"] * len(dists)
        if colors is None:
            # get the default ListedColormap; get_cmap does not always
            # return an object with .colors, so we have to ignore the type:
            base_colors = plt.get_cmap("tab10").colors  # type: ignore
            colors = [
                base_colors[i % len(base_colors)] for i in range(len(dists))
            ]
        if len(options) != len(dists) or len(colors) != len(dists):
            raise ValueError(
                "kinds and colors must match number of distributions"
            )

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
        ax.set_xticklabels([str(d) for d in dists[0].x_categories])
        ax.set_xlabel(dists[0].x_label)
        ax.set_ylabel(dists[0].y_label)
        ax.set_title("Grouped Histogram Plot for 1-D Distributions")

        for width_idx, (dist, color) in zip(width_idxes, bar_graph_info):
            x_axis = x_coords + width_idx * bar_width + is_even_offset
            ax.bar(
                x_axis, dist.data, width=bar_width, label=dist.name, color=color
            )

        for dist, color in line_graph_info:
            ax.plot(
                x_coords, dist.data, color=color, marker="o", label=dist.name
            )

        ax.legend()
        fig.tight_layout()
        if show:
            plt.show()
        return fig
