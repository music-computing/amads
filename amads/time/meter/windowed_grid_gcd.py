"""
Given a monotonically increasing series of integers (tatum indices),
process (and optionally visualise) GCD across all possible window sizes and start points.
"""

__author__ = "Mark Gotham"


from typing import Sequence, Union

import matplotlib.colors as mpl
import matplotlib.pyplot as plt
import numpy as np

from amads.algorithms.gcd import integer_gcd
from amads.core.vector_transforms_checks import (
    indicator_to_interval,
    indices_to_indicator,
)


def is_monotonic(numbers: Sequence) -> bool:
    """
    Check if a list of numbers is monotonically increasing.
    Return True if so, raises an error if not in order to report on the first fail point.

    Please note that this may function may move if needed elsewhere and
    in that case, edge case behaviour (e.g., 0, None, raises) may also change.

    Parameters
    ----------
        numbers: A sequence (list, tuple, ...) of numeric values (integers, floats, ...).

    Examples
    --------
    >>> is_monotonic([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    True
    >>> is_monotonic([1, 2, 3, 4, 5, 7, 6, 8, 9, 10])
    Traceback (most recent call last):
    ValueError: Data must be monotonically increasing: value 7 at index 5 is not less than 6.

    """
    for i in range(len(numbers) - 1):
        if numbers[i] >= numbers[i + 1]:
            raise ValueError(
                "Data must be monotonically increasing: value "
                f"{numbers[i]} at index {i} is not less than {numbers[i + 1]}."
            )
    return True


def windowed_gcd(
    indices: list, exclude_redundant: bool = True, plot: bool = True
) -> Union[dict | None]:
    """
    Performs windowed GCD calculations on a monotonically increasing list of numbers
    and creates a visualization with time on the x-axis and window size on the y.

    Parameters
    ----------
    indices: A list of monotonically increasing numbers.
    exclude_redundant:
        If True, do not process or plot window sizes
        whose list of GCD is identical to the previous round (window size - 1).
        Default True to save on a lot of processing of trivial data.
    plot: Optionally run `windowed_gcd_visualization` to plot the data.

    Raises
    ------
    If the indices data is not monotonically increasing (see `is_monotonic`).

    Examples
    --------
    Internally, the function processes monotonic indices into windowed intervals.

    >>> monotonic_indices = [0, 1, 2, 4, 6, 7, 10]
    >>> indicator_vector = indices_to_indicator(monotonic_indices)
    >>> indicator_vector
    (1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1)

    >>> indicator_to_interval(indicator_vector, wrap=False)
    (1, 1, 2, 2, 1, 3)

    This function returns a dict where
    keys are the window size,
    and for each key the value is a list of gcds for that size.
    We only store them all if `exclude_redundant=False`.

    >>> windowed_gcd_data = windowed_gcd(monotonic_indices, plot=False, exclude_redundant=False)

    >>> windowed_gcd_data.keys()
    dict_keys([2, 3, 4, 5, 6, 7, 8, 9, 10])

    By defaut, `exclude_redundant=True` so
    >>> windowed_gcd_data = windowed_gcd(monotonic_indices, plot=False)  # exclude_redundant=True
    >>> windowed_gcd_data.keys()
    dict_keys([2, 3, 4, 5, 6])

    >>> windowed_gcd_data[4]
    [1, 1, 2, 2, 1, 1, 1, 3]

    I.e., for the `monotonic_indices` [0, 1, 2, 4, 6, 7, 10] and window size 4 we have:

    0-3 -> indices 0, 1, 2 -> tatum 1
    1-4 -> indices 1, 2, 4 -> tatum 1
    2-5 -> indices 2, 4 -> tatum 2
    3-6 -> indices 2, 4, 6 -> tatum 2
    4-7 -> indices 4, 6, 7 -> tatum 1
    5-8 -> indices 6, 7 -> tatum 1
    6-9 -> indices 6, 7, 10 -> tatum 1
    7-10 -> indices 7, 10 -> tatum 3
    """
    is_monotonic(indices)

    indicator = indices_to_indicator(
        indices, indicator_length=max(indices) + 1
    )  # to include the last value
    max_val = len(indicator)

    gcds_by_window_size = {}
    max_gcd = 1
    last_gcd_list = []  # init empty, then store previous at each step.

    for window_size in range(
        2, max_val
    ):  # window_size 2 is the minimum size for 1 interval (two notes).
        this_window_size_gcd_list = []
        for i in range(0, max_val - window_size + 1):  # sic.
            window = indicator[i : i + window_size]  # Get window from indicator
            within_window_intervals = indicator_to_interval(
                window, wrap=False
            )  # Interval sequence within this window
            if len(within_window_intervals) == 0:
                this_window_size_gcd_list.append(
                    0
                )  # Always append: something for each increment.
            else:
                this_window_size_gcd_list.append(
                    integer_gcd(within_window_intervals)
                )

        if exclude_redundant:

            if all(
                v == 0 for v in this_window_size_gcd_list
            ):  # All zeroes, exclude.
                continue

            if (
                this_window_size_gcd_list == last_gcd_list[:-1]
            ):  # same as the previous entry, skip
                last_gcd_list = this_window_size_gcd_list
                continue

            # If here, meaningful despite `exclude_redundant`, prepare data ...
            last_gcd_list = this_window_size_gcd_list

        # If `exclude_redundant` is False or if `exclude_redundant` is True and passed the above.
        gcds_by_window_size[window_size] = this_window_size_gcd_list
        if max(this_window_size_gcd_list) > max_gcd:
            max_gcd = max(this_window_size_gcd_list)

    if plot:
        windowed_gcd_visualization(
            max_val=max_val,
            max_gcd=max_gcd,
            gcds_by_window_size=gcds_by_window_size,
        )
        return None
    else:
        return gcds_by_window_size


