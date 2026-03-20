from typing import Optional, Sequence

import numpy as np

from amads.core.basics import Score

__author__ = "David Whyatt"


class PolynomialContour:
    """A class for computing polynomial contour.

    As described in the FANTASTIC toolbox [1].
    This approach is discussed in detail in Müllensiefen and Wiggins (2011) [2].

    Polynomial Contour is constructed in 3 simple steps:

     - First, the onsets are first centred around the origin of the time axis,
       making a symmetry between the first onset and the last.

     - Then, a polynomial model is fit, seeking to predict the pitch values from
       a least squares regression of the centred onset times.

     - Finally, the best model is selected using Bayes' Information Criterion,
       stepwise and in a backwards direction.

    The final output is the coefficients of the first three non-constant terms,
    i.e. [c1, c2, c3] from p = c0 + c1t + c2t^2 + c3t^3.

    <small>**Author**: David Whyatt</small>

    Attributes
    ----------
    coefficients : list[float]
        The polynomial contour coefficients. Returns the first 3 non-constant
        coefficients [c1, c2, c3] of the final selected polynomial contour
        model. The constant term is not included as per the FANTASTIC
        toolbox specification.

    References
    ----------
     1. Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology
        Accessing STatistics (In a Corpus): Technical Report v1.5
     2. Müllensiefen, D., & Wiggins, G.A. (2011). Polynomial functions as a
        representation of melodic phrase contour.

    Examples
    --------
    Single note melodies return [0.0, 0.0, 0.0] since there is no contour:
    >>> pc = PolynomialContour(onsets=[1.0], pitches=[60])
    >>> pc.coefficients
    [0.0, 0.0, 0.0]

    Real melody examples:
    >>> test_pitches = [62, 64, 65, 67, 64, 60, 62]
    >>> test_case = Score.from_melody(pitches=test_pitches, durations=[1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0]) # duration
    >>> test_case_pc = PolynomialContour(test_case)
    >>> test_case_pc.onsets
    [0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 7.0]

    >>> [round(x, 7) for x in test_case_pc.coefficients]  # Verified against FANTASTIC toolbox
    [-1.5014826, -0.2661533, 0.122057]

    The same result if this data comes from a score or directly.

    >>> test_onsets = [0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 7.0]
    >>> test_case_pc.onsets == test_onsets
    True

    >>> test_pitches = [62, 64, 65, 67, 64, 60, 62]
    >>> test_2 = PolynomialContour(onsets=test_onsets, pitches=test_pitches)
    >>> test_2.onsets == test_onsets
    True

    >>> [round(x, 7) for x in test_2.coefficients]  # Verified against FANTASTIC toolbox
    [-1.5014826, -0.2661533, 0.122057]

    >>> twinkle = Score.from_melody([60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60],
    ... [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0])
    >>> pc3 = PolynomialContour(twinkle)
    >>> [round(x, 7) for x in pc3.coefficients]  # Verified against FANTASTIC toolbox
    [-0.9535562, 0.2120971, 0.0]
    """

    def __init__(
        self,
        score: Optional[Score] = None,
        onsets: Optional[Sequence[float]] = None,
        pitches: Optional[Sequence[int]] = None,
    ):
        none_checks = (onsets is not None, pitches is not None)
        if any(none_checks) and not all(none_checks):
            raise ValueError(
                "onsets and pitches must be provided together, not one without the other."
            )

        if all(none_checks):
            if len(onsets) != len(pitches):
                raise ValueError(
                    f"onsets and pitches must have the same length, "
                    f"got {len(onsets)} and {len(pitches)}."
                )
            self.onsets = list(onsets)
            self.pitches = list(pitches)
        else:
            if score is None:
                raise ValueError(
                    "Provide either a Score or both onsets and pitches."
                )
            self.onsets, self.pitches = self.get_onsets_and_pitches(score)

        self.coefficients = self.calculate_coefficients(
            self.onsets, self.pitches
        )

    def calculate_coefficients(
        self, onsets: list[float], pitches: list[int]
    ) -> list[float]:
        """Calculate polynomial contour coefficients for the melody.
        Main method for the PolynomialContour class.

        Parameters
        ----------
        onsets : list[float]
            List of onset times from the score
        pitches : list[int]
            List of pitch values from the score

        Returns
        -------
        list[float]
            First 3 coefficients [c1, c2, c3] of the polynomial contour, with zeros
            padded if needed. For melodies with fewer than 2 notes, returns [0.0, 0.0, 0.0]
            since there is no meaningful contour to analyze.
        """
        if len(onsets) <= 1:
            return [0.0, 0.0, 0.0]

        # Center onset times
        centered_onsets = self.center_onset_times(onsets)

        # Calculate polynomial degree
        m = len(onsets) // 2

        # Select best model using BIC
        return self.select_model(centered_onsets, pitches, m)

    def get_onsets_and_pitches(
        self, score: Score
    ) -> tuple[list[float], list[int]]:
        """Extract onset times and pitches from a Score object.

        Parameters
        ----------
        score : Score
            The Score object to extract data from

        Returns
        -------
        tuple[list[float], list[int]]
            A tuple containing (onset_times, pitch_values)
        """
        notes = score.get_sorted_notes()
        return [note.onset for note in notes], [note.key_num for note in notes]

    def center_onset_times(self, onsets: list[float]) -> list[float]:
        """Center onset times around their midpoint. This produces a symmetric axis
        of onset times, which is used later to fit the polynomial.

        For single-note melodies, returns [0.0] since there is no meaningful contour
        to analyze.

        Parameters
        ----------
        onsets : list[float]
            List of onset times to center

        Returns
        -------
        list[float]
            List of centered onset times. Returns [0.0] for single-note melodies.
        """
        if len(onsets) <= 1:
            return [0.0] * len(onsets)

        # Calculate midpoint using first and last onset times
        midpoint = (onsets[0] + onsets[-1]) / 2
        return [time - midpoint for time in onsets]

    def fit_polynomial(
        self, centered_onsets: list[float], pitches: list[int], m: int
    ) -> list[float]:
        """
        Fit a polynomial model to the melody contour using least squares regression.

        The polynomial has the form:
        p = c0 + c1*t + c2*t^2 + ... + cm*t^m

        where m = n // 2 (n = number of notes) and t are centered onset times.

        Parameters
        ----------
        centered_onsets : list[float]
            List of centered onset times
        pitches : list[int]
            List of pitch values
        m : int
            Maximum polynomial degree to use

        Returns
        -------
        list[float]
            The coefficients [c0, c1, ..., cm] of the fitted polynomial
        """

        n = len(pitches)
        if n <= 1:
            return [float(pitches[0]) if n == 1 else 0.0]

        # Create predictor matrix X where each column is t^i
        x = np.array(
            [[t**i for i in range(m + 1)] for t in centered_onsets], dtype=float
        )
        y = np.array(pitches, dtype=float)

        # Use numpy's least squares solver
        coeffs = np.linalg.lstsq(x, y, rcond=None)[0]

        return coeffs.tolist()

    def select_model(
        self, centered_onsets: list[float], pitches: list[int], m: int
    ) -> list[float]:
        """Select the best polynomial model using BIC in an exhaustive search
        over all subsets of polynomial terms.

        Tests all 2^(m+1) - 1 combinations of polynomial terms and selects
        the one with the best (lowest) BIC. The max degree is m = n // 2.

        Note: the search space grows as O(2^m).
        This is fine for shot melodies (up to c.30 notes, m <= 15).
        Longer melodies will be slow and need a review of this method for performance.

        Parameters
        ----------
        centered_onsets : list[float]
            List of centered onset times
        pitches : list[int]
            List of pitch values
        m : int
            Maximum polynomial degree to consider

        Returns
        -------
        list[float]
            The coefficients [c1, c2, c3] of the selected polynomial model,
            padded with zeros if the selected degree is less than 3.
        """
        max_degree = m
        pitches_array = np.array(pitches, dtype=float)
        x_full = np.array(
            [[t**i for i in range(max_degree + 1)] for t in centered_onsets]
        )

        # Start with maximum degree model
        best_fit = self.fit_polynomial(centered_onsets, pitches, m)
        # Pad to at least degree-3 so indexing [1],[2],[3] is always safe
        best_coeffs = np.zeros(max(max_degree + 1, 4))
        best_coeffs[: len(best_fit)] = best_fit
        best_bic = self._calculate_bic(
            best_coeffs[: max_degree + 1], x_full, pitches_array
        )

        for i in range(1, 2 ** (max_degree + 1)):
            binary = format(i, f"0{max_degree + 1}b")
            degrees = [j for j in range(1, max_degree + 1) if binary[j] == "1"]

            if not degrees:
                continue

            x = np.ones((len(centered_onsets), len(degrees) + 1))
            for j, degree in enumerate(degrees):
                x[:, j + 1] = [t**degree for t in centered_onsets]

            coeffs = np.linalg.lstsq(x, pitches_array, rcond=None)[0]

            # Build a full coefficient array (padded to at least degree 3)
            test_coeffs = np.zeros(max(max_degree + 1, 4))
            test_coeffs[0] = coeffs[0]
            for j, degree in enumerate(degrees):
                test_coeffs[degree] = coeffs[j + 1]

            bic = self._calculate_bic(
                test_coeffs[: max_degree + 1], x_full, pitches_array
            )

            if bic < best_bic:
                best_coeffs = test_coeffs
                best_bic = bic

        return [
            best_coeffs[1].item(),  # convert to native float
            best_coeffs[2].item(),
            best_coeffs[3].item(),
        ]

    def _calculate_bic(
        self, coeffs: np.ndarray, x: np.ndarray, y: np.ndarray
    ) -> float:
        """Calculate BIC for a set of coefficients.

        Emulates the FANTASTIC toolbox implementation, which uses stepAIC from
        the MASS package in R. Only non-zero coefficients are counted as
        parameters.

        If the max value is 0, then a small epsilon is added to RSS.
        We do this before taking the log to guard against
        the case of a perfect fit (RSS = 0 → log(0) = -inf).

        Parameters
        ----------
        coeffs : np.ndarray
            Coefficient array (length must match x.shape[1])
        x : np.ndarray
            Predictor matrix
        y : np.ndarray
            Response vector

        Returns
        -------
        float
            BIC value
        """
        predictions = np.dot(x, coeffs)
        residuals = predictions - y
        rss = np.sum(residuals**2)
        rss = max(rss, 1e-10)  # guard against log(0) on perfect fits
        n = len(y)

        # Count only non-zero coefficients as parameters
        n_params = np.sum(np.abs(coeffs) > 1e-10)

        return n * np.log(rss / n) + n_params * np.log(n)

    def plot(self, ax=None):
        """Plot the melody contour and the fitted polynomial curve.

        Displays pitch values at their centered onset times (scatter) with the
        selected polynomial fit overlaid (line). The y-axis is labelled with
        note names derived from the MIDI pitch numbers.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes to draw on. If None, a new figure and axes are created
            with ``figsize=(8, 4)``.

        Returns
        -------
        matplotlib.axes.Axes
            The axes containing the plot, suitable for further customisation
            or embedding in a larger figure.

        Raises
        ------
        ImportError
            If matplotlib is not installed.

        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.ticker as ticker
        except ImportError as e:
            raise ImportError(
                "matplotlib is required for plotting. "
                "Install it with: pip install matplotlib"
            ) from e

        onsets = self.onsets
        pitches = self.pitches
        centered_onsets = self.center_onset_times(onsets)

        t = np.array(centered_onsets)
        c1, c2, c3 = self.coefficients

        # Recover the constant term c0 (not stored per FANTASTIC spec) as the
        # mean of the residuals after subtracting the known polynomial terms.
        poly_terms = c1 * t + c2 * t**2 + c3 * t**3
        c0 = float(np.mean(np.array(pitches, dtype=float) - poly_terms))

        t_smooth = np.linspace(t[0], t[-1], 300) if len(t) > 1 else t.copy()
        fit_curve = c0 + c1 * t_smooth + c2 * t_smooth**2 + c3 * t_smooth**3

        if ax is None:
            _, ax = plt.subplots(figsize=(8, 4))

        ax.scatter(
            centered_onsets,
            pitches,
            zorder=3,
            label="Notes",
            color="steelblue",
            s=60,
            linewidths=0.8,
            edgecolors="white",
        )
        ax.plot(
            t_smooth,
            fit_curve,
            color="tomato",
            linewidth=2,
            label=f"Contour  [c₁={c1:.3f}, c₂={c2:.3f}, c₃={c3:.3f}]",
            zorder=2,
        )

        def _midi_to_name(midi: int) -> str:
            names = [
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
            ]
            return f"{names[midi % 12]}{midi // 12 - 1}"

        unique_pitches = sorted(set(pitches))
        ax.set_yticks(unique_pitches)
        ax.set_yticklabels(
            [_midi_to_name(p) for p in unique_pitches], fontsize=9
        )

        ax.xaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _: f"{x:+.1f}")
        )
        ax.set_xlabel("Centered onset time (beats)", fontsize=10)
        ax.set_ylabel("Pitch", fontsize=10)
        ax.set_title("Polynomial contour", fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)

        return ax
