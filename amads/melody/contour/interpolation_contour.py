"""Calculates the Interpolation Contour of a melody, along with related features, as
implemented in the FANTASTIC toolbox of Müllensiefen (2009) [1]
(features 23–27).
"""

__author__ = "David Whyatt"

from typing import Optional, Sequence

import numpy as np

from amads.core.basics import Score


class InterpolationContour:
    """Class for calculating and analyzing interpolated contours of melodies.

    As implemented in the FANTASTIC toolbox of Müllensiefen (2009) [1] (as
    features 23–27). This representation was first formalised by Steinbeck
    (1982) [2], and informed a variant of the present implementation in
    Müllensiefen & Frieler (2004) [3].

    Includes a modified version of the FANTASTIC method that is better
    suited to short melodies than the original implementation. This
    'AMADS' method defines turning points using reversals, and is the
    default method. All features are returned for either method.

    An interpolation contour is produced by first identifying turning points
    in the melody, and then interpolating a linear gradient between each
    turning point. The resulting list of values represents the gradient
    of the melody at evenly spaced points in time.

    <small>**Author**: David Whyatt</small>
    """

    def __init__(
        self,
        score: Optional[Score] = None,
        onsets: Optional[Sequence[float]] = None,
        pitches: Optional[Sequence[int]] = None,
        method: str = "amads",
    ):
        """Initialize with pitch and time values.

        Parameters
        ----------
        score : Score, optional, default=None
            If `pitches` and `onsets` are provided, use them. If not and a `score` is use that.
        pitches : list[int]
            Pitch values in any numeric format (e.g., MIDI numbers).
        onsets : list[float]
            Onset onsets in any consistent, proportional scheme (e.g., seconds,
            quarter notes, etc.)
        method : str, optional
            Method to use for contour calculation, either "fantastic" or "amads".
            Defaults to "amads".
            The FANTASTIC method is the original implementation, and identifies
            turning points using contour extrema via a series of rules. The
            AMADS method instead identifies reversals for all melody lengths,
            and is the default method.

        Raises
        ------
        ValueError
            If neither `onsets` and `pitches` or a score parameter are provided.
            If the `onsets` and `pitches` parameters are not the same length.
            If method is not "fantastic" or "amads"

        Examples
        --------
        >>> happy_birthday_pitches = [
        ...     60, 60, 62, 60, 65, 64, 60, 60, 62, 60, 67, 65,
        ...     60, 60, 72, 69, 65, 64, 62, 70, 69, 65, 67, 65
        ... ]
        >>> happy_birthday_onsets = [
        ...     0, 0.75, 1, 2, 3, 4, 6, 6.75, 7, 8, 9, 10,
        ...     12, 12.75, 13, 14, 15, 16, 17, 18, 18.75, 19, 20, 21
        ... ]
        >>> ic = InterpolationContour(
        ...     pitches=happy_birthday_pitches,
        ...     onsets=happy_birthday_onsets,
        ...     method="fantastic",
        ... )
        >>> ic.direction_changes
        0.6
        >>> ic.class_label
        'ccbc'
        >>> round(ic.mean_gradient, 6)
        2.702857
        >>> round(ic.gradient_std, 6)
        5.65564
        >>> ic.global_direction
        1

        References
        ----------
         1. Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology
            Accessing STatistics (In a Corpus): Technical Report v1.5

         2. W. Steinbeck, Struktur und Ähnlichkeit: Methoden automatisierter
            Melodieanalyse. Bärenreiter, 1982.

         3. Müllensiefen, D. & Frieler, K. (2004). Cognitive Adequacy in the
            Measurement of Melodic Similarity: Algorithmic vs. Human Judgments
        """
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
            if not isinstance(score, Score):
                raise TypeError("Score should be a Score object.")

            self.onsets, self.pitches = self.get_onsets_and_pitches(score)

        if method not in ["fantastic", "amads"]:
            raise ValueError(
                f"Method must be either 'fantastic' or 'amads', got {method}"
            )
        self.method = method

        self.contour = self.calculate_interpolation_contour(
            pitches, onsets, method
        )

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

    @staticmethod
    def _is_turning_point_fantastic(pitches: list[int], i: int) -> bool:
        """Helper method to determine if a point is a turning point in FANTASTIC method."""
        return any(
            [
                (pitches[i - 1] < pitches[i] and pitches[i] > pitches[i + 1]),
                (pitches[i - 1] > pitches[i] and pitches[i] < pitches[i + 1]),
                (
                    pitches[i - 1] == pitches[i]
                    and pitches[i - 2] < pitches[i]
                    and pitches[i] > pitches[i + 1]
                ),
                (
                    pitches[i - 1] < pitches[i]
                    and pitches[i] == pitches[i + 1]
                    and pitches[i + 2] > pitches[i]
                ),
                (
                    pitches[i - 1] == pitches[i]
                    and pitches[i - 2] > pitches[i]
                    and pitches[i] < pitches[i + 1]
                ),
                (
                    pitches[i - 1] > pitches[i]
                    and pitches[i] == pitches[i + 1]
                    and pitches[i + 2] < pitches[i]
                ),
            ]
        )

    @staticmethod
    def calculate_interpolation_contour(
        pitches: list[int], onsets: list[float], method: str = "amads"
    ) -> list[float]:
        """Calculate the interpolation contour representation of a melody [1].

        Returns
        -------
        list[float]
            Array containing the interpolation contour representation
        """
        if method == "fantastic":
            return InterpolationContour._calculate_fantastic_contour(
                pitches, onsets
            )

        return InterpolationContour._calculate_amads_contour(pitches, onsets)

    @staticmethod
    def _calculate_fantastic_contour(
        pitches: list[int], onsets: list[float]
    ) -> list[float]:
        """
        Calculate the interpolation contour using the FANTASTIC method.

        Utilises the helper function _is_turning_point_fantastic to identify
        turning points.
        """
        # Find candidate points
        candidate_points_pitch = [pitches[0]]  # Start with first pitch
        candidate_points_time = [onsets[0]]  # Start with first time

        # Special case for very short melodies
        if len(pitches) in [3, 4]:
            for i in range(1, len(pitches) - 1):
                if InterpolationContour._is_turning_point_fantastic(pitches, i):
                    candidate_points_pitch.append(pitches[i])
                    candidate_points_time.append(onsets[i])
        else:
            # For longer melodies
            for i in range(2, len(pitches) - 2):
                if InterpolationContour._is_turning_point_fantastic(pitches, i):
                    candidate_points_pitch.append(pitches[i])
                    candidate_points_time.append(onsets[i])

        # Initialize turning points with first note
        turning_points_pitch = [pitches[0]]
        turning_points_time = [onsets[0]]

        # Find turning points
        if len(candidate_points_pitch) > 2:
            for i in range(1, len(pitches) - 1):
                if onsets[i] in candidate_points_time:
                    if pitches[i - 1] != pitches[i + 1]:
                        turning_points_pitch.append(pitches[i])
                        turning_points_time.append(onsets[i])

        # Add last note
        turning_points_pitch.append(pitches[-1])
        turning_points_time.append(onsets[-1])

        # Calculate gradients
        gradients = np.diff(turning_points_pitch) / np.diff(turning_points_time)

        # Calculate durations
        durations = np.diff(turning_points_time)

        # Create weighted gradients vector
        sample_rate = 10  # 10 samples per second
        samples_per_duration = abs(
            np.round(durations * sample_rate).astype(int)
        )
        interpolation_contour = np.repeat(gradients, samples_per_duration)

        return [float(x) for x in interpolation_contour]

    @staticmethod
    def _remove_repeated_notes(
        pitches: list[int], onsets: list[float]
    ) -> tuple[list[int], list[float]]:
        """Helper function to remove repeated notes, keeping only the middle occurrence.

        This is used for the AMADS method to produce the interpolated gradient values
        at the middle of a sequence of repeated notes, should there be a reversal
        between the repeated notes.
        """
        unique_pitches, unique_onsets = [], []
        i = 0
        while i < len(pitches):
            start_idx = i
            while i < len(pitches) - 1 and pitches[i + 1] == pitches[i]:
                i += 1
            mid_idx = start_idx + (i - start_idx) // 2
            unique_pitches.append(pitches[mid_idx])
            unique_onsets.append(onsets[mid_idx])
            i += 1
        return unique_pitches, unique_onsets

    @staticmethod
    def _calculate_amads_contour(
        pitches: list[int], onsets: list[float]
    ) -> list[float]:
        """
        Calculate the interpolation contour using the AMADS method.

        Utilises the helper function _remove_repeated_notes.
        """
        reversals_pitches = [pitches[0]]
        reversals_time = [onsets[0]]

        # Remove repeated notes
        pitches, onsets = InterpolationContour._remove_repeated_notes(
            pitches, onsets
        )

        # Find reversals
        for i in range(2, len(pitches)):
            if (
                pitches[i] < pitches[i - 1] > pitches[i - 2]
                or pitches[i] > pitches[i - 1] < pitches[i - 2]
            ):
                reversals_pitches.append(pitches[i - 1])
                reversals_time.append(onsets[i - 1])

        # Add last note
        reversals_pitches.append(pitches[-1])
        reversals_time.append(onsets[-1])

        # Calculate gradients
        gradients = np.diff(reversals_pitches) / np.diff(reversals_time)

        # Calculate durations
        durations = np.diff(reversals_time)

        # Create weighted gradients vector
        samples_per_duration = abs(np.round(durations * 10).astype(int))

        # Can't have a contour with less than 2 points
        if len(reversals_pitches) < 2:
            return [0.0]

        # If there are only 2 points, just use the gradient between them
        if len(reversals_pitches) == 2:
            gradient = reversals_pitches[1] - reversals_pitches[0]
            return [float(gradient / (reversals_time[1] - reversals_time[0]))]

        interpolation_contour = np.repeat(gradients, samples_per_duration)
        return [float(x) for x in interpolation_contour]

    @property
    def global_direction(self) -> int:
        """Calculate the global direction of the interpolation contour.

        Takes the sign of the sum of all contour values.
        Can be invoked for either FANTASTIC or AMADS method.

        Returns
        -------
        int
            1 if sum is positive, 0 if sum is zero, -1 if sum is negative

        Examples
        --------
        Flat overall contour direction (returns the same using FANTASTIC method)
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4])
        >>> ic.global_direction
        0

        Upwards contour direction (returns the same using FANTASTIC method)
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 65, 67], onsets=[0, 1, 2, 3, 4])
        >>> ic.global_direction
        1

        Downwards contour direction (returns the same using FANTASTIC method)
        >>> ic = InterpolationContour(pitches=[67, 65, 67, 62, 60], onsets=[0, 1, 2, 3, 4])
        >>> ic.global_direction
        -1
        """
        return int(np.sign(sum(self.contour)))

    @property
    def mean_gradient(self) -> float:
        """Calculate the absolute mean gradient of the interpolation contour.
        Can be invoked for either FANTASTIC or AMADS method.

        Returns
        -------
        float
            Mean of the absolute gradient values

        Examples
        --------
        Steps of 2 semitones per second
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4])
        >>> ic.mean_gradient
        2.0

        FANTASTIC method returns 0.0 for this example
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4], method="fantastic")
        >>> ic.mean_gradient
        0.0
        """
        return float(np.mean(np.abs(self.contour)))

    @property
    def gradient_std(self) -> float:
        """Calculate the standard deviation of the interpolation contour gradients.

        Can be invoked for either FANTASTIC or AMADS method.

        Returns
        -------
        float
            Standard deviation of the gradient values (by default, using Bessel's correction)

        Examples
        --------
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4])
        >>> round(ic.gradient_std, 7)
        2.0254787

        FANTASTIC method returns 0.0 for this example
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4], method="fantastic")
        >>> ic.gradient_std
        0.0
        """
        return float(np.std(self.contour, ddof=1))

    @property
    def direction_changes(self) -> float:
        """Calculate the proportion of interpolated gradient values that consistute
        a change in direction. For instance, a gradient value of
        -0.5 to 0.25 is a change in direction.
        Can be invoked for either FANTASTIC or AMADS method.

        Returns
        -------
        float
            Ratio of the number of changes in contour direction relative to the number
            of different interpolated gradient values

        Examples
        --------
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4])
        >>> ic.direction_changes
        1.0

        FANTASTIC method returns 0.0 for this example
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4], method="fantastic")
        >>> ic.direction_changes
        0.0
        """
        # Convert contour to numpy array for element-wise multiplication
        contour_array = np.array(self.contour)
        # Calculate products of consecutive gradients
        consecutive_products = contour_array[:-1] * contour_array[1:]

        # Get signs of products and count negative ones (direction changes)
        product_signs = np.sign(consecutive_products)
        direction_changes = np.sum(np.abs(product_signs[product_signs == -1]))

        # Count total gradient changes (where consecutive values are different)
        total_changes = np.sum(contour_array[:-1] != contour_array[1:])

        # Avoid division by zero
        if total_changes == 0:
            return 0.0

        return float(direction_changes / total_changes)

    @property
    def class_label(self) -> str:
        """Classify an interpolation contour into gradient categories.

        Can be invoked for either FANTASTIC or AMADS method.

        The contour is sampled at 4 equally spaced points and each gradient is
        normalized to units of pitch change per second
        (expressed in units of semitones per 0.25 seconds.)
        The result is then classified into one of 5 categories:

        - 'a': Strong downward (-2) - normalized gradient <= -1.45
        - 'b': Downward (-1) - normalized gradient between -1.45 and -0.45
        - 'c': Flat (0) - normalized gradient between -0.45 and 0.45
        - 'd': Upward (1) - normalized gradient between 0.45 and 1.45
        - 'e': Strong upward (2) - normalized gradient >= 1.45

        Returns
        -------
        str
            String of length 4 containing letters a-e representing the gradient
            categories at 4 equally spaced points in the contour

        Examples
        --------
        Upwards, then downwards contour
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4])
        >>> ic.class_label
        'ddbb'

        FANTASTIC method returns 'cccc' for this example, as though the contour is flat
        >>> ic = InterpolationContour(pitches=[60, 62, 64, 62, 60], onsets=[0, 1, 2, 3, 4], method="fantastic")
        >>> ic.class_label
        'cccc'
        """
        # Sample the contour at 4 equally spaced points
        # Get 4 equally spaced indices
        n = len(self.contour)
        indices = np.linspace(0, n - 1, 4, dtype=int)

        # Sample the contour at those indices
        sampled_points = [self.contour[i] for i in indices]

        # Normalize the gradients to a norm where value of 1 corresponds to a semitone
        # change in pitch over 0.25 seconds.
        # Given that base pitch and time units are 1 second and 1 semitone respectively,
        # just divide by 4
        norm_gradients = np.array(sampled_points) * 0.25
        classes = ""
        for grad in norm_gradients:
            if grad <= -1.45:
                classes += "a"  # strong down
            elif -1.45 < grad <= -0.45:
                classes += "b"  # down
            elif -0.45 < grad < 0.45:
                classes += "c"  # flat
            elif 0.45 <= grad < 1.45:
                classes += "d"  # up
            else:
                classes += "e"  # strong up

        return classes

    def plot(self, ax=None):
        """
        Plot the melody notes and the interpolation contour gradients.

        Displays two subplots (if ``ax`` is None):

        * **Top**: pitch values at their onset times as a scatter/step plot,
          with all original melody notes connected by lines.
        * **Bottom**: the interpolation contour — the piecewise-constant
          gradient values produced by `calculate_interpolation_contour`,
          plotted as a step function over normalised time (0–1).

        Parameters
        ----------
        ax : array-like of matplotlib.axes.Axes, optional
            A pair of Axes ``[ax_melody, ax_contour]`` to draw on.  If
            ``None``, a new figure with two vertically stacked subplots is
            created with ``figsize=(8, 5)``.

        Returns
        -------
        tuple[matplotlib.axes.Axes, matplotlib.axes.Axes]
            ``(ax_melody, ax_contour)`` — the two axes, suitable for further
            customisation or embedding in a larger figure.

        Raises
        ------
        ImportError
            If matplotlib is not installed.

        Examples
        --------
        >>> ic = InterpolationContour(
        ...     pitches=[60, 62, 64, 62, 60],
        ...     onsets=[0, 1, 2, 3, 4],
        ... )
        >>> ax_melody, ax_contour = ic.plot()
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError as e:
            raise ImportError(
                "matplotlib is required for plotting. "
                "Install it with: pip install matplotlib"
            ) from e

        if ax is None:
            _, (ax_melody, ax_contour) = plt.subplots(
                2, 1, figsize=(8, 5), constrained_layout=True
            )
        else:
            ax_melody, ax_contour = ax

        # Top panel: all melody notes with connecting lines
        ax_melody.plot(
            self.onsets,
            self.pitches,
            color="steelblue",
            linewidth=1.2,
            zorder=2,
        )
        ax_melody.scatter(
            self.onsets,
            self.pitches,
            color="steelblue",
            s=50,
            linewidths=0.8,
            edgecolors="white",
            zorder=3,
            label="Notes",
        )
        ax_melody.set_xlabel("Onset time", fontsize=10)
        ax_melody.set_ylabel("MIDI pitch", fontsize=10)
        ax_melody.set_title("Melody", fontsize=11)
        ax_melody.grid(True, linestyle="--", alpha=0.4)
        ax_melody.spines[["top", "right"]].set_visible(False)

        # Bottom panel: interpolation contour
        contour = self.contour
        # The contour is sampled at a rate of 10 samples per unit time.
        # Build a normalised time axis over [0, 1] for display.
        n = len(contour)
        norm_time = np.linspace(0, 1, n, endpoint=False)

        ax_contour.step(
            norm_time,
            contour,
            where="post",
            color="tomato",
            linewidth=1.8,
            label=f"Interpolation contour ({self.method})",
        )
        ax_contour.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax_contour.set_xlabel("Normalised time", fontsize=10)
        ax_contour.set_ylabel("Gradient (semitones / s)", fontsize=10)
        ax_contour.set_title(
            f"Interpolation contour  "
            f"[direction={self.global_direction:+d}, "
            f"mean={self.mean_gradient:.2f}, "
            f"class={self.class_label}]",
            fontsize=11,
        )
        ax_contour.legend(fontsize=9)
        ax_contour.grid(True, linestyle="--", alpha=0.4)
        ax_contour.spines[["top", "right"]].set_visible(False)

        return ax_melody, ax_contour
