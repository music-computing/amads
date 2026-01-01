"""Compute histograms and distributions.

This module provides Histogram1D and Histogram2D classes for computing
one-dimensional and two-dimensional histograms, respectively. Histograms
can be normalized to form probability distributions.

The `bins` attribute can be directly assigned to the `data` attribute of
the `Distribution` class in `core.distribution`.

Histogram bins can be specified either by their centers or their boundaries.
When centers are provided:

  - the number of centers gives the number of bins
  - if ignore_extrema is False, the first and last bins are open-ended,
    counting all values below the first center and above the last center.
    boundaries can be computed from centers using either linear or logarithmic
    interpolation. If provided, boundaries can be of length len(centers) + 1,
    in which case the first and last values are ignored (since the bins are
    open-ended); otherwise, boundaries have length len(centers) - 1.
  - if ignore_extrema is True, the first and last bins are closed, and values
    outside the bin boundaries are ignored. In this case, boundaries must be
    provided and have length len(centers) + 1.

When centers are not provided, boundaries must be provided:

  - the number of bins is len(boundaries) - 1
  - bin centers can be computed as arithmetic or geometric means of boundaries.
  - if ignore_extrema is False, the upper and lower boundaries are ignored,
    making the first and last bins open-ended.
  - if ignore_extrema is True, the first and last bins are closed, and values
    outside the bin boundaries are ignored.
"""

import math
from typing import Optional, cast


def boundaries_to_centers(
    boundaries: list[float], interpolation: str = "linear"
) -> list[float]:
    """
    Convert bin boundaries to bin centers.

    The lower and upper boundaries are only used to compute the
    centers of the bins in between, so the returned list has length
    len(boundaries) - 1, so the lower bin will count all values
    below boundaries[1], and the upper bin will count all values
    above boundaries[-2].

    If interpolation is linear, the center between two boundaries x1
    and x2 is (x1 + x2) / 2. If interpolation is 'log', the center is
    sqrt(x1 * x2).

    Parameters
    ----------
    boundaries: list[float]
        List of bin boundaries.
    interpolation: str
        "linear" for arithmetic mean, "log" for geometric mean.

    Returns
    -------
    list[float]
        List of bin centers.
    """
    if interpolation == "linear":
        centers = [
            (boundaries[i] + boundaries[i + 1]) / 2
            for i in range(len(boundaries) - 1)
        ]
    elif interpolation == "log":
        centers = [
            math.sqrt(boundaries[i] * boundaries[i + 1])
            for i in range(len(boundaries) - 1)
        ]
    else:
        raise ValueError("interpolation must be 'linear' or 'log'")
    return centers


def centers_to_boundaries(
    centers: list[float], interpolation: str = "linear"
) -> list[float]:
    """
    Convert bin centers to bin boundaries.

    The returned list has length len(centers) - 1, with the first and
    last bins being open-ended.

    To get a closed interval around upper or lower centers, simply add an
    additional center below or above and ignore the resulting values. In
    the case of a distribution, to truly throw out the outliers, you will
    need to extract the desired sub-vector or sub-matrix and re-normalize.

    If interpolation is "linear", the boundary between two centers
    x1 and x2 is (x1 + x2) / 2. If interpolation is "log", the boundary
    is sqrt(x1 * x2).

    Parameters
    ----------
    centers : list[float]
        List of bin centers.
    interpolation : str
        "linear" for arithmetic mean, "log" for geometric mean.

    Returns
    -------
    list[float]
        List of bin boundaries.
    """
    # strangely, this is the same function as boundaries_to_centers:
    return boundaries_to_centers(centers, interpolation)


