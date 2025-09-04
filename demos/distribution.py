from typing import List

import matplotlib.pyplot as plt
import numpy as np

from amads.core.distribution import Distribution

toy_distribution_1d: List[float] = [
    0.170,
    0.012,
    0.118,
    0.141,
    0.011,
    0.098,
    0.026,
    0.212,
    0.074,
    0.024,
    0.023,
    0.091,
]

toy_distribution_2d: List[List[float]] = np.random.dirichlet(
    [1.0] * 12, size=12
).tolist()

PITCHES = [
    "C",
    "C# / Db",
    "D",
    "D# / Eb",
    "E",
    "F",
    "F# / Gb",
    "G",
    "G# / Ab",
    "A",
    "A# / Bb",
    "B",
]

TONIC = [
    "tonic",
    "tonic + 1",
    "tonic + 2",
    "tonic + 3",
    "tonic + 4",
    "tonic + 5",
    "tonic + 6",
    "tonic + 7",
    "tonic + 8",
    "tonic + 9",
    "tonic + 10",
    "tonic + 11",
]


def main():
    dist1 = Distribution(
        name="example 1D bar plot",
        data=toy_distribution_1d,
        distribution_type="pitch_class",
        dimensions=[12],
        x_categories=PITCHES,
        x_label="Pitch class",
        y_categories=None,
        y_label="Probability",
    )
    dist2 = Distribution(
        name="example 2D heatmap",
        data=toy_distribution_2d,
        distribution_type="pitch_class",
        dimensions=[12, 12],
        x_categories=TONIC,
        x_label="Pitch (relative to tonic)",
        y_categories=PITCHES,
        y_label="Key",
    )

    _ = dist1._plot_1d()
    _ = dist2._plot_2d()
    plt.show()


if __name__ == "__main__":
    main()
