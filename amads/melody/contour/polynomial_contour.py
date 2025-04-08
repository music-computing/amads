import numpy as np

from amads.core.basics import Note, Score


class PolynomialContour:
    """A class for computing polynomial contour, as described in the FANTASTIC toolbox [1].
    This approach is discussed in detail in Müllensiefen and Wiggins (2011) [2].

    Polynomial Contour is constructed in 3 simple steps:
    First, the onsets are first centred around the origin of the time axis,
    making a symmetry between the first onset and the last.
    Then, a polynomial model is fit, seeking to predict the pitch values from
    a least squares regression of the centred onset times.
    Finally, the best model is selected using Bayes' Information Criterion,
    stepwise and in a backwards direction.

    The final output is the coefficients of the first three non-constant terms,
    i.e. [c1, c2, c3] from p = c0 + c1t + c2t^2 + c3t^3.

    Attributes
    ----------
    score : Score
        The score object containing the melody to analyze.
    coefficients : list[float]
        The polynomial contour coefficients. Returns the first 3 non-constant coefficients
        [c1, c2, c3] of the final selected polynomial contour model.
        The constant term is not included as per the FANTASTIC toolbox specification.

    References
    ----------
    [1] Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology Accessing
    STatistics (In a Corpus): Technical Report v1.5
    [2] Müllensiefen, D., & Wiggins, G.A. (2011). Polynomial functions as a
    representation of melodic phrase contour.

    Examples
    --------
    Single note melodies return [0.0, 0.0, 0.0] since there is no contour:
    >>> single_note = Score.from_melody([60], [1.0])
    >>> pc = PolynomialContour(single_note)
    >>> pc.coefficients
    [0.0, 0.0, 0.0]

    Real melody examples:
    >>> the_lick = Score.from_melody([62, 64, 65, 67, 64, 60, 62],
    ... [1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0])
    >>> pc2 = PolynomialContour(the_lick)
    >>> pc2.coefficients  # Verified against FANTASTIC toolbox
    [-1.5014826, -0.2661533, 0.1220570]

    >>> twinkle = Score.from_melody([60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60],
    ... [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0])
    >>> pc3 = PolynomialContour(twinkle)
    >>> pc3.coefficients  # Verified against FANTASTIC toolbox
    [-0.9535562, 0.2120971, 0.0000000]
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
        coefficients = self.select_model(centered_onsets, pitches, m)
        return coefficients

    def get_onsets_and_pitches(self, score: Score) -> tuple[list[float], list[int]]:
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
        flattened_score = score.flatten(collapse=True)
        notes = list(flattened_score.find_all(Note))
        return [note.onset for note in notes], [note.keynum for note in notes]

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
        # Subtract midpoint from each onset time
        centered_onsets = [time - midpoint for time in onsets]
        return centered_onsets

    def fit_polynomial(
        self, centered_onsets: list[float], pitches: list[int], m: int
    ) -> list[float]:
        """Fit a polynomial model to the melody contour using least squares regression.

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
        """Select the best polynomial model using BIC in a step-wise backwards fashion.
        Tests polynomials of decreasing degree and selects the one with the best BIC.
        The max degree is the same as `m` in the fit_polynomial method.

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
            The coefficients [c1, c2, c3] of the selected polynomial model
        """
        max_degree = m
        pitches_array = np.array(pitches, dtype=float)
        x_full = np.array(
            [[t**i for i in range(max_degree + 1)] for t in centered_onsets]
        )

        # Start with maximum degree model
        best_fit = self.fit_polynomial(centered_onsets, pitches, m)
        best_coeffs = np.array(best_fit)
        best_bic = self._calculate_bic(best_coeffs, x_full, pitches_array)

        # Try all possible combinations of polynomial terms
        for i in range(1, 2 ** (max_degree + 1)):
            binary = format(i, f"0{max_degree + 1}b")
            degrees = [j for j in range(1, max_degree + 1) if binary[j] == "1"]

            if not degrees:  # Skip if only constant term
                continue

            # Create design matrix for this combination
            x = np.ones((len(centered_onsets), len(degrees) + 1))
            for j, degree in enumerate(degrees):
                x[:, j + 1] = [t**degree for t in centered_onsets]

            # Fit model with this combination of degrees
            coeffs = np.linalg.lstsq(x, pitches_array, rcond=None)[0]

            # Create a full coefficient array with zeros for missing degrees
            test_coeffs = np.zeros(max_degree + 1)
            test_coeffs[0] = coeffs[0]  # Constant term

            # Fill in the coefficients for the included degrees
            for j, degree in enumerate(degrees):
                test_coeffs[degree] = coeffs[j + 1]

            # Calculate BIC
            bic = self._calculate_bic(test_coeffs, x_full, pitches_array)

            # Keep simpler model if BIC improves
            if bic < best_bic:
                best_coeffs = test_coeffs
                best_bic = bic

        return [
            best_coeffs[1],
            best_coeffs[2],
            best_coeffs[3],
        ]  # Return c1, c2, c3 coefficients

    def _calculate_bic(
        self, coeffs: list[float], x: np.ndarray, y: np.ndarray
    ) -> float:
        """Helper method to calculate BIC for a set of coefficients.
        This emulates the FANTASTIC toolbox implementation, which uses stepAIC from the `MASS`
        package in R. As such, it counts only non-zero coefficients as parameters.

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

        # Count only non-zero coefficients as parameters
        n_params = np.sum(np.abs(coeffs) > 1e-10)

        return n * np.log(rss / n) + n_params * np.log(n)