class Histogram1D:
    """Class for computing one-dimensional histograms.

    Parameters
    ----------
    bin_centers : list of float, optional
        Centers of the histogram bins.
    bin_boundaries : list of float, optional
        boundaries of the histogram bins.
    interpolation : str, optional
        Interpolation method for missing bin_centers or bin_boundaries.
        "linear" to use the average of neighboring values, "log" for
        geometric mean.
    ignore_extrema : bool, optional
        If True, values below the lowest bin edge and above the highest
        bin edge are ignored. If False, they are counted in the first
        and last bins, respectively. Default is False.
    initial_value : float
        The initial bin values are all set to this value (default is 0).
        This avoids a divide-by-a-zero-total problem when normalizing
        bins that are all zero. This can also avoid zero-probability bins
        by giving all bins a non-zero "prior." The divide-by-zero problem
        is avoided in any case: When normalizing and all bins are zero,
        the bin values are left at zero.

    Attributes
    ----------
    bin_boundaries : list of float
        Boundaries of the histogram bins. If ignore_extrema is True,
        bin_boundaries has length len(bin_centers) + 1 and surround
        all bins. If ignore_extrema is False, bin_boundaries has length
        len(bin_centers) - 1 and the first and last bins are open-ended,
        so bin_boundaries are boundaries between bins only.
    bin_centers: list of float
        Centers of the histogram bins (used for plot labels)
    bins : list of float
        (weighted) counts or probability of data points in each bin.
    ignore_extrema : bool
        If True, values outside the bin boundaries are ignored.
    """

    def __init__(
        self,
        bin_centers: Optional[list[float]] = None,
        bin_boundaries: Optional[list[float]] = None,
        interpolation: str = "linear",
        ignore_extrema: bool = False,
        initial_value: float = 0.0,
    ):
        if not bin_centers and not bin_boundaries:
            raise ValueError(
                "Must provide either bin_centers or " "bin_boundaries."
            )
        if not bin_boundaries:
            if ignore_extrema:
                raise ValueError(
                    "When ignore_extrema is True, "
                    "bin_boundaries must be provided."
                )
            centers = cast(list[float], bin_centers)
            bin_boundaries = centers_to_boundaries(centers, interpolation)
        elif bin_centers:  # we have both bin_boundaries and bin_centers
            blen = len(bin_boundaries)
            clen = len(bin_centers)
            if ignore_extrema:
                if blen != clen + 1:
                    raise ValueError(
                        "When ignore_extrema is False, "
                        "len(bin_boundaries) must be len(bin_centers) + 1"
                    )
            elif blen == clen + 1:  # allowed, but we trim the boundaries:
                bin_boundaries = bin_boundaries[1:-1]
            elif blen != clen - 1:
                raise ValueError(
                    "When ignore_extrema is False, "
                    "len(bin_boundaries) must be len(bin_centers) + 1 "
                    "or len(bin_centers) - 1"
                )
        if not bin_centers:
            bin_centers = boundaries_to_centers(bin_boundaries, interpolation)
            if ignore_extrema:
                bin_boundaries = bin_boundaries[1:-1]

        # now, we need len(bin_boundaries) to respect ignore_extrema
        blen = len(bin_boundaries)
        clen = len(bin_centers)
        assert (not ignore_extrema and (blen == clen - 1)) or (
            (ignore_extrema) and (blen == clen + 1)
        )

        self.ignore_extrema = ignore_extrema
        self.bins = [initial_value] * len(bin_centers)
        self.bin_centers = bin_centers
        self.bin_boundaries = bin_boundaries

    def find_bin(self, value: float):
        """
        find the bin index for a given value such that i indexes
        the next boundary above value. If the value is greater or
        equal to the highest boundary, len(bin_boundaries) is returned.
        """
        i = 0  # for the strange case of len(bin_boundaries) == 0
        for i in range(len(self.bin_boundaries)):
            if self.bin_boundaries[i] > value:
                return i
        return len(self.bin_boundaries)

    def add_point(self, data: float, weight: float = 1.0):
        """Record one count or weight update to the histogram
        Parameters
        ----------
        data : float
            value to be recorded in the histogram
        weight : float
            weight to add to the appropriate bin (default is 1.0)

        Returns
        -------
        Optional[int]
            bin number where the data point was recorded or
            None if data was out of bounds
        """
        # prevent a Histogram2D from using this method:
        if isinstance(self.bins[0], list):
            raise ValueError("Histogram2D must use add_point_2d method")
        i = self.find_bin(data)
        if self.ignore_extrema:
            if i == 0 or i == len(self.bins):
                return None  # out of bounds
            else:
                i -= 1  # bin[0] corresponds to bounds[1:2]
        self.bins[i] += weight
        return i

    def normalize(self):
        """
        Convert the histogram into a probability distribution.
        If all bins are zero, the resulting bins remain at zero.
        """
        total = sum(self.bins)
        if total > 0:
            self.bins = [b / total for b in self.bins]


