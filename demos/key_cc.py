import amads.pitch.key.profiles as prof
from amads.all import import_midi
from amads.core.distribution import Distribution
from amads.music import example
from amads.pitch.key_cc import key_cc


def build_key_correlation_distribution(profile, score):
    """
    Compute key correlations for given profile and score and return a Distribution.
    """
    results = key_cc(score, profile=profile)
    corr_map = {name: list(vals) for name, vals in results}

    majors = corr_map.get("major", [0.0] * 12)
    minors = corr_map.get("minor", [0.0] * 12)

    majors_labels = prof.PitchProfile._pitches
    minors_labels = [s.lower() for s in majors_labels]
    x_labels = majors_labels + minors_labels
    data = majors + minors

    dist = Distribution(
        name=f"{profile.name} correlations",
        data=data,
        distribution_type="key_correlation",
        dimensions=[len(data)],
        x_categories=x_labels,
        x_label="Key",
        y_categories=None,
        y_label="Corr. coeff.",
    )
    return dist


def main(profiles=None):
    midi_path = example.fullpath("midi/sarabande.mid")
    score = import_midi(midi_path, show=False)
    for p in profiles:
        dist = build_key_correlation_distribution(p, score)
        dist.plot()


if __name__ == "__main__":
    # example: analyze multiple profiles
    main(profiles=[prof.bellman_budge, prof.krumhansl_kessler, prof.quinn_white])
