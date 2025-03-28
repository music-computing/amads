import numpy as np

from amads.core.basics import Note, Score


class PolynomialContour:
    """A class for computing polynomial contour, as described in the FANTASTIC toolbox [1].
    This approach is discussed in detail in Müllensiefen and Wiggins (2009) [2].

    Polynomial Contour is constructed in 3 simple steps:
    First, the onsets are first centred around the origin of the time axis,
    making a symmetry between the first onset and the last.
    Then, a polynomial model is fit, seeking to predict the pitch values from
    a least squares regression of the centred onset times.
    Finally, the best model is selected using Bayes' Information Criterion,
    stepwise and in a backwards direction.

    The final output of this is the coefficients of the first three non-constant terms,
    i.e. [c1, c2, c3] from p = c0 + c1t + c2t^2 + c3t^3.

    Attributes
    ----------
    score : Score
        The score object containing the melody to analyze.
    coefficients : list[float]
        The polynomial contour coefficients. Returns the first 3 non-constant coefficients
        [c1, c2, c3] of the polynomial contour, with zeros padded if needed. The constant
        term is not included as per the FANTASTIC toolbox specification.

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

    >>> single_note = Score.from_melody([60], [1.0])
    >>> pc3 = PolynomialContour(single_note)
    >>> pc3.coefficients  # For single notes, all coefficients are 0 as there is no contour
    [0.0000000, 0.0000000, 0.0000000]
    """

    def __init__(self, score: Score):
        """Initialize the polynomial contour using a Score object and calculate
        the Polynomial Contour coefficients. Only the first three non-constant coefficients
        are returned, as the constant term is not used in the FANTASTIC toolbox. It is
        believed that the first three polynomial coefficients capture enough variation in
        the contour to be useful.

        Parameters
        ----------
        score : Score
            The score object containing the melody to analyze.
        """
        onsets, pitches = self.get_onsets_and_pitches(score)
        self.coefficients = self.calculate_coefficients(onsets, pitches)

    def calculate_coefficients(
        self, onsets: list[float], pitches: list[int]
    ) -> list[float]:
        """Calculate polynomial contour coefficients for the melody.

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

        # Fit the model
        coefficients = self.fit_polynomial(centered_onsets, pitches)

        # Select best model using BIC
        coefficients = self.select_model(centered_onsets, pitches)

        # Keep only first 3 non-constant coefficients, padded with zeros if needed
        coeffs_no_constant = coefficients[1:]  # Skip constant term (c0)
        coefficients = (
            list(coeffs_no_constant[:3])
            if len(coeffs_no_constant) >= 3
            else list(coeffs_no_constant) + [0.0] * (3 - len(coeffs_no_constant))
        )
        return coefficients

    def get_onsets_and_pitches(self, score: Score) -> tuple[list[float], list[int]]:
        """Get the onset times and pitches from the score.

        Parameters
        ----------
        score : Score
            The Score object for which pitches and onsets are to be extracted.

        Returns
        -------
        tuple[list[float], list[int]]
            A tuple containing two lists: the first is a list of onset times, and the second
            is a list of pitch values.
        """
        flattened_score = score.flatten(collapse=True)
        notes = list(flattened_score.find_all(Note))
        onsets = [note.onset for note in notes]
        pitches = [note.keynum for note in notes]
        return onsets, pitches

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
            List of centered onset times
        """
        if len(onsets) <= 1:
            return [0.0] * len(onsets)

        # Calculate midpoint using first and last onset times
        midpoint = (onsets[0] + onsets[-1]) / 2
        # Subtract midpoint from each onset time
        centered_onsets = [time - midpoint for time in onsets]
        return centered_onsets

    def fit_polynomial(
        self, centered_onsets: list[float], pitches: list[int]
    ) -> list[float]:
        """Fit a polynomial model to the melody contour using QR decomposition.

        The polynomial is of the form:
        p = c0 + c1*t + c2*t^2 + ... + cm*t^m

        where m = floor(n/2), n is number of notes, and t are centered onset times.
        The coefficients c are found using QR decomposition and least squares regression.

        Parameters
        ----------
        centered_onsets : list[float]
            List of centered onset times
        pitches : list[int]
            List of pitch values

        Returns
        -------
        list[float]
            The coefficients [c0, c1, ..., cm] of the fitted polynomial
        """
        # Calculate polynomial degree m = floor(n/2)
        n = len(pitches)
        if n <= 1:
            return [float(pitches[0]) if n == 1 else 0.0]

        m = n // 2

        # Create predictor matrix X where each column is t^i
        x = np.array(
            [[t**i for i in range(m + 1)] for t in centered_onsets], dtype=float
        )
        y = np.array(pitches, dtype=float)

        # Use numpy's least squares solver
        coeffs = np.linalg.lstsq(x, y, rcond=None)[0]

        return coeffs.tolist()

    def select_model(
        self, centered_onsets: list[float], pitches: list[int]
    ) -> list[float]:
        """Select the best polynomial model using BIC in a step-wise backwards fashion.
        Tests polynomials of decreasing degree and selects the one with the best BIC.

        Parameters
        ----------
        centered_onsets : list[float]
            List of centered onset times
        pitches : list[int]
            List of pitch values

        Returns
        -------
        list[float]
            Coefficients of the selected polynomial model
        """
        n = len(pitches)
        max_degree = n // 2  # Use same degree as fit_polynomial

        # Convert to numpy arrays once
        pitches_array = np.array(pitches, dtype=float)
        x_full = np.array(
            [[t**i for i in range(max_degree + 1)] for t in centered_onsets]
        )

        # Start with maximum degree model
        best_fit = self.fit_polynomial(centered_onsets, pitches)
        best_coeffs = np.array(best_fit)  # Convert to numpy array for calculations
        best_bic = self._calculate_bic(best_coeffs, x_full, pitches_array)

        # Try models of decreasing degree
        for degree in range(max_degree - 1, -1, -1):
            # Create design matrix for this degree
            x = np.array([[t**i for i in range(degree + 1)] for t in centered_onsets])

            # Fit model of this degree using all data points
            coeffs = np.linalg.lstsq(x, pitches_array, rcond=None)[0]

            # Pad with zeros to match full model size for BIC calculation
            test_coeffs = np.pad(coeffs, (0, max_degree + 1 - len(coeffs)), "constant")

            # Calculate BIC
            bic = self._calculate_bic(test_coeffs, x_full, pitches_array)

            # Keep simpler model if BIC improves
            if bic < best_bic:
                best_coeffs = test_coeffs
                best_bic = bic
        return best_coeffs.tolist()  # Convert numpy array to list

    def _calculate_bic(
        self, coeffs: list[float], x: np.ndarray, y: np.ndarray
    ) -> float:
        """Helper method to calculate BIC for a set of coefficients

        Parameters
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
        return [
            sum(c * (t**i) for i, c in enumerate(self.coefficients))
            for t in centered_onsets
        ]
