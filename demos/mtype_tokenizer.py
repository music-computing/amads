from amads.algorithms.mtype_tokenizer import FantasticTokenizer
from amads.algorithms.ngrams import NGramCounter
from amads.core.basics import Score
from amads.melody.segment import fantastic_segmenter


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
    tokens = tokenizer.tokenize(melody)

    # Count only bigrams (n=2)
    ngrams.count_ngrams(tokens, n=2)
    print(f"Dictionary of bigram counts: {ngrams.get_counts()}\n")

    # Reset counter before counting trigrams
    ngrams.reset()

    # Count only trigrams (n=3)
    ngrams.count_ngrams(tokens, n=3)
    print(f"Dictionary of trigram counts: {ngrams.get_counts()}\n")

    # Reset counter before counting all n-grams
    ngrams.reset()

    # Count all n-grams
    ngrams.count_ngrams(tokens, n=None)
    print(f"Dictionary of all n-gram counts: {ngrams.get_counts()}\n")

    # Happy Birthday example
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

    # Segment the melody into phrases
    segments = fantastic_segmenter(happy_birthday, phrase_gap=2.0, units="quarters")
    # Count all n-grams
    ngrams.reset()
    for segment in segments:
        segment_tokens = tokenizer.tokenize(segment)
        ngrams.count_ngrams(segment_tokens, n=None)

    print("All n-grams:")
    print(f"Yule's K: {ngrams.yules_k}")
    print(f"Simpson's D: {ngrams.simpsons_d}")
    print(f"Sichel's S: {ngrams.sichels_s}")
    print(f"Honore's H: {ngrams.honores_h}")
    print(f"Normalized Entropy: {ngrams.mean_entropy}")
    print(f"Mean Productivity: {ngrams.mean_productivity}\n")

    ngrams.reset()
    # Count bigrams only
    ngrams.count_ngrams(segment_tokens, n=2)

    print("Bigrams:")
    print(f"Yule's K: {ngrams.yules_k}")
    print(f"Simpson's D: {ngrams.simpsons_d}")
    print(f"Sichel's S: {ngrams.sichels_s}")
    print(f"Honore's H: {ngrams.honores_h}")
    print(f"Normalized Entropy: {ngrams.mean_entropy}")
    print(f"Mean Productivity: {ngrams.mean_productivity}\n")


if __name__ == "__main__":
    example_usage()
