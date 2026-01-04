import matplotlib.pyplot as plt

from amads.pitch.key.profiles import krumhansl_kessler, quinn_white


def demo_symmetric():
    # symmetric profile: KrumhanslKessler.major
    profile = krumhansl_kessler.major
    profile.name = "Krumhansl-Kessler Major (symmetric, 1D bar plot)"
    fig = profile.plot(show=False)
    # suptitle has a spacing problem, so I just replaced the title above
    # fig.suptitle("Krumhansl-Kessler Major (symmetric, 1D bar plot)")
    return fig


# def demo_symmetric1():
#     # symmetric profile: KrumhanslKessler.major
#     profile = krumhansl_kessler.major
#     fig = profile.plot(keys=["C", "D", "E"], show=False)
#     fig.suptitle("Krumhansl-Kessler Major (symmetric, 1D bar plot)")
#     return fig


def demo_asymmetric():
    # asymmetric profile: QuinnWhite.major_asymmetric
    profile = quinn_white.major_asym
    profile.name = "Quinn-White Major Asymmetric (2D heatmap)"
    fig = profile.plot(show=False)
    # suptitle has a spacing problem, so I just replaced the title above
    # fig.suptitle("Quinn-White Major Asymmetric (2D heatmap)")
    return fig


def main():
    demo_symmetric()
    # demo_symmetric1()
    demo_asymmetric()
    plt.show()


if __name__ == "__main__":
    main()
