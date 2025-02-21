from amads.algorithms.mtype_tokenizer import FantasticTokenizer
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

    # Initialize tokenizer and counter
    tokenizer = FantasticTokenizer()
    ngrams = NGramCounter()

    # Tokenize melody and count n-grams
    tokenizer.tokenize_melody(melody)

    # Count only bigrams (n=2)
    bigram_counts = ngrams.count_ngrams(tokenizer.tokens, method=2)
    print(f"Dictionary of bigram counts: {bigram_counts}\n")

    # Count only trigrams (n=3)
    trigram_counts = ngrams.count_ngrams(tokenizer.tokens, method=3)
    print(f"Dictionary of trigram counts: {trigram_counts}\n")

    # Count all n-grams
    all_counts = ngrams.count_ngrams(tokenizer.tokens, method="all")
    print(f"Dictionary of all n-gram counts: {all_counts}\n")
    happy_birthday = Score.from_melody(
        pitches=[
            60,
            60,
            62,
            60,
            65,
            64,
            60,
            60,
            62,
            60,
            67,
            65,
            60,
            60,
            72,
            69,
            65,
            65,
            64,
            62,
            70,
            70,
            69,
            65,
            67,
            65,
        ],
        durations=[
            0.75,
            0.25,
            1.0,
            1.0,
            1.0,
            2.0,
            0.75,
            0.25,
            1.0,
            1.0,
            1.0,
            2.0,
            0.75,
            0.25,
            1.0,
            1.0,
            0.75,
            0.25,
            1.0,
            1.0,
            0.75,
            0.25,
            1.0,
            1.0,
            1.0,
            2.0,
        ],
    )

    tokenizer.tokenize_melody(happy_birthday)
    ngrams.count_ngrams(tokenizer.tokens, method="all")
    # These are the complexity measures computed from the n-grams of all lengths
    print("All n-grams:")
    print(f"Yule's K: {ngrams.yules_k}")
    print(f"Simpson's D: {ngrams.simpsons_d}")
    print(f"Sichel's S: {ngrams.sichels_s}")
    print(f"Honore's H: {ngrams.honores_h}")
    print(f"Normalized Entropy: {ngrams.mean_entropy}")
    print(f"Mean Productivity: {ngrams.mean_productivity}\n")

    # If we instead count only bigrams, we get a different set of results
    bigram_counts = ngrams.count_ngrams(tokenizer.tokens, method=2)
    print("Bigrams:")
    print(f"Yule's K: {ngrams.yules_k}")
    print(f"Simpson's D: {ngrams.simpsons_d}")
    print(f"Sichel's S: {ngrams.sichels_s}")
    print(f"Honore's H: {ngrams.honores_h}")
    print(f"Normalized Entropy: {ngrams.mean_entropy}")
    print(f"Mean Productivity: {ngrams.mean_productivity}\n")


if __name__ == "__main__":
    example_usage()
