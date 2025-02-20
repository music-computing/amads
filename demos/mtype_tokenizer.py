from amads.algorithms.ngrams import NGramCounter
from amads.core.basics import Score


def example_usage():
    """Example usage of the MType tokenizer and n-gram counting.

    This shows how to tokenize a melody into MTypes
    and count n-grams of the resulting tokens.
    """

    # Create a simple melody
    melody = Score.from_melody(
        pitches=[60, 62, 64, 67, 72],  # C4, D4, E4, G4, C5
        durations=[
            1.0,
            0.5,
            1.0,
            0.5,
            0.5,
        ],  # quarter, eighth, quarter, eighth, eighth notes
    )

    # Initialize the n-gram counter
    counter = NGramCounter(melody)

    # Count only bigrams (n=2)
    bigram_counts = counter.get_mtype_counts(method=2)
    print(f"Dictionary of bigram counts: {bigram_counts}\n")

    # Count only trigrams (n=3)
    trigram_counts = counter.get_mtype_counts(method=3)
    print(f"Dictionary of trigram counts: {trigram_counts}\n")

    # Count all n-grams
    all_counts = counter.get_mtype_counts(method="all")
    print(f"Dictionary of all n-gram counts: {all_counts}\n")


if __name__ == "__main__":
    example_usage()
