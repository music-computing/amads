"""Calculates the Interpolation Contour of a melody, along with related features, as
implemented in the FANTASTIC toolbox of Müllensiefen (2009) [1]
(features 23–27).
Includes a modified version of the FANTASTIC method that is better suited to short melodies
than the original implementation. This 'AMADS' method defines turning points using reversals,
and is the default method. All features are returned for either method.
"""

__author__ = "David Whyatt"

import numpy as np


class InterpolationContour:
    """Class for calculating and analyzing the interpolated contours of melodies, according to
    Müllensiefen (2009) [1]. This representation was first formalised by Steinbeck (1982)
    [2], and informed a varient of the present implementation in Müllensiefen & Frieler
    (2004) [3].
    An interpolation contour is produced by first identifying turning points in the melody,
    and then interpolating a linear gradient between each turning point. The resulting list
    of values represents the gradient of the melody at evenly spaced points in time.
    """

    def __init__(self, pitches: list[int], times: list[float], method: str = "amads"):
        """Initialize with pitch and time values.

        Parameters
        ----------
        pitches : list[int]
            Pitch values in any numeric format (e.g., MIDI numbers).
        times : list[float]
            Onset times in any consistent, proportional scheme (e.g., seconds, quarter notes, etc.)
        method : str, optional
            Method to use for contour calculation, either "fantastic" or "amads".
            Defaults to "amads".
            The FANTASTIC method is the original implementation, and identifies turning points
            using contour extrema via a series of rules. The AMADS method instead identifies
            reversals for all melody lengths, and is the default method.

        Raises
        ------
        ValueError
            If the `times` and `pitches` parameters are not the same length.
            If method is not "fantastic" or "amads"

        Examples
        --------
        >>> happy_birthday_pitches = [
        ...     60, 60, 62, 60, 65, 64, 60, 60, 62, 60, 67, 65,
        ...     60, 60, 72, 69, 65, 64, 62, 70, 69, 65, 67, 65
        ... ]
        >>> happy_birthday_times = [
        ...     0, 0.75, 1, 2, 3, 4, 6, 6.75, 7, 8, 9, 10,
        ...     12, 12.75, 13, 14, 15, 16, 17, 18, 18.75, 19, 20, 21
        ... ]
        >>> ic = InterpolationContour(
        ...     happy_birthday_pitches,
        ...     happy_birthday_times,
        ...     method="fantastic",
        ... )
        >>> ic.direction_changes
        0.6
        >>> ic.class_label
        'ccbc'
        >>> ic.mean_gradient
        2.702...
        >>> ic.gradient_std
        5.655...
        >>> ic.global_direction
        1

        References
        ----------
        [1] Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology Accessing
        STatistics (In a Corpus): Technical Report v1.5
        [2] W. Steinbeck, Struktur und Ähnlichkeit: Methoden automatisierter
            Melodieanalyse. Bärenreiter, 1982.
        [3] Müllensiefen, D. & Frieler, K. (2004). Cognitive Adequacy in the Measurement
        of Melodic Similarity: Algorithmic vs. Human Judgments
        """
        if len(times) != len(pitches):
            raise ValueError(
                f"Times and pitches must have the same length, got {len(times)} and {len(pitches)}"
            )
        if method not in ["fantastic", "amads"]:
            raise ValueError(
                f"Method must be either 'fantastic' or 'amads', got {method}"
            )

        self.times = times
        self.pitches = pitches
        self.method = method
        self.contour = self.calculate_interpolation_contour(pitches, times, method)

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
        pitches: list[int], times: list[float], method: str = "amads"
    ) -> list[float]:
        """Calculate the interpolation contour representation of a melody [1].

        Returns
        -------
        list[float]
            Array containing the interpolation contour representation
        """
        if method == "fantastic":
            return InterpolationContour._calculate_fantastic_contour(pitches, times)

        return InterpolationContour._calculate_amads_contour(pitches, times)

    @staticmethod
    def _calculate_fantastic_contour(
        pitches: list[int], times: list[float]
    ) -> list[float]:
        """
        Calculate the interpolation contour using the FANTASTIC method.
        Utilises the helper function _is_turning_point_fantastic to identify turning points.
        """
        # Find candidate points
        candidate_points_pitch = [pitches[0]]  # Start with first pitch
        candidate_points_time = [times[0]]  # Start with first time

        # Special case for very short melodies
        if len(pitches) in [3, 4]:
            for i in range(1, len(pitches) - 1):
                if InterpolationContour._is_turning_point_fantastic(pitches, i):
                    candidate_points_pitch.append(pitches[i])
                    candidate_points_time.append(times[i])
        else:
            # For longer melodies
            for i in range(2, len(pitches) - 2):
                if InterpolationContour._is_turning_point_fantastic(pitches, i):
                    candidate_points_pitch.append(pitches[i])
                    candidate_points_time.append(times[i])

        # Initialize turning points with first note
        turning_points_pitch = [pitches[0]]
        turning_points_time = [times[0]]

        # Find turning points
        if len(candidate_points_pitch) > 2:
            for i in range(1, len(pitches) - 1):
                if times[i] in candidate_points_time:
                    if pitches[i - 1] != pitches[i + 1]:
                        turning_points_pitch.append(pitches[i])
                        turning_points_time.append(times[i])

        # Add last note
        turning_points_pitch.append(pitches[-1])
        turning_points_time.append(times[-1])

        # Calculate gradients
        gradients = np.diff(turning_points_pitch) / np.diff(turning_points_time)

        # Calculate durations
        durations = np.diff(turning_points_time)

        # Create weighted gradients vector
        sample_rate = 10  # 10 samples per second
        samples_per_duration = abs(np.round(durations * sample_rate).astype(int))
        interpolation_contour = np.repeat(gradients, samples_per_duration)

        return [float(x) for x in interpolation_contour]

    @staticmethod
    def _remove_repeated_notes(
        pitches: list[int], times: list[float]
    ) -> tuple[list[int], list[float]]:
        """Helper function to remove repeated notes, keeping only the middle occurrence.
        This is used for the AMADS method to produce the interpolated gradient values
        at the middle of a sequence of repeated notes, should there be a reversal
        between the repeated notes.
        """
        unique_pitches, unique_times = [], []
        i = 0
        while i < len(pitches):
            start_idx = i
            while i < len(pitches) - 1 and pitches[i + 1] == pitches[i]:
                i += 1
            mid_idx = start_idx + (i - start_idx) // 2
            unique_pitches.append(pitches[mid_idx])
            unique_times.append(times[mid_idx])
            i += 1
        return unique_pitches, unique_times

    @staticmethod
    def _calculate_amads_contour(pitches: list[int], times: list[float]) -> list[float]:
        """
        Calculate the interpolation contour using the AMADS method.
        Utilises the helper function _remove_repeated_notes.
        """
        reversals_pitches = [pitches[0]]
        reversals_time = [times[0]]

        # Remove repeated notes
        pitches, times = InterpolationContour._remove_repeated_notes(pitches, times)

        # Find reversals
        for i in range(2, len(pitches)):
            if (
                pitches[i] < pitches[i - 1] > pitches[i - 2]
                or pitches[i] > pitches[i - 1] < pitches[i - 2]
            ):
                reversals_pitches.append(pitches[i - 1])
                reversals_time.append(times[i - 1])

        # Add last note
        reversals_pitches.append(pitches[-1])
        reversals_time.append(times[-1])

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
        """Calculate the global direction of the interpolation contour by taking
        the sign of the sum of all contour values.
        Can be invoked for either FANTASTIC or AMADS method.

        Returns
        -------
        int
            1 if sum is positive, 0 if sum is zero, -1 if sum is negative

        Examples
        --------
        Flat overall contour direction (returns the same using FANTASTIC method)
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4])
        >>> ic.global_direction
        0

        Upwards contour direction (returns the same using FANTASTIC method)
        >>> ic = InterpolationContour([60, 62, 64, 65, 67], [0, 1, 2, 3, 4])
        >>> ic.global_direction
        1

        Downwards contour direction (returns the same using FANTASTIC method)
        >>> ic = InterpolationContour([67, 65, 67, 62, 60], [0, 1, 2, 3, 4])
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
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4])
        >>> ic.mean_gradient
        2.0

        FANTASTIC method returns 0.0 for this example
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4], method="fantastic")
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
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4])
        >>> ic.gradient_std
        2.0254...

        FANTASTIC method returns 0.0 for this example
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4], method="fantastic")
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
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4])
        >>> ic.direction_changes
        1.0

        FANTASTIC method returns 0.0 for this example
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4], method="fantastic")
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
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4])
        >>> ic.class_label
        'ddbb'

        FANTASTIC method returns 'cccc' for this example, as though the contour is flat
        >>> ic = InterpolationContour([60, 62, 64, 62, 60], [0, 1, 2, 3, 4], method="fantastic")
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