def windowed_gcd_visualization(
    max_val: int, max_gcd: int, gcds_by_window_size: dict
) -> None:
    """
    Create a triangular plot of windowed GCD values,
    analogous to the "keyscape" plots of Sapp et al. for the case of key.

    The x-axis represents tatum position, the y-axis represents window size,
    and each block is coloured by the GCD of the indices within that window.
    Larger window sizes appear higher on the plot, so the topmost row (if present)
    covers the entire piece — typically excluded as redundant by `windowed_gcd`.

    Parameters
    ----------
    max_val : int
        The length of the indicator vector, used to set the x-axis range.
    max_gcd : int
        The maximum GCD value across all windows, used to anchor the discrete colour map.
    gcds_by_window_size : dict
        A dict mapping window size (int) to a list of GCD values (one per tatum position),
        as returned by `windowed_gcd`.

    See Also
    --------
    windowed_gcd : Computes the `gcds_by_window_size` dict passed to this function.
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.grid(axis="x")
    ax.set_xlim(0, max_val)

    cmap = plt.get_cmap(
        "viridis", max_gcd
    )  # discrete: exactly n=max_gcd colours
    bounds = np.arange(
        0.5, max_gcd + 1.5, 1
    )  # boundaries between integers 1..max_gcd
    norm = mpl.BoundaryNorm(bounds, cmap.N)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []
    fig.colorbar(sm, ax=ax, ticks=range(1, max_gcd + 1))

    for window_size_key, gcd_list in gcds_by_window_size.items():
        colors = create_colormap(gcd_list, max_gcd)
        for index, (gcd, color) in enumerate(zip(gcd_list, colors)):
            ax.barh(window_size_key, 1, left=index, height=0.95, color=color)

    ax.set_xlabel("Tatum index")
    ax.set_ylabel("Window Size")
    plt.tight_layout()
    plt.show()


def create_colormap(data, n, name="viridis"):
    """
    Map a list of integer values to discrete colours from a matplotlib colormap.

    Creates a discretised colormap with exactly `n` colours (one per integer from 1 to n),
    ensuring that each integer value gets a distinct, consistent colour rather than
    a continuous interpolation.

    Parameters
    ----------
    data : list or numpy.ndarray
        A list of integer values to map to colours. Expected range: 1 to n.
    n : int
        The number of discrete colours to generate, corresponding to the maximum
        integer value in the data.
    name : str, optional
        A matplotlib colormap name (e.g., 'viridis', 'plasma'). Default: 'viridis'.

    Returns
    -------
    numpy.ndarray
        An array of RGBA colours, one for each value in `data`.

    Examples
    --------
        With `n=3`, three distinct colours are created.
    The first and last values in this
    share a colour since they share an integer value:

    Here is a list of 4 items, but only 3 distinct values.
    >>> test_case = [1, 2, 3, 1]
    >>> colours = create_colormap(test_case, n=3)

    Items at index 0 and 3 have the same value (1) and so return the same colour
    >>> colours[0].tolist() == colours[3].tolist()
    True

    Items at index 0 and 1 have different values and colours:
    >>> colours[0].tolist() == colours[1].tolist()
    False

    See Also
    --------
    windowed_gcd_visualization : Primary caller of this function.
    """
    normalised_data = np.array(data) / n
    cmap = plt.get_cmap(name)
    colours = cmap(normalised_data)

    return colours


# ------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
