"""Calculates the Step Contour of a melody, along with related features, as implemented
in the FANTASTIC toolbox of Müllensiefen (2009) [1].

Examples
--------
>>> pitches = [60, 62, 64, 65, 67]  # C4, D4, E4, F4, G4
>>> durations = [1.0, 1.0, 1.0, 1.0, 1.0]
>>> sc = StepContour(pitches, durations)
>>> sc.contour[:8]  # First 8 values of 64-length contour
[60, 60, 60, 60, 60, 60, 60, 60]
>>> sc.global_variation  # Standard deviation of contour
2.3974...
>>> sc.global_direction  # Correlation with ascending line
0.9746...
>>> sc.local_variation  # Average absolute difference between adjacent values
0.1111...
"""

__author__ = "David Whyatt"

import numpy as np


class StepContour:
    """Class for calculating and analyzing step contours of melodies.

    Examples
    --------
    >>> pitches = [60, 64, 67]  # C4, E4, G4
    >>> durations = [2.0, 1.0, 1.0]
    >>> sc = StepContour(pitches, durations)
    >>> len(sc.contour)  # Default length is 64
    64
    """

    _step_contour_length = 64

    def __init__(
        self,
        pitches: list[int],
        durations: list[float],
        step_contour_length: int = _step_contour_length
    ):
        """Initialize StepContour with melody data.

        Parameters
        ----------
        pitches : list[int]
            List of pitch values
        durations : list[float]
            List of duration values measured in tatums
        step_contour_length : int, optional
            Length of the output step contour vector (default is 64)

        References
        ----------
        [1] Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology Accessing
        STatistics (In a Corpus): Technical Report v1.5

        Examples
        --------
        >>> sc = StepContour([60, 62], [1.0, 1.0], step_contour_length=4)
        >>> sc.contour
        [60, 60, 62, 62]
        """
        if len(pitches) != len(durations):
            raise ValueError(
                f"The length of pitches (currently {len(pitches)}) must be equal to "
                f"the length of durations (currently {len(durations)})"
            )

        self._step_contour_length = step_contour_length
        self._contour = self._calculate_contour(pitches, durations)

    def _normalize_durations(self, durations: list[float]) -> list[float]:
        """Helper function to normalize note durations to fit within 4 bars of 4/4 time
        (64 tatums total).

        Parameters
        ----------
        durations : list[float]
            List of duration values measured in tatums

        Returns
        -------
        list[float]
            List of normalized duration values

        Examples
        --------
        >>> sc = StepContour([60], [1.0])
        >>> sc._normalize_durations([2.0, 2.0])
        [32.0, 32.0]
        """
        total_duration = sum(durations)
        if total_duration == 0:
            return durations

        normalized = [
            self._step_contour_length * (duration / total_duration)
            for duration in durations
        ]
        return normalized

    def _expand_to_vector(
        self,
        pitches: list[int],
        normalized_durations: list[float]
    ) -> list[int]:
        """Helper function to create a vector of length step_contour_length by repeating
        each pitch value proportionally to its normalized duration.

        Parameters
        ----------
        pitches : list[int]
            List of pitch values
        normalized_durations : list[float]
            List of normalized duration values (should sum to step_contour_length)

        Returns
        -------
        list[int]
            List of length step_contour_length containing repeated pitch values

        Examples
        --------
        >>> sc = StepContour([60], [1.0], step_contour_length=4)
        >>> sc._expand_to_vector([60, 62], [2.0, 2.0])
        [60, 60, 62, 62]
        """
        result = []
        for pitch, duration in zip(pitches, normalized_durations):
            repetitions = round(duration)
            result.extend([pitch] * repetitions)

        if len(result) > self._step_contour_length:
            result = result[:self._step_contour_length]
        elif len(result) < self._step_contour_length:
            result.extend([result[-1]] * (self._step_contour_length - len(result)))

        return result

    def _calculate_contour(
        self,
        pitches: list[int],
        durations: list[float]
    ) -> list[int]:
        """Calculate the step contour from input pitches and durations.

        Examples
        --------
        >>> sc = StepContour([60, 62], [1.0, 1.0], step_contour_length=4)
        >>> sc._calculate_contour([60, 62], [1.0, 1.0])
        [60, 60, 62, 62]
        """
        normalized_durations = self._normalize_durations(durations)
        return self._expand_to_vector(pitches, normalized_durations)

    @property
    def contour(self) -> list[int]:
        """Get the step contour vector.

        Examples
        --------
        >>> sc = StepContour([60, 62], [1.0, 1.0], step_contour_length=4)
        >>> sc.contour
        [60, 60, 62, 62]
        """
        return self._contour

    @property
    def global_variation(self) -> float:
        """Calculate the global variation of the step contour.

        Returns
        -------
        float
            Float value representing the global variation of the step contour

        Examples
        --------
        >>> sc = StepContour([60, 62, 64], [1.0, 1.0, 1.0])
        >>> round(sc.global_variation, 2)
        1.64
        """
        return float(np.nanstd(self._contour))

    @property
    def global_direction(self) -> float:
        """Calculate the global direction of the step contour.

        Returns
        -------
        float
            Float value representing the global direction of the step contour
            Returns 0.0 if the contour is flat

        Examples
        --------
        >>> sc = StepContour([60, 62, 64], [1.0, 1.0, 1.0])
        >>> round(sc.global_direction, 3)
        0.943
        """
        if len(set(self._contour)) == 1:
            return 0.0

        try:
            corr = np.corrcoef(
                self._contour,
                np.arange(self._step_contour_length)
            )[0, 1]
            return float(corr)
        except Exception:
            return None

    @property
    def local_variation(self) -> float:
        """Calculate the local variation of the step contour.

        Returns
        -------
        float
            Float value representing the local variation of the step contour

        Examples
        --------
        >>> sc = StepContour([60, 62, 64], [1.0, 1.0, 1.0])
        >>> sc.local_variation
        0.06349206349206349
        """
        pairs = list(zip(self._contour, self._contour[1:]))
        local_variation = sum(abs(c2 - c1) for c1, c2 in pairs) / len(pairs)
        return local_variation
