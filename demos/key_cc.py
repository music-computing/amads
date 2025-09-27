import amads.pitch.key.profiles as prof
from amads.all import import_midi
from amads.music import example
from amads.pitch.key_cc import build_key_correlation_distribution


def main(profiles=None, kind: str = "bar"):
    midi_path = example.fullpath("midi/sarabande.mid")
    score = import_midi(midi_path, show=False)
    for p in profiles:
        dist = build_key_correlation_distribution(score=score, profile=p)
        dist.plot(option=kind)


if __name__ == "__main__":
    # example: analyze multiple profiles
    main(profiles=[prof.bellman_budge, prof.krumhansl_kessler, prof.quinn_white])
