import matplotlib.pyplot as plt

import amads.pitch.key.profiles as prof


def main():
    test_profile = prof.quinn_white
    test_profile.major_assym.plot(show=False)
    test_profile.major.plot(show=False)
    plt.show()


if __name__ == "__main__":
    main()
