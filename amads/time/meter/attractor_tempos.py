"""
What does it mean for music to be "fast" or "slow"?
Certainly BPM is not enough.
The "Attractor tempos" theory (Gotham 2015, [1]) proposes
 a definition of "fast"/"slow" relative to neutral, central, moderate tempos
 and a definition of those moderate ("Attractor") tempos that accounts for the role of the metrical structure.
In short, it provides a model for optimizing the salience of metrical structures.

[1] Gotham, M. (2015). Attractor tempos for metrical structures. Journal of Mathematics and Music, 9(1), 23–44.
https://doi.org/10.1080/17459737.2014.980343
"""

__author__ = "Mark Gotham"


import matplotlib.pyplot as plt
import numpy as np

# ------------------------------------------------------------------------------


class MetricalSalience:
    """
    Methods for storing array representations of metrical structure and derived salience values.

    Parameters
    ----------
    symbolic_pulses:
        A NumPy array representing the symbolic pulse lengths by level.
    quarter_bpm:
        The beats-per-minute corresponding to the symbolic value of a pulse length 1.0 in symbolic time.
        The user sets this value if/when calculating absolute length and salience values.
    mu: float
        The mean of the Gaussian.
    sig: float
        The standard deviation of the Gaussian.

    Attributes
    ----------
    symbolic_pulses:
        As above.
    absolute_pulses:
        An adaptation of the symbolic pulse lengths array that maps each value from symbolic to seconds.
    salience_values:
        An adaptation of the absolute pulse lengths to the equivalent salience values (see notes a `log_gaussian`).
    cumulative_salience_values:
        A 1D array summation of the absolute salience values by column (one value per metrical position).
    indicator:
        An indicator array for the (non-)presence of values at each position of the symbolic pulse lengths array.
        This can serve, for example, as the symbolic equivalent of the (absolute) `salience_values` array.

    Examples
    --------

    >>> from amads.time.meter import PulseLengths
    >>> pl = [4, 2, 1, 0.5]
    >>> pls = PulseLengths(pulse_lengths=pl, cycle_length=4)
    >>> arr = pls.to_array()
    >>> arr
    array([[4. , 0. , 0. , 0. , 0. , 0. , 0. , 0. ],
           [2. , 0. , 0. , 0. , 2. , 0. , 0. , 0. ],
           [1. , 0. , 1. , 0. , 1. , 0. , 1. , 0. ],
           [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]])

    >>> ms = MetricalSalience(symbolic_pulses=arr, quarter_bpm=120)
    >>> ms.absolute_pulses
    array([[2.  , 0.  , 0.  , 0.  , 0.  , 0.  , 0.  , 0.  ],
           [1.  , 0.  , 0.  , 0.  , 1.  , 0.  , 0.  , 0.  ],
           [0.5 , 0.  , 0.5 , 0.  , 0.5 , 0.  , 0.5 , 0.  ],
           [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]])

    >>> ms.cumulative_salience_values
    array([2.39342011, 0.44793176, 1.4136999 , 0.44793176, 2.17446773,
           0.44793176, 1.4136999 , 0.44793176])

    """

    def __init__(
        self,
        symbolic_pulses: np.array = None,
        quarter_bpm: float = None,
        mu: float = 0.6,
        sig: float = 0.3,
    ):
        self.symbolic_pulses = symbolic_pulses
        self.quarter_bpm = quarter_bpm
        self.mu = mu
        self.sig = sig
        self.absolute_pulses = self.calculate_absolute_pulse_lengths()
        self.salience_values = self.calculate_salience_values()
        self.cumulative_salience_values = self.calculate_cumulative_salience_values()
        self.indicator = self.make_indicator()

    def calculate_absolute_pulse_lengths(self):
        """
        Calculate absolute pulse lengths from
        the symbolic lengths (`symbolic_pulses`) and
        the BPM provided here for the 'quarter note' as reference value.
        """
        return self.symbolic_pulses * (60 / self.quarter_bpm)

    def calculate_salience_values(self):
        """
        Calculate salience values for items in the `symbolic_pulses`
        using `log_gaussian` (see notes on that function).
        """
        return log_gaussian(self.absolute_pulses, self.mu, self.sig)

    def calculate_cumulative_salience_values(self):
        """
        Calculate cumulative salience values by summing over columns.
        """
        return np.sum(self.salience_values, axis=0)

    def make_indicator(self):
        """
        Make a 2D indicator vector for the presence/absense of a pulse value at each position.
        """
        return (self.symbolic_pulses > 0).astype(int)

    def plot(self, symbolic_not_absolute: bool = False, reverse_to_plot: bool = True):
        """
        Plot the salience values with their respective contribution.

        Parameters
        ----------
        symbolic_not_absolute: If True, plot only the indicator values (one per level).
            If False (default), plot the tempo- and meter-sensitive, weighted salience values.
        reverse_to_plot: If True (default), plot the fastest values at the bottom.
        """
        if symbolic_not_absolute:
            data = self.indicator
        else:
            data = self.salience_values

        pulse_values_for_labels = self.symbolic_pulses[:, 0]

        if reverse_to_plot:
            data = data[::-1]  # TODO maybe revisit for elegance, checks
            pulse_values_for_labels = pulse_values_for_labels[::-1]

        num_layers = data.shape[0]
        num_cols = data.shape[1]
        fig, ax = plt.subplots()
        bottom = np.zeros(num_cols)

        for i in range(num_layers):
            ax.bar(
                np.arange(num_cols),
                data[i],
                bottom=bottom,
                label=f"Pulse={pulse_values_for_labels[i]}; IOI={pulse_values_for_labels[i] * 60 / self.quarter_bpm}",
            )
            bottom += data[i]

        ax.set_xlabel("Cycle-relative position")
        ax.set_ylabel("Weighting")
        ax.legend()
        ax.grid(True)
        return plt, fig


def log_gaussian(arr: np.ndarray, mu: float = 0.6, sig: float = 0.3):
    """
    Compute a log-linear Gaussian which is the basis of individual pulse salience values.
    To avoid log(0) issues, `np.clip` values to be always greater than 0.
    See also `MetricalSalience.get_salience_values`.


    Parameters
    ----------
    mu: float
        The mean of the Gaussian.
    sig: float
        The standard deviation of the Gaussian.

    Examples
    --------

    >>> log_gaussian(np.array([0.06, 0.6, 6.0])) # demo log-lin symmetry
    array([0.00386592, 1.        , 0.00386592])

    >>> log_gaussian(np.array([0.5, 1., 2.])) # 2x between levels
    array([0.96576814, 0.76076784, 0.21895238])

    """
    if sig <= 0:
        raise ValueError("Standard deviation (`sig`) must be positive.")
    if mu <= 0:
        raise ValueError("Mean (`mu`) must be positive.")
    x = np.clip(arr, 1e-9, None)
    return np.exp(-(np.log10(x / mu) ** 2 / (2 * sig**2)))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
