import amads.pitch.key.profiles as prof
from amads.core.distribution import Distribution
from amads.core.pitch import CHROMATIC_NAMES
from amads.io.readscore import import_midi
from amads.music import example
from amads.pitch.key.key_cc import key_cc


def build_key_correlation_distribution(profile, score):
    """
    Compute key correlations for given profile.
    """
    results = key_cc(score, profile, ["major", "minor"])
    majors = results[0][1]
    minors = results[1][1]
    assert majors is not None, "profile did not contain 'major' correlations"
    assert minors is not None, "profile did not contain 'minor' correlations"

    majors_labels = CHROMATIC_NAMES
    minors_labels = [s.lower() for s in majors_labels]
    x_labels = majors_labels + minors_labels
    data = list(majors) + list(minors)

    dist = Distribution(
        name=f"{profile.name} correlations",
        data=data,
        distribution_type="key_correlation",
        dimensions=[len(data)],
        # x_categories is more general than list[str], but it's OK here:
        x_categories=x_labels,  # type: ignore
        x_label="Key",
        y_categories=None,
        y_label="Corr. coeff.",
    )
    return dist


def main(profiles, option: str = "bar"):
    midi_path = example.fullpath("midi/sarabande.mid")
    assert midi_path
    score = import_midi(midi_path, show=False)
    for p in profiles:
        dist = build_key_correlation_distribution(p, score)
        dist.plot(option=option)


if __name__ == "__main__":
    # example: analyze multiple profiles
    main(
        profiles=[prof.bellman_budge, prof.krumhansl_kessler, prof.quinn_white]
    )
