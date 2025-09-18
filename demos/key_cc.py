import matplotlib.pyplot as plt

import amads.pitch.key.profiles as prof
from amads.all import import_midi
from amads.core.distribution import Distribution
from amads.music import example
from amads.pitch.key_cc import key_cc


def main():
    midi_path = example.fullpath("midi/sarabande.mid")
    score = import_midi(midi_path, show=False)

    # compute correlations for both major and minor using BellmanBudge
    results = key_cc(score, profile=prof.bellman_budge)

    # results is a list of (attribute_name, correlations_tuple)
    # find major and minor (order preserved if provided)
    corr_map = {name: list(vals) for name, vals in results}

    majors = corr_map.get("major")
    minors = corr_map.get("minor")

    # prepare data and labels: majors then minors
    majors_labels = prof.PitchProfile._pitches  # ["C","C#",...,"B"]
    minors_labels = [s.lower() for s in majors_labels]  # ["c","c#",...,"b"]
    x_labels = majors_labels + minors_labels
    data = majors + minors  # length 24

    dist = Distribution(
        name=f"{prof.bellman_budge.name} correlations (major then minor)",
        data=data,
        distribution_type="key_correlation",
        dimensions=[len(data)],
        x_categories=x_labels,
        x_label="Key",
        y_categories=None,
        y_label="Corr. coeff.",
    )

    # plot without showing, so we can add horizontal zero line and adjust layout
    fig = dist.plot(color="gray", show=False)
    ax = fig.axes[0]
    ax.axhline(0, color="k", linewidth=0.8)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
