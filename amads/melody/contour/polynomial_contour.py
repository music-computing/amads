import numpy as np

from amads.core.basics import Note, Score


class PolynomialContour:
    """A class for computing polynomial contour, as described in the FANTASTIC toolbox [1].
    This approach is discussed in detail in Müllensiefen and Wiggins (2009) [2].

    Attributes
    ----------
    score : Score
        The score object containing the melody to analyze.
    _coefficients : list[float]
        The coefficients of the polynomial contour. This is a private attribute and should
        not be accessed directly. Instead, use the `coefficients` property.

    References
        ----------
        [1] Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology Accessing
        STatistics (In a Corpus): Technical Report v1.5
        [2] Müllensiefen, D., & Wiggins, G. A. (2009). Polynomial functions as a representation of
        melodic phrase contour

    Examples
    --------
    >>> the_lick = Score.from_melody([62, 64, 65, 67, 64, 60, 62], [1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0])
    >>> pc = PolynomialContour(the_lick)
    >>> pc.coefficients  # this value is confirmed by the FANTASTIC toolbox
    [-1.5014826, -0.2661533, 0.1220570]

    >>> twinkle_twinkle = Score.from_melody([60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60],
    ... [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0])
    >>> pc2 = PolynomialContour(twinkle_twinkle)
    >>> pc2.coefficients # there is a small mismatch with the FANTASTIC toolbox - TODO: investigate
    [-0.9535562, 0.2120971, 0.0000000]
    """

    def __init__(self, score: Score):
        self.score = score
        self._coefficients = None

    @property
    def coefficients(self) -> list[float]:
        """Get the polynomial contour coefficients. Only the three non-constant coefficients
        are returned, as the constant term is not used in the FANTASTIC toolbox. It is
        believed that the first three polynomial coefficients capture enough variation in
        the contour to be useful.

        Returns
        -------
        list[float]
            First 3 coefficients [c1, c2, c3] of the polynomial contour. If the polynomial
            has fewer than 3 coefficients, the remaining values are padded with 0.0.
        """
        if self._coefficients is None:
            self._calculate_coefficients()
        return self._coefficients

    def _calculate_coefficients(self) -> None:
        """Helper method to calculate polynomial contour coefficients for the melody."""
        # Extract onset times and pitches
        flattened_score = self.score.flatten(collapse=True)
        notes = list(flattened_score.find_all(Note))
        onset_times = [note.onset for note in notes]
        pitches = [note.keynum for note in notes]

        # Center onset times
        centered_onsets = self.center_onset_times(onset_times)

        # Calculate max degree
        n = len(notes)
        max_degree = n // 2  # floor(n/2) as specified in FANTASTIC toolbox

        # Initialize coefficients and fit model
        self._coefficients = [0.0] * (max_degree + 1)
        self.fit_polynomial(centered_onsets, pitches)

        # Select best model using BIC
        self._coefficients = self.select_model(centered_onsets, pitches)

        # Keep only first 3 non-constant coefficients, padded with zeros if needed
        coeffs_no_constant = self._coefficients[1:]  # Skip constant term (c0)
        self._coefficients = (
            list(coeffs_no_constant[:3])
            if len(coeffs_no_constant) >= 3
            else list(coeffs_no_constant) + [0.0] * (3 - len(coeffs_no_constant))
        )

        # Apply precise rounding to match FANTASTIC's output format (7 decimal places)
        self._coefficients = [round(c, 7) for c in self._coefficients]

    def center_onset_times(self, onset_times: list[float]) -> list[float]:
        """Center onset times around their midpoint. This produces a symmetric axis
        of onset times, which is used later to fit the polynomial.

        Parameters
        ----------
        onset_times : list[float]
            List of onset times to center

        Returns
        -------
        list[float]
            List of centered onset times
        """
        # Calculate midpoint using first and last onset times
        midpoint = (onset_times[0] + onset_times[-1]) / 2
        # Subtract midpoint from each onset time
        centered_onsets = [time - midpoint for time in onset_times]
        return centered_onsets

    def fit_polynomial(self, centered_onsets: list[float], pitches: list[int]) -> None:
        """Fit a polynomial model to the melody contour.

        The polynomial is of the form:
        p = c0 + c1*t + c2*t^2 + ... + cm*t^m

        where m = floor(n/2), n is number of notes, and t are centered onset times.
        The coefficients c are found using least squares regression.

        Parameters
        ----------
        centered_onsets : list[float]
            List of centered onset times
        pitches : list[int]
            List of pitch values
        """
        # Calculate polynomial degree m = floor(n/2)
        n = len(pitches)
        m = n // 2

        # Create predictor matrix X where each column is t^i
        x = []
        for t in centered_onsets:
            row = [t**i for i in range(m + 1)]
            x.append(row)

        # Convert to numpy arrays for lstsq
        x = np.array(x, dtype=float)
        y = np.array(pitches, dtype=float)

        # Use numpy's least squares solver to find coefficients
        coeffs = np.linalg.lstsq(x, y, rcond=None)[0]

        # Store coefficients
        self._coefficients = coeffs.tolist()

    def select_model(
        self, centered_onsets: list[float], pitches: list[int]
    ) -> list[float]:
        """Select the best polynomial model using BIC in a step-wise backwards fashion.

        Args
        ----------
        centered_onsets : list[float]
            List of centered onset times
        pitches : list[int]
            List of pitch values

        Returns
        -------
        list[float]
            Coefficients of the selected polynomial model, with non-selected components set to 0
        """
        n = len(pitches)
        max_degree = n // 2  # Use same degree as fit_polynomial

        # Start with full model
        self.fit_polynomial(centered_onsets, pitches)
        best_coeffs = self._coefficients.copy()

        # Convert to numpy arrays
        pitches = np.array(pitches, dtype=float)
        x = np.array([[t**i for i in range(max_degree + 1)] for t in centered_onsets])

        # Calculate BIC for full model
        # full_bic = self._calculate_bic(best_coeffs, x, pitches)

        # Try removing each coefficient in turn
        for i in range(max_degree + 1):
            # Create model without coefficient i
            test_coeffs = best_coeffs.copy()
            test_coeffs[i] = 0

            # Calculate predictions and BIC
            predictions = np.dot(x, test_coeffs)
            residuals = predictions - pitches
            rss = np.sum(residuals**2)
            n_params = sum(1 for c in test_coeffs if c != 0)
            bic = n * np.log(rss / n) + n_params * np.log(n)

            # Keep simpler model if BIC improves
            if bic < self._calculate_bic(best_coeffs, x, pitches):
                best_coeffs = test_coeffs

        return best_coeffs

    def _calculate_bic(
        self, coeffs: list[float], x: np.ndarray, y: np.ndarray
    ) -> float:
        """Helper method to calculate BIC for a set of coefficients

        Args
        ----------
        coeffs : list[float]
            List of coefficients
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
        n = len(y)
        n_params = sum(1 for c in coeffs if c != 0)
        return n * np.log(rss / n) + n_params * np.log(n)

    def predict(self, centered_onsets: list[float]) -> list[float]:
        """Evaluate the polynomial at given centered onset times.

        Parameters
        ----------
        centered_onsets : list[float]
            List of centered onset times to evaluate at

        Returns
        -------
        list[float]
            Predicted pitch values
        """
        predictions = []
        for t in centered_onsets:
            # Start with constant term (c0)
            pred = self._coefficients[0]
            # Add polynomial terms
            for i, c in enumerate(self._coefficients[1:], 1):
                pred += c * (t**i)
            predictions.append(pred)
        return predictions
