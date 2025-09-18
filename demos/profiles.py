import matplotlib.pyplot as plt

from amads.pitch.key.profiles import PitchProfile, krumhansl_kessler, quinn_white


def demo_symmetric():
    # symmetric profile: KrumhanslKessler.major
    profile = krumhansl_kessler.major
    fig = profile.plot(keys=None, show=False)
    fig.suptitle("Krumhansl-Kessler Major (symmetric, 1D bar plot)")
    return fig


def demo_symmetric1():
    # symmetric profile: KrumhanslKessler.major
    profile = krumhansl_kessler.major
    fig = profile.plot(keys=["C", "D", "E"], show=False)
    fig.suptitle("Krumhansl-Kessler Major (symmetric, 1D bar plot)")
    return fig


def demo_assymetric():
    # assymetric profile: QuinnWhite.major_assym
    profile = PitchProfile("QuinnWhite Major Assym", quinn_white.major_assym)
    fig = profile.plot(keys=None, show=False)
    fig.suptitle("Quinn-White Major Assymetric (2D heatmap)")
    return fig


def main():
    demo_symmetric()
    demo_symmetric1()
    plt.show()


if __name__ == "__main__":
    main()
