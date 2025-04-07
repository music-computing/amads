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

from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np

# ------------------------------------------------------------------------------


class MetricalSalience:
    """ "
    Organises an array representation of metrical structre and derives salience values.

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

    >>> ms = MetricalSalience(symbolic_pulse_length_array=arr)
    >>> ms.pulse_lengths == pl
    True

    >>> ms.pulse_symbolic_to_absolute(quarter_bpm=120)
    >>> ms.absolute_pulse_length_array
    array([[2.  , 0.  , 0.  , 0.  , 0.  , 0.  , 0.  , 0.  ],
           [1.  , 0.  , 0.  , 0.  , 1.  , 0.  , 0.  , 0.  ],
           [0.5 , 0.  , 0.5 , 0.  , 0.5 , 0.  , 0.5 , 0.  ],
           [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]])

    >>> ms.get_salience_values()
    >>> ms.salience_values_array[0, 0] # small value
    np.float64(0.21895238068829734)

    >>> ms.salience_values_array[0, 1] # 0 value
    np.float64(0.0)

    >>> ms.salience_values_array[1, 0] # higher value (nearer mu)
    np.float64(0.760767837812628)

    >>> ms.get_cumulative_salience_values()
    >>> ms.cumulative_salience_values
    array([2.39342011, 0.44793176, 1.4136999 , 0.44793176, 2.17446773,
           0.44793176, 1.4136999 , 0.44793176])

    """

    def __init__(
        self,
        symbolic_pulse_length_array: Optional[np.array] = None,
    ):
        self.symbolic_pulse_length_array = symbolic_pulse_length_array
        self.pulse_lengths = [x[0] for x in self.symbolic_pulse_length_array]
        self.quarter_bpm = None
        self.absolute_pulse_length_array = None
        self.salience_values_array = None
        self.cumulative_salience_values = None
        self.indicator = None

    def pulse_symbolic_to_absolute(self, quarter_bpm: float = 120):
        """
        Get absolute values for every item in the `symbolic_pulse_length_array`.

        """
        self.quarter_bpm = quarter_bpm
        self.absolute_pulse_length_array = (
            self.symbolic_pulse_length_array * 60 / quarter_bpm
        )

    def get_salience_values(self):
        """
        Get salience values for every item in the `symbolic_pulse_length_array`
        See notes at `log_gaussian`

        """
        self.salience_values_array = log_gaussian(self.absolute_pulse_length_array)

    def get_cumulative_salience_values(self):
        """
        Get cumulative salience values by summing over columns.
        """
        if self.salience_values_array is None:
            self.get_salience_values()
        self.cumulative_salience_values = self.salience_values_array.sum(axis=0)

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
            self.indicator = (self.symbolic_pulse_length_array > 0).astype(int)
            data = self.indicator
        else:
            data = self.salience_values_array

        if reverse_to_plot:
            data = data[::-1]  # TODO maybe revisit for elegance, checks
            pulse_values_for_labels = self.pulse_lengths[::-1]
        else:
            pulse_values_for_labels = self.pulse_lengths

        num_layers = data.shape[0]
        num_cols = data.shape[1]
        fig, ax = plt.subplots()
        bottom = np.zeros(num_cols)  # Init bottom of each bar

        for i in range(num_layers):
            ax.bar(
                np.arange(num_cols),
                data[i],
                bottom=bottom,
                label=f"Pulse={pulse_values_for_labels[i]}; IOI={pulse_values_for_labels[i] * 60 / self.quarter_bpm}",
            )
            bottom += data[i]  # Update bottom for each layer

        ax.set_xlabel("Cycle-relative position")
        ax.set_ylabel("Weighting")
        ax.legend()
        ax.grid(True)
        return plt


def log_gaussian(x: Union[float, np.array], mu: float = 0.6, sig: float = 0.3):
    """
    The log-linear Gaussian is the basis of individual pulse salience values.
    See `MetricalSalience.get_salience_values`.

    >>> log_gaussian(0.6)
    np.float64(1.0)

    >>> log_gaussian(np.array([0.06, 0.6, 6.0])) # demo log-lin symmetry
    array([0.00386592, 1.        , 0.00386592])

    >>> log_gaussian(np.array([0.5, 1., 2.])) # 2x between levels
    array([0.96576814, 0.76076784, 0.21895238])

    """
    return np.exp(-(np.log10(x / mu) ** 2 / (2 * sig**2)))


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