class Histogram2D(Histogram1D):
    """Class for computing two-dimensional histograms.

    Parameters
    ----------
    bin_centers : list of float, optional
        Centers of the histogram bins.
    bin_boundaries : list of float, optional
        boundaries of the histogram bins.
    interpolation : str, optional
        Interpolation method for missing bin_centers or bin_boundaries.
        "linear" to use the average of neighboring values, "log" for
        geometric mean.
    ignore_extrema : bool, optional
        If True, values below the lowest bin edge and above the highest
        bin edge are ignored. If False, they are counted in the first
        and last bins, respectively. Default is False.

    Attributes
    ----------
    bin_boundaries : list of float
        Boundaries of the histogram bins.
    bin_centers: list of float
        Centers of the histogram bins (used for plot labels)
    bins : list of float
        (weighted) counts or probability of data points in each bin.
    ignore_extrema : bool
        If True, values outside the bin boundaries are ignored.
    """

    def __init__(
        self,
        bin_centers: Optional[list[float]] = None,
        bin_boundaries: Optional[list[float]] = None,
        interpolation: str = "linear",
        ignore_extrema: bool = False,
        initial_value: float = 0.0,
    ):
        # Histogram1D takes care of the messy establishment of
        # centers and boundaries, which are the same for 2D:
        super().__init__(
            bin_centers, bin_boundaries, interpolation, ignore_extrema
        )
        # now we just have to fix bins to be 2D:
        self.bins = [
            [initial_value] * len(self.bins) for _ in range(len(self.bins))
        ]

    def add_point_2d(
        self,
        data1: Optional[float],
        data2: float,
        weight: float = 1.0,
        prev: Optional[int] = None,
    ):
        """Record one count or weight update to the histogram

        A typical use is to record consecutive elements of a sequence
        as data1 along with the next element as data2. In this case, data2
        will become data1 in the next call, so the returned bin index for
        data2 can be provided as prev in the next call to avoid re-compmuting
        the bin index for data1.

        To further support this use case, if data1 is None, the histogram
        is not changed, but the bin index for data2 is still computed and
        returned. Thus, you can pass None for data1 and the first element
        as data2 to get things started.

        If the histogram is not updated (because data1 is None or because
        data1 or data2 are out of bounds and ignore_extrema is True),
        None is returned, in which case data1 should be passed as None in
        the next call as if starting a new sequence.

        Parameters
        ----------
        data1 : float
            value for dimension 1 (or None to skip)
        data2 : float
            value for dimension 2
        weight : float
            weight to add to the appropriate bin (default is 1.0)
        prev : Optional(int)
            optional previous bin index for data1; if provided, this
            value is used instead of recomputing the bin index for data1.

        Returns
        -------
        int
            bin number for data2 if data were used to add to
            the histogram, else None (which means the bin must
            be calculated).
        """
        i = None  # index for data1
        if data1 is not None:
            if prev:
                i = prev
            else:
                i = self.find_bin(data1)
                if i == 0 or i == len(self.bins):
                    if self.ignore_extrema:
                        return None  # out of bounds

        j = self.find_bin(data2)  # index for data2
        if j == 0 or j == len(self.bins) + 1:
            if self.ignore_extrema:
                return None

        if i is not None:
            self.bins[i][j] += weight
        return j

    def normalize(self):
        total = 0.0
        for row in self.bins:
            total += sum(row)
        if total > 0:
            self.bins = [[c / total for c in row] for row in self.bins]
