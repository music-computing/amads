import matplotlib.pyplot as plt

import amads.pitch.key.profiles as prof
from amads.core.distribution import Distribution


def main():
    test_profiles = [
        prof.quinn_white.major,
        prof.krumhansl_kessler.major,
        prof.quinn_white.major_asym,
    ]
    # showing a plot in matplotlib is blocking.

    Distribution.plot_grouped_1d(test_profiles[:2], options="line", show=False)
    Distribution.plot_multiple(test_profiles[1:3], show=False, options="bar")

    plt.show()


if __name__ == "__main__":
    main()
