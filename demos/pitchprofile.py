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

    Distribution.plot_multiple(test_profiles[-1:])

    plt.show()


if __name__ == "__main__":
    main()
