import matplotlib.pyplot as plt

import amads.pitch.key.profiles as prof
from amads.core.distribution import Distribution


def main():
    test_profiles = [
        prof.quinn_white.major,
        prof.krumhansl_kessler.major,
        prof.quinn_white.major_assym,
    ]
    # showing a plot in matplotlib is blocking.

    Distribution.plot_grouped_1d(test_profiles[:2] + test_profiles[:1], show=False)
    Distribution.plot_multiple(test_profiles[:2], show=False)

    plt.show()


if __name__ == "__main__":
    main()
